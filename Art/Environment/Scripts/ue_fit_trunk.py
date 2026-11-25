"""Fit every BP_CivicTrunk to the Civic next to it.

Run in the editor with the map open: py "<this file>". The trunk actor
stands behind the car; its Hinge and Lid must sit on the hatch hinge of
the nearest SM_CivicBody actor, at that actor's scale, and its light
inside the trunk. Run it after ue_dress_lot.py, which places the car.
"""
import json
import os

import unreal

# In SM_CivicBody's space, cm (blender_civic.py; Blender +Y is UE -Y)
HINGE = unreal.Vector(0, -120, 133)
LIGHT = unreal.Vector(0, -160, 85)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
res = {}
cars = [a for a in eas.get_all_level_actors()
        if isinstance(a, unreal.StaticMeshActor)
        and a.static_mesh_component.static_mesh
        and a.static_mesh_component.static_mesh.get_name() == "SM_CivicBody"]
for trunk in eas.get_all_level_actors():
    if not trunk.get_class().get_name().startswith("BP_CivicTrunk"):
        continue
    here = trunk.get_actor_location()
    car = min(cars, key=lambda a: (a.get_actor_location() - here).length())
    pose = car.get_actor_transform()
    parts = {c.get_name(): c
             for c in trunk.get_components_by_class(unreal.SceneComponent)}
    trunk.modify()
    for part in parts.values():
        part.modify()
    parts["Hinge"].set_world_location(
        pose.transform_location(HINGE), False, False)
    parts["Hinge"].set_world_rotation(car.get_actor_rotation(), False, False)
    parts["Lid"].set_relative_scale3d(car.get_actor_scale3d())
    parts["TrunkLight"].set_world_location(
        pose.transform_location(LIGHT), False, False)
    res[trunk.get_actor_label()] = {
        "car": car.get_actor_label(),
        "hinge": str(parts["Hinge"].get_world_location()),
        "scale": str(car.get_actor_scale3d())}
json.dump(res, open(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "out.json"), "w"), indent=1)
