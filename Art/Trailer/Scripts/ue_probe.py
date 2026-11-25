"""Writes editor state to Saved/Trailer/out.json (run with py in the Cmd box)."""
import json

import unreal

utils = unreal.EditorLoadingAndSavingUtils
out = {"dirty_content": [], "dirty_maps": []}
for package in utils.get_dirty_content_packages():
    out["dirty_content"].append(package.get_name())
for package in utils.get_dirty_map_packages():
    entry = {"package": package.get_name(), "actors": []}
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_package() == package:
            entry["actors"].append({
                "label": actor.get_actor_label(),
                "class": actor.get_class().get_name(),
                "location": str(actor.get_actor_location()),
                "rotation": str(actor.get_actor_rotation())})
    out["dirty_maps"].append(entry)
out["pie"] = unreal.EditorLevelLibrary.get_game_world() is not None
path = unreal.Paths.project_saved_dir() + "Trailer/out.json"
with open(path, "w") as handle:
    json.dump(out, handle, indent=1)
unreal.log("TRAILER probe done")
