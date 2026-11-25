"""Reloads the open map from disk, dropping unsaved actor edits (run
with py in the Cmd box)."""
import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
name = world.get_path_name().split(".")[0]
unreal.EditorLoadingAndSavingUtils.load_map(name)
unreal.log("TRAILER reloaded " + name)
