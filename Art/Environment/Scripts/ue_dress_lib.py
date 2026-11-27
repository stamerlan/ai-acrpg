import math
import random

import unreal

K = "/Game/Environment/Kenney/"
eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
sdl = unreal.SubobjectDataBlueprintFunctionLibrary
_meshes = {}


def mesh(path):
    if not path.startswith("/"):
        path = K + path
    if path not in _meshes:
        sm = eal.load_asset(path)
        if sm is None:
            raise RuntimeError("no mesh " + path)
        _meshes[path] = sm
    return _meshes[path]


def ensure_collision(sm):
    """Box collision so the camera occlusion sweep finds the mesh."""
    if unreal.EditorStaticMeshLibrary.get_simple_collision_count(sm) == 0:
        unreal.EditorStaticMeshLibrary.add_simple_collisions(
            sm, unreal.ScriptCollisionShapeType.BOX)
        eal.save_loaded_asset(sm)


def camera_only(c, occluder=True):
    c.set_editor_property("can_ever_affect_navigation", False)
    if not occluder:
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        return
    c.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
    c.set_collision_response_to_all_channels(
        unreal.CollisionResponseType.ECR_IGNORE)
    c.set_collision_response_to_channel(
        unreal.CollisionChannel.ECC_CAMERA,
        unreal.CollisionResponseType.ECR_BLOCK)


def clear(prefix):
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith(prefix):
            eas.destroy_actor(a)


def place(path, loc, yaw=0.0, scale=1.0, label="Art", folder="Art",
          occluder=True, mi=None):
    sm = mesh(path)
    if occluder:
        ensure_collision(sm)
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                   unreal.Vector(*loc),
                                   unreal.Rotator(0, 0, yaw))
    a.set_actor_label(label)
    a.set_folder_path(folder)
    c = a.static_mesh_component
    c.set_static_mesh(sm)
    if isinstance(scale, (int, float)):
        scale = (scale, scale, scale)
    a.set_actor_scale3d(unreal.Vector(*scale))
    camera_only(c, occluder)
    if mi:
        for i in range(c.get_num_materials()):
            c.set_material(i, eal.load_asset(mi))
    return a


def holder(label, folder, loc=(0, 0, 0)):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                   unreal.Vector(*loc), unreal.Rotator())
    a.set_actor_label(label)
    a.set_folder_path(folder)
    return a


def part(actor, name, cls):
    """Add a component of a class to an actor, under its root."""
    root = sds.k2_gather_subobject_data_for_instance(actor)[0]
    handle, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(
        parent_handle=root, new_class=cls, blueprint_context=None))
    sds.rename_subobject(handle, unreal.Text(name))
    return sdl.get_object(sdl.get_data(handle))


def ism(actor, name, path, occluder=False):
    """Add a hierarchical instanced mesh component to a holder actor."""
    sm = mesh(path)
    if occluder:
        ensure_collision(sm)
    c = part(actor, name, unreal.HierarchicalInstancedStaticMeshComponent)
    c.set_static_mesh(sm)
    camera_only(c, occluder)
    return c


def add(c, x, y, z=0.0, yaw=0.0, s=1.0):
    t = unreal.Transform(unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw),
                         unreal.Vector(s, s, s))
    c.add_instance(t, True)


def scatter(rng, x0, x1, y0, y1, n, min_gap, taken=None):
    """Random points in a box, at least min_gap apart."""
    pts = taken if taken is not None else []
    out = []
    tries = 0
    while len(out) < n and tries < n * 60:
        tries += 1
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if all((x - px) ** 2 + (y - py) ** 2 >= min_gap ** 2
               for px, py in pts):
            pts.append((x, y))
            out.append((x, y))
    return out


def hide_graybox(actor, keep=()):
    """Hide the visible graybox pieces; collision stays for gameplay."""
    actor.modify()  # or the map does not save the change
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        if c.get_name() in keep or not c.static_mesh:
            continue
        c.modify()
        c.set_visibility(False)
        c.set_editor_property("hidden_in_game", True)
