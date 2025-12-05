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

    Modes:

      disk-and-refs (default)
        - Rename/move files on disk
        - Update image & library paths in all .blend files

      refs-only
        - Only update paths inside .blend files (no disk changes)

      disk-only
        - Only rename/move files on disk (no .blend changes)

      move-blend
        - Move a single .blend from old-path to new-path
        - Rebase its internal relative image & library paths
        - Update library references in other .blend files

    Example:

      blender --background --python rename_texture_and_update_paths.py -- \
          --mode disk-and-refs \
          --root-dir "/path/to/project" \
          --old-path "/old/location" \
          --new-path "/new/location"
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
    mode = "disk-and-refs"  # default

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
        elif args[i] == "--mode" and i + 1 < len(args):
            mode = args[i + 1].lower()
            i += 2
        else:
            i += 1

    if not root_dir or not old_path or not new_path:
        print(
            "Usage (after --): "
            "--root-dir /path --old-path old --new-path new "
            "[--mode disk-and-refs|refs-only|disk-only|move-blend]"
        )
        return None

    if mode not in {"disk-and-refs", "refs-only", "disk-only", "move-blend"}:
        print(
            f"Invalid --mode '{mode}'. Use 'disk-and-refs', 'refs-only', "
            "'disk-only', or 'move-blend'."
        )
        return None

    root_dir = os.path.abspath(root_dir)
    old_path_abs = os.path.realpath(os.path.abspath(old_path))
    new_path_abs = os.path.realpath(os.path.abspath(new_path))

    return {
        "mode": mode,
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
# Helper: rebase relative paths when a .blend moves
# --------------------------------------------------


def rebase_relative_path(original_path, old_blend_dir, new_blend_dir):
    """
    Given a Blender-style relative path starting with '//',
    compute a new relative path from new_blend_dir that still points
    to the same absolute file.
    """
    rel = original_path[2:]
    rel = rel.replace("\\", "/")

    abs_from_old = os.path.normpath(os.path.join(old_blend_dir, rel))
    new_rel = os.path.relpath(abs_from_old, new_blend_dir)
    new_rel = new_rel.replace("\\", "/")

    return "//" + new_rel


def move_blend_and_fix_internal_paths(old_path, new_path):
    """
    Move a single .blend (old_path -> new_path) and fix all relative
    image & library paths *inside that file* so they still point to
    the same absolute assets.
    """
    old_dir = os.path.dirname(old_path)
    new_dir = os.path.dirname(new_path)

    if not os.path.exists(old_path):
        print(f"ERROR: old .blend does not exist: {old_path}")
        return False

    if not os.path.exists(new_dir):
        print(f"Creating directory: {new_dir}")
        os.makedirs(new_dir, exist_ok=True)

    print(f"[move-blend] Opening source blend: {old_path}")
    bpy.ops.wm.open_mainfile(filepath=old_path)

    changed_any = False

    # Images
    for img in bpy.data.images:
        if not img.filepath:
            continue

        original_path = img.filepath
        if not original_path.startswith("//"):
            # absolute or packed or something else; leave as-is
            continue

        new_rel = rebase_relative_path(original_path, old_dir, new_dir)
        if new_rel != original_path:
            print(f"    Image '{img.name}':")
            print(f"      {original_path}")
            print(f"      -> {new_rel}")
            img.filepath = new_rel
            if hasattr(img, "filepath_raw"):
                img.filepath_raw = new_rel
            changed_any = True

    # Libraries inside the library .blend
    for lib in bpy.data.libraries:
        if not lib.filepath:
            continue

        original_path = lib.filepath
        if not original_path.startswith("//"):
            continue

        new_rel = rebase_relative_path(original_path, old_dir, new_dir)
        if new_rel != original_path:
            print(f"    Library '{lib.name}' (internal):")
            print(f"      {original_path}")
            print(f"      -> {new_rel}")
            lib.filepath = new_rel
            changed_any = True

    print(f"[move-blend] Saving to new path: {new_path}")
    bpy.ops.wm.save_mainfile(filepath=new_path)

    # Optionally delete old file on disk
    if old_path != new_path and os.path.exists(old_path):
        try:
            os.remove(old_path)
            print(f"[move-blend] Deleted old blend: {old_path}")
        except Exception as e:
            print(f"[move-blend] WARNING: failed to delete old blend: {e}")

    return changed_any


# --------------------------------------------------
# Updating .blend image & library references in other files
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


def update_library_paths_in_blend(
    old_path_fragment, new_path_fragment, exact_match=False
):
    """
    In the currently open .blend file, replace any library filepath whose
    absolute path matches or contains old_path_fragment, depending on mode.

    - If exact_match is False (default), use substring logic (good for folder moves).
    - If exact_match is True, treat old_path_fragment/new_path_fragment as *full*
      paths to a single library .blend and only change libraries whose resolved
      path exactly equals old_path_fragment.

    Relative vs absolute is preserved.
    """
    changed_any = False

    if exact_match:
        target_old = os.path.realpath(old_path_fragment)
        target_new = os.path.realpath(new_path_fragment)
    else:
        target_old = old_path_fragment
        target_new = new_path_fragment

    for lib in bpy.data.libraries:
        if not lib.filepath:
            continue

        original_path = lib.filepath
        is_relative = original_path.startswith("//")

        abs_path_raw = bpy.path.abspath(original_path)
        abs_path = os.path.realpath(abs_path_raw)

        if exact_match:
            # Only touch this library if it *is* the old library path
            if abs_path != target_old:
                continue
            new_abs_path = target_new
        else:
            # Folder/fragment mode
            if target_old not in abs_path:
                continue
            new_abs_path = abs_path.replace(target_old, target_new)
            if abs_path == new_abs_path:
                continue

        # Preserve relative vs absolute style
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


def process_blend_file(
    blend_path,
    old_path_fragment,
    new_path_fragment,
    update_images=True,
    update_libs=True,
    exact_lib_match=False,
):
    print(f"\nProcessing .blend: {blend_path}")
    bpy.ops.wm.open_mainfile(filepath=blend_path)

    changed_images = False
    changed_libs = False

    if update_images:
        changed_images = update_image_paths_in_blend(
            old_path_fragment, new_path_fragment
        )
    if update_libs:
        changed_libs = update_library_paths_in_blend(
            old_path_fragment, new_path_fragment, exact_match=exact_lib_match
        )

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

    mode = args["mode"]
    root_dir = args["root_dir"]
    old_path = args["old_path"]
    new_path = args["new_path"]

    print("--------------------------------------------------")
    print("WARNING: This script will modify files on disk and/or .blend files.")
    print("Make sure you have a backup of your project directory.")
    print("--------------------------------------------------")
    print(f"Mode:                 {mode}")
    print(f"Root directory:       {root_dir}")
    print(f"Old path fragment:    {old_path}")
    print(f"New path fragment:    {new_path}")
    print(f"Ignore dirs:          {sorted(IGNORE_DIRS)}")
    print(f"Ignore hidden dirs:   {IGNORE_HIDDEN_DIRS}")
    print("--------------------------------------------------")

    if mode == "move-blend":
        # 1) Move the .blend and fix its internal relative paths
        move_blend_and_fix_internal_paths(old_path, new_path)

        # 2) Update library references in *other* .blend files
        blend_files = find_blend_files(root_dir)
        if not blend_files:
            print("No .blend files found under root directory.")
            return

        print(
            f"\nFound {len(blend_files)} .blend file(s) to process for library path updates."
        )

        for blend_path in blend_files:
            # Skip the moved library file itself in this phase
            if os.path.abspath(blend_path) == os.path.abspath(new_path):
                print(f"\nSkipping moved library file: {blend_path}")
                continue

            process_blend_file(
                blend_path,
                old_path_fragment=old_path,
                new_path_fragment=new_path,
                update_images=False,  # only libraries
                update_libs=True,
                exact_lib_match=True,
            )

    else:
        # 1) Rename/move files on disk (if mode requires it)
        if mode in {"disk-and-refs", "disk-only"}:
            find_and_rename_files_on_disk(root_dir, old_path, new_path)

        # 2) Update references in all .blend files (if mode requires it)
        if mode in {"disk-and-refs", "refs-only"}:
            blend_files = find_blend_files(root_dir)
            if not blend_files:
                print("No .blend files found under root directory.")
                return

            print(f"\nFound {len(blend_files)} .blend file(s) to process.")

            for blend_path in blend_files:
                process_blend_file(
                    blend_path,
                    old_path_fragment=old_path,
                    new_path_fragment=new_path,
                    update_images=True,
                    update_libs=True,
                )

    print("\nDone.")


if __name__ == "__main__":
    main()
