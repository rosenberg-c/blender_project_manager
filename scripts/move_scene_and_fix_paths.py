import os
import sys

import bpy

# --------------------------------------------------
# Argument parsing
# --------------------------------------------------


def parse_args():
    """
    Usage:

        blender --background --python move_scene_and_fix_paths.py -- \
            --old-scene "/path/to/old_scene.blend" \
            --new-scene "/new/path/to/scene.blend" \
            [--delete-old yes|no]

    Default for --delete-old is "no" (keeps the original file).
    """
    if "--" not in sys.argv:
        print(
            "No custom arguments found. Use -- to separate Blender args from script args."
        )
        return None

    idx = sys.argv.index("--") + 1
    args = sys.argv[idx:]

    old_scene = None
    new_scene = None
    delete_old = "no"

    i = 0
    while i < len(args):
        if args[i] == "--old-scene" and i + 1 < len(args):
            old_scene = args[i + 1]
            i += 2
        elif args[i] == "--new-scene" and i + 1 < len(args):
            new_scene = args[i + 1]
            i += 2
        elif args[i] == "--delete-old" and i + 1 < len(args):
            delete_old = args[i + 1].lower()
            i += 2
        else:
            i += 1

    if not old_scene or not new_scene:
        print(
            "Usage (after --): --old-scene <file.blend> --new-scene <file.blend> [--delete-old yes|no]"
        )
        return None

    old_scene_abs = os.path.abspath(old_scene)
    new_scene_abs = os.path.abspath(new_scene)

    if not os.path.isfile(old_scene_abs):
        print(f"Old scene does not exist: {old_scene_abs}")
        return None

    if delete_old not in {"yes", "no"}:
        print("Invalid --delete-old, use 'yes' or 'no'")
        return None

    return {
        "old_scene": old_scene_abs,
        "new_scene": new_scene_abs,
        "delete_old": delete_old == "yes",
    }


# --------------------------------------------------
# Rebase helper
# --------------------------------------------------


def rebase_relative_path(original_path, old_scene_dir, new_scene_dir):
    """
    Given a Blender-style relative path starting with '//',
    compute a new relative path from new_scene_dir that still points
    to the same absolute file.

    Returns the new Blender-style path (still starting with '//').
    """
    # Strip leading '//' and normalize
    rel = original_path[2:]
    rel = rel.replace("\\", "/")

    # Absolute path as seen from the old scene dir
    abs_from_old = os.path.normpath(os.path.join(old_scene_dir, rel))

    # New relative path from new scene dir
    new_rel = os.path.relpath(abs_from_old, new_scene_dir)
    new_rel = new_rel.replace("\\", "/")

    return "//" + new_rel


def update_paths_for_scene(old_scene_path, new_scene_path):
    """
    Open old_scene_path, rebase all relative image and library paths
    to be correct from new_scene_path's directory, and save to new_scene_path.
    """
    print(f"Opening old scene: {old_scene_path}")
    bpy.ops.wm.open_mainfile(filepath=old_scene_path)

    old_scene_dir = os.path.dirname(old_scene_path)
    new_scene_dir = os.path.dirname(new_scene_path)

    changed_any = False

    # Images
    for img in bpy.data.images:
        if not img.filepath:
            continue

        original_path = img.filepath
        if not original_path.startswith("//"):
            # Absolute or other form; leave as-is
            continue

        new_path = rebase_relative_path(original_path, old_scene_dir, new_scene_dir)
        if new_path != original_path:
            print(f"    Image '{img.name}':")
            print(f"      {original_path}")
            print(f"      -> {new_path}")
            img.filepath = new_path
            if hasattr(img, "filepath_raw"):
                img.filepath_raw = new_path
            changed_any = True

    # Libraries
    for lib in bpy.data.libraries:
        if not lib.filepath:
            continue

        original_path = lib.filepath
        if not original_path.startswith("//"):
            # Absolute; leave as-is
            continue

        new_path = rebase_relative_path(original_path, old_scene_dir, new_scene_dir)
        if new_path != original_path:
            print(f"    Library '{lib.name}':")
            print(f"      {original_path}")
            print(f"      -> {new_path}")
            lib.filepath = new_path
            changed_any = True

    # Save to new location
    print(f"\nSaving scene to: {new_scene_path}")
    bpy.ops.wm.save_mainfile(filepath=new_scene_path)

    return changed_any


# --------------------------------------------------
# Main
# --------------------------------------------------


def main():
    args = parse_args()
    if args is None:
        return

    old_scene = args["old_scene"]
    new_scene = args["new_scene"]
    delete_old = args["delete_old"]

    print("--------------------------------------------------")
    print("Move scene and fix relative image/library paths")
    print("--------------------------------------------------")
    print(f"Old scene:      {old_scene}")
    print(f"New scene:      {new_scene}")
    print(f"Delete old:     {delete_old}")
    print("--------------------------------------------------")

    new_dir = os.path.dirname(new_scene)
    if not os.path.exists(new_dir):
        print(f"Creating directory: {new_dir}")
        os.makedirs(new_dir, exist_ok=True)

    changed = update_paths_for_scene(old_scene, new_scene)

    if delete_old:
        try:
            os.remove(old_scene)
            print(f"Deleted old scene: {old_scene}")
        except Exception as e:
            print(f"WARNING: Failed to delete old scene '{old_scene}': {e}")

    print("\nDone.")
    if not changed:
        print("Note: no relative paths were changed (maybe everything was absolute?).")


if __name__ == "__main__":
    main()
