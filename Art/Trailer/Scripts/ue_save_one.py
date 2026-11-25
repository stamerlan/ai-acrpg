"""Saves one dirty package, named in Saved/Trailer/save.txt (run with py
in the Cmd box; one package per run, the editor can hang on several)."""
import unreal

path = unreal.Paths.project_saved_dir() + "Trailer/save.txt"
with open(path) as handle:
    name = handle.read().strip()
utils = unreal.EditorLoadingAndSavingUtils
dirty = (list(utils.get_dirty_content_packages())
         + list(utils.get_dirty_map_packages()))
match = [package for package in dirty if package.get_name() == name]
done = utils.save_packages(match, True) if match else False
with open(path + ".done", "w") as handle:
    handle.write(f"{name} {done} {len(match)}")
