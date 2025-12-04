# README

```sh
# Run rename script
/Applications/Blender.app/Contents/MacOS/Blender --background \
--python scripts/rename_texture_and_update_paths.py -- \
--root-dir "./" \
--old-path "./textures/abc.jpg" \
--new-path "./textures/def.jpg"

```

```sh
# Run rename object
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/rename_objects.py -- \
  --root-dir "." \
  --lib-path "./blendfile.blend" --old-name "OldObjectName" \
  --new-name "NewObjectName"


```
