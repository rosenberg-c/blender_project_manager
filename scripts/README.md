# README


```sh
# move scene
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/move_scene_and_fix_paths.py -- \
  --old-scene "./environment.apartment.ystadsgatan-36.blend" \
  --new-scene "./models/environment.apartment.ystadsgatan-36.blend" \
  --delete-old yes

```

```sh
# move model
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/rename_texture_and_update_paths.py -- \
  --mode move-blend \
  --root-dir "./" \
  --old-path "./shelves.material.akacia.blend" \
  --new-path "./models/shelves.material.akacia.blend"

```

```sh
# rename
/Applications/Blender.app/Contents/MacOS/Blender --background \
--python scripts/rename_texture_and_update_paths.py -- \
--mode disk-and-refs \
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

```

```sh
# Run rename collection
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/rename_objects_and_ids.py -- \
  --root-dir "." \
  --lib-path "./blendfile.blend" \
  --old-name "OldCollectionName" \
  --new-name "NewCollectionName" \
  --id-type collection

```
