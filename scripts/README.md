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
  --python scripts/rename_objects_and_ids.py -- \
  --root-dir "." \
  --lib-path "./blendfile.blend" --old-name "OldObjectName" \
  --new-name "NewObjectName" \
  --id-type object

# Run rename collection
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/rename_objects_and_ids.py -- \
  --root-dir "." \
  --lib-path "./blendfile.blend" \
  --old-name "OldCollectionName" \
  --new-name "NewCollectionName" \
  --id-type collection


```
