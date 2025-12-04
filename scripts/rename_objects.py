import os
import sys

import bpy

# --------------------------------------------------
# Configuration for directory ignores
# --------------------------------------------------

IGNORE_DIRS = {
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    ".idea",
    ".vscode",
}

IGNORE_HIDDEN_DIRS = True


def prune_walk_dirs(dirnames):
    """
    Mutate dirnames in-place to remove ignored directories.

    This is meant to be used inside os.walk like:

        for dirpath, dirnames, filenames in os.walk(root_dir):
            prune_walk_dirs(dirnames)
            ...
    """
    dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
    if IGNORE_HIDDEN_DIRS:
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]


# --------------------------------------------------
# Argument parsing
# --------------------------------------------------


def parse_args():
    """
    Usage:

        blender --background --python rename_and_update_linked_objects.py -- \
            --root-dir "/path/to/scene/files" \
            --lib-path "/path/to/library.blend" \
            --old-name "OldObjectName" \
            --new-name "NewObjectName"

    Behavior:

      1) Renames the local object in the library file (lib-path)
      2) In all .blend files under root-dir, remaps linked usages
         from old-name -> new-name for that library.
    """
    if "--" not in sys.argv:
        print("No custom arguments found. Use -- to separate Blender args from script args.")
        return None

    idx = sys.argv.index("--") + 1
    args = sys.argv[idx:]

    root_dir = None
    lib_path = None
    old_name = None
    new_name = None

    i = 0
    while i < len(args):
        if args[i] == "--root-dir" and i + 1 < len(args):
            root_dir = args[i + 1]
            i += 2
        elif args[i] == "--lib-path" and i + 1 < len(args):
            lib_path = args[i + 1]
            i += 2
        elif args[i] == "--old-name" and i + 1 < len(args):
            old_name = args[i + 1]
            i += 2
        elif args[i] == "--new-name" and i + 1 < len(args):
            new_name = args[i + 1]
            i += 2
        else:
            i += 1

    if not root_dir:
        print("Missing --root-dir (scenes root or single .blend)")
        return None
    if not lib_path:
        print("Missing --lib-path (path to the library .blend)")
        return None
    if not old_name or not new_name:
        print("You must provide --old-name and --new-name")
        return None

    root_dir = os.path.abspath(root_dir)
    lib_path = os.path.abspath(lib_path)

    return {
        "root_dir": root_dir,
        "lib_path": lib_path,
        "old_name": old_name,
        "new_name": new_name,
    }


# --------------------------------------------------
# Utility: find all .blend files under root_dir
# --------------------------------------------------


def find_blend_files(root_path):
    """
    If root_path is a .blend file, return just that.
    Otherwise, walk the directory and return all .blend files.
    """
    if os.path.isfile(root_path) and root_path.lower().endswith(".blend"):
        return [root_path]

    blend_files = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        prune_walk_dirs(dirnames)
        for fname in filenames:
            if fname.lower().endswith(".blend"):
                blend_files.append(os.path.join(dirpath, fname))
    return blend_files


# --------------------------------------------------
# Part 1: rename local object in library file
# --------------------------------------------------


def update_object_names_in_blend(old_name, new_name, rename_data=True):
    """
    In the currently open .blend file, rename any *local* object whose name is
    old_name to new_name. Optionally also renames its data-block if the
    data had the same name.

    All internal references (modifiers, constraints, collections, etc.)
    are pointer-based, so they remain valid after the rename.

    Linked (library) objects are skipped for safety.
    """
    changed_any = False

    for obj in bpy.data.objects:
        # Skip linked/library objects (they are read-only and part of libraries)
        if obj.library is not None:
            continue

        if obj.name == old_name:
            print(f"    Object: '{obj.name}' -> '{new_name}'")
            obj.name = new_name

            if rename_data and obj.data and obj.data.name == old_name:
                print(f"      Data: '{obj.data.name}' -> '{new_name}'")
                obj.data.name = new_name

            changed_any = True

    return changed_any


def process_library_file(lib_path, old_name, new_name):
    """
    Open the library .blend file, rename local objects, save if changed.
    """
    print(f"\n[Step 1] Processing library file: {lib_path}")
    bpy.ops.wm.open_mainfile(filepath=lib_path)

    changed = update_object_names_in_blend(old_name, new_name)

    if changed:
        print("  Changes detected in library file, saving...")
        bpy.ops.wm.save_mainfile()
    else:
        print("  No changes needed in library file; not saving.")


# --------------------------------------------------
# Part 2: remap linked usages in scene files
# --------------------------------------------------


def ensure_new_linked_object(lib_abs, new_name):
    """
    Ensure the new linked object 'new_name' from lib_abs exists in this file.

    Returns the bpy.types.Object for the new linked object, or None on failure.
    """
    # If already present, just return it
    for obj in bpy.data.objects:
        if (
            obj.name == new_name
            and obj.library
            and os.path.abspath(bpy.path.abspath(obj.library.filepath)) == lib_abs
        ):
            return obj

    # Otherwise, link it from the library
    print(f"    Linking new object '{new_name}' from library:")
    print(f"      {lib_abs}")

    with bpy.data.libraries.load(lib_abs, link=True) as (data_from, data_to):
        if new_name not in data_from.objects:
            print(f"    ERROR: Object '{new_name}' not found in library {lib_abs}")
            return None
        data_to.objects = [new_name]

    # After load, the object should now exist as a linked object
    for obj in bpy.data.objects:
        if (
            obj.name == new_name
            and obj.library
            and os.path.abspath(bpy.path.abspath(obj.library.filepath)) == lib_abs
        ):
            return obj

    print("    ERROR: Failed to retrieve newly linked object.")
    return None


def remap_linked_object_users(lib_abs, old_name, new_name):
    """
    In the currently open .blend file:

    - Find any linked object(s) from lib_abs with name old_name
    - Ensure new_name is linked from the same library
    - Call ID.user_remap() to redirect all usages from old -> new
    - Remove old linked objects

    Returns True if any changes were made.
    """
    changed_any = False

    # Find libraries matching the given lib_abs
    matching_libs = [
        lib for lib in bpy.data.libraries
        if os.path.abspath(bpy.path.abspath(lib.filepath)) == lib_abs
    ]

    if not matching_libs:
        # This file does not use that library at all
        return False

    for lib in matching_libs:
        # Find old linked objects from this library
        old_objs = [
            obj for obj in bpy.data.objects
            if obj.library is lib and obj.name == old_name
        ]

        if not old_objs:
            continue

        print(f"    Found {len(old_objs)} linked object(s) named '{old_name}' from this library.")

        # Make sure we have the new linked object available
        new_obj = ensure_new_linked_object(lib_abs, new_name)
        if new_obj is None:
            continue

        # Remap each old object to the new one
        for old_obj in old_objs:
            print(f"    Remapping users of '{old_obj.name}' -> '{new_obj.name}'")
            old_obj.user_remap(new_obj)

            # After remap, old_obj should have no users and can be removed safely
            print(f"    Removing old linked object '{old_obj.name}'")
            bpy.data.objects.remove(old_obj)

            changed_any = True

    return changed_any


def process_scene_file(scene_path, lib_abs, old_name, new_name):
    print(f"\n[Step 2] Processing scene file: {scene_path}")
    bpy.ops.wm.open_mainfile(filepath=scene_path)

    changed = remap_linked_object_users(lib_abs, old_name, new_name)

    if changed:
        print("  Changes detected, saving file...")
        bpy.ops.wm.save_mainfile()
    else:
        print("  No changes needed; not saving.")


# --------------------------------------------------
# Main
# --------------------------------------------------


def main():
    args = parse_args()
    if args is None:
        return

    root_dir = args["root_dir"]
    lib_path = args["lib_path"]
    old_name = args["old_name"]
    new_name = args["new_name"]

    lib_abs = os.path.abspath(lib_path)

    print("--------------------------------------------------")
    print("WARNING: This script will modify .blend files.")
    print("Make sure you have a backup of your project directory.")
    print("--------------------------------------------------")
    print("Mode:                rename-local + remap-linked")
    print(f"Scenes root:         {root_dir}")
    print(f"Library path:        {lib_abs}")
    print(f"Old object name:     {old_name}")
    print(f"New object name:     {new_name}")
    print(f"Ignore dirs:         {sorted(IGNORE_DIRS)}")
    print(f"Ignore hidden dirs:  {IGNORE_HIDDEN_DIRS}")
    print("--------------------------------------------------")

    # Step 1: rename object in the library file itself
    process_library_file(lib_abs, old_name, new_name)

    # Step 2: remap references in all scene files under root_dir
    blend_files = find_blend_files(root_dir)
    if not blend_files:
        print("No .blend files found under root path.")
        return

    print(f"\nFound {len(blend_files)} .blend file(s) to process for remapping.")

    for blend_path in blend_files:
        # Skip the library file itself if it's under root_dir
        if os.path.abspath(blend_path) == lib_abs:
            print(f"\nSkipping library file itself in remap phase: {blend_path}")
            continue

        process_scene_file(blend_path, lib_abs, old_name, new_name)

    print("\nDone.")


if __name__ == "__main__":
    main()
