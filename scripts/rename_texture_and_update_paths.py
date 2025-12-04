import os
import sys

import bpy

# --------------------------------------------------
# Configuration for directory ignores
# --------------------------------------------------

# Directories that should never be scanned or modified
IGNORE_DIRS = {
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    ".idea",
    ".vscode",
}

# If True, ignore *all* hidden directories starting with "."
IGNORE_HIDDEN_DIRS = True


def prune_walk_dirs(dirnames):
    """
    Mutate dirnames in-place to remove ignored directories.

    This is meant to be used inside os.walk like:

        for dirpath, dirnames, filenames in os.walk(root_dir):
            prune_walk_dirs(dirnames)
            ...
    """
    # Remove explicitly ignored names
    dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

    if IGNORE_HIDDEN_DIRS:
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]


# --------------------------------------------------
# Argument parsing
# --------------------------------------------------


def parse_args():
    """
    Blender passes its own args first, then everything after `--` is ours.

    Example:
    blender --background --python rename_texture_and_update_paths.py -- \
        --root-dir "/path/to/project" \
        --old-path "./textures/old_texture_name.png" \
        --new-path "./textures/new_texture_name.png"
    """
    if "--" not in sys.argv:
        print(
            "No custom arguments found. Use -- to separate Blender args from script args."
        )
        return None

    idx = sys.argv.index("--") + 1
    args = sys.argv[idx:]

    root_dir = None
    old_path = None
    new_path = None

    i = 0
    while i < len(args):
        if args[i] == "--root-dir" and i + 1 < len(args):
            root_dir = args[i + 1]
            i += 2
        elif args[i] == "--old-path" and i + 1 < len(args):
            old_path = args[i + 1]
            i += 2
        elif args[i] == "--new-path" and i + 1 < len(args):
            new_path = args[i + 1]
            i += 2
        else:
            i += 1

    if not root_dir or not old_path or not new_path:
        print("Usage (after --): --root-dir /path --old-path old --new-path new")
        return None

    root_dir = os.path.abspath(root_dir)
    old_path_abs = os.path.abspath(old_path)
    new_path_abs = os.path.abspath(new_path)

    return {
        "root_dir": root_dir,
        "old_path": old_path_abs,
        "new_path": new_path_abs,
    }


# --------------------------------------------------
# Disk file renaming / moving
# --------------------------------------------------


def find_and_rename_files_on_disk(root_dir, old_path_fragment, new_path_fragment):
    """
    Walks root_dir and renames/moves any file whose absolute path contains
    old_path_fragment, replacing that fragment with new_path_fragment.

    Examples:
      Single file:
        old_path_fragment = /proj/textures/old_texture.png
        new_path_fragment = /proj/textures/new_texture.png

      Folder move:
        old_path_fragment = /proj/textures_old/
        new_path_fragment = /proj/textures_new/
    """
    print(f"Searching for files whose path contains:\n  '{old_path_fragment}'")
    renamed_paths = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        prune_walk_dirs(dirnames)  # <- ignore .git etc.

        for fname in filenames:
            abs_path = os.path.abspath(os.path.join(dirpath, fname))

            if old_path_fragment in abs_path:
                new_abs_path = abs_path.replace(old_path_fragment, new_path_fragment)

                if abs_path == new_abs_path:
                    continue  # nothing to change

                target_dir = os.path.dirname(new_abs_path)
                if not os.path.exists(target_dir):
                    print(f"  Creating directory: {target_dir}")
                    os.makedirs(target_dir, exist_ok=True)

                if os.path.exists(new_abs_path):
                    print(f"  WARNING: target already exists, skipping: {new_abs_path}")
                    continue

                print(f"  Renaming/moving file:\n    {abs_path}\n    -> {new_abs_path}")
                os.rename(abs_path, new_abs_path)
                renamed_paths.append((abs_path, new_abs_path))

    if not renamed_paths:
        print("No files found to rename/move on disk.")
    else:
        print(f"Renamed/moved {len(renamed_paths)} file(s) on disk.")

    return renamed_paths


# --------------------------------------------------
# Updating .blend image references
# --------------------------------------------------


def update_image_paths_in_blend(old_path_fragment, new_path_fragment):
    """
    In the currently open .blend file, replace any image filepath whose
    absolute path contains old_path_fragment with one where that fragment
    is replaced by new_path_fragment.

    Relative vs absolute is preserved.
    """
    changed_any = False

    for img in bpy.data.images:
        if not img.filepath:
            continue

        original_path = img.filepath
        is_relative = original_path.startswith("//")

        abs_path = bpy.path.abspath(original_path)

        if old_path_fragment in abs_path:
            new_abs_path = abs_path.replace(old_path_fragment, new_path_fragment)

            if abs_path == new_abs_path:
                continue

            if is_relative:
                new_path = bpy.path.relpath(new_abs_path)
            else:
                new_path = new_abs_path

            print(f"    Image '{img.name}':")
            print(f"      {original_path}")
            print(f"      -> {new_path}")

            img.filepath = new_path
            if hasattr(img, "filepath_raw"):
                img.filepath_raw = new_path

            changed_any = True

    return changed_any


def update_library_paths_in_blend(old_path_fragment, new_path_fragment):
    """
    In the currently open .blend file, replace any library filepath whose
    absolute path contains old_path_fragment with one where that fragment
    is replaced by new_path_fragment.

    Relative vs absolute is preserved (same logic as images).
    """
    changed_any = False

    for lib in bpy.data.libraries:
        if not lib.filepath:
            continue

        original_path = lib.filepath
        is_relative = original_path.startswith("//")

        abs_path = bpy.path.abspath(original_path)

        if old_path_fragment in abs_path:
            new_abs_path = abs_path.replace(old_path_fragment, new_path_fragment)

            if abs_path == new_abs_path:
                continue

            if is_relative:
                new_path = bpy.path.relpath(new_abs_path)
            else:
                new_path = new_abs_path

            print(f"    Library '{lib.name}':")
            print(f"      {original_path}")
            print(f"      -> {new_path}")

            lib.filepath = new_path
            changed_any = True

    return changed_any


def process_blend_file(blend_path, old_path_fragment, new_path_fragment):
    print(f"\nProcessing .blend: {blend_path}")
    bpy.ops.wm.open_mainfile(filepath=blend_path)

    changed_images = update_image_paths_in_blend(old_path_fragment, new_path_fragment)
    changed_libs = update_library_paths_in_blend(old_path_fragment, new_path_fragment)

    changed = changed_images or changed_libs

    if changed:
        print("  Changes detected, saving file...")
        bpy.ops.wm.save_mainfile()
    else:
        print("  No changes needed; not saving.")


def find_blend_files(root_dir):
    blend_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        prune_walk_dirs(dirnames)  # <- same ignore logic reused

        for fname in filenames:
            if fname.lower().endswith(".blend"):
                blend_files.append(os.path.join(dirpath, fname))
    return blend_files


# --------------------------------------------------
# Main
# --------------------------------------------------


def main():
    args = parse_args()
    if args is None:
        return

    root_dir = args["root_dir"]
    old_path = args["old_path"]
    new_path = args["new_path"]

    print("--------------------------------------------------")
    print("WARNING: This script will modify files on disk and .blend files.")
    print("Make sure you have a backup of your project directory.")
    print("--------------------------------------------------")
    print(f"Root directory:       {root_dir}")
    print(f"Old path fragment:    {old_path}")
    print(f"New path fragment:    {new_path}")
    print(f"Ignore dirs:          {sorted(IGNORE_DIRS)}")
    print(f"Ignore hidden dirs:   {IGNORE_HIDDEN_DIRS}")
    print("--------------------------------------------------")

    # 1) Rename/move files on disk
    find_and_rename_files_on_disk(root_dir, old_path, new_path)

    # 2) Update references in all .blend files
    blend_files = find_blend_files(root_dir)
    if not blend_files:
        print("No .blend files found under root directory.")
        return

    print(f"\nFound {len(blend_files)} .blend file(s) to process.")

    for blend_path in blend_files:
        process_blend_file(blend_path, old_path, new_path)

    print("\nDone.")


if __name__ == "__main__":
    main()
