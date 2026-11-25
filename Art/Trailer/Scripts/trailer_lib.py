"""Shared helpers for the trailer shots (Blender 5.3, scenes in meters).

Each shots_*.py builds one shot from the art sources and renders it:

    blender --background --python shots_road.py -- <shot> [still <frame>]

Frames go to Saved/Trailer/renders/<shot>/, stills (half size) to
Saved/Trailer/preview/.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

ART = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SAVED = os.path.join(os.path.dirname(ART), "Saved", "Trailer")
KENNEY = os.path.join(ART, "Environment", "Kenney")
MODELS = os.path.join(ART, "Trailer", "Models")
CHICKEN = os.path.join(ART, "Chicken", "Source", "SK_Chicken.blend")
SHAWARMAN = os.path.join(
    ART, "Enemies", "Shawarman", "Source", "SK_Shawarman.blend")
ENEMY_PROPS = os.path.join(ART, "Enemies", "Source", "EnemyProps.blend")
PROPS = os.path.join(ART, "Props", "Source", "Props.blend")
CIVIC = os.path.join(ART, "Environment", "Source", "Civic.blend")
FPS = 24
# Objects whose keys must run at constant speed (see key and render).
LINEAR = set()


def args():
    """Arguments after "--": shot name, then optional "still <frame>"."""
    return sys.argv[sys.argv.index("--") + 1:]


def new_scene(frames, glare=0.6, glare_threshold=1.0, samples=32):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.fps = FPS
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.frame_start = 1
    scene.frame_end = frames
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.4
    scene.eevee.taa_render_samples = samples
    scene.eevee.use_raytracing = True
    scene.eevee.use_shadows = True
    scene.eevee.use_volumetric_shadows = True
    scene.eevee.volumetric_tile_size = "8"
    scene.eevee.volumetric_samples = 64
    scene.eevee.volumetric_shadow_samples = 8
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    scene.world = bpy.data.worlds.new("World")
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "BEZIER"

    tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
    tree.interface.new_socket(
        "Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    layers = tree.nodes.new("CompositorNodeRLayers")
    bloom = tree.nodes.new("CompositorNodeGlare")
    bloom.inputs["Type"].default_value = "Bloom"
    bloom.inputs["Threshold"].default_value = glare_threshold
    bloom.inputs["Strength"].default_value = glare
    bloom.inputs["Size"].default_value = 0.6
    out = tree.nodes.new("NodeGroupOutput")
    tree.links.new(layers.outputs["Image"], bloom.inputs["Image"])
    tree.links.new(bloom.outputs["Image"], out.inputs[0])
    scene.compositing_node_group = tree
    return scene


def sky(horizon, zenith, strength=1.0, glow=None, glow_dir=(0, -1, 0),
        glow_power=3.0):
    """Vertical gradient world with an optional glow around a direction."""
    world = bpy.context.scene.world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()
    coord = nodes.new("ShaderNodeTexCoord")
    split = nodes.new("ShaderNodeSeparateXYZ")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*horizon, 1)
    ramp.color_ramp.elements[1].position = 0.45
    ramp.color_ramp.elements[1].color = (*zenith, 1)
    dot = nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = Vector(glow_dir).normalized()
    power = nodes.new("ShaderNodeMath")
    power.operation = "POWER"
    power.use_clamp = True
    power.inputs[1].default_value = glow_power
    blend = nodes.new("ShaderNodeMix")
    blend.data_type = "RGBA"
    blend.inputs["B"].default_value = (*(glow or horizon), 1)
    back = nodes.new("ShaderNodeBackground")
    back.inputs["Strength"].default_value = strength
    out = nodes.new("ShaderNodeOutputWorld")
    links.new(coord.outputs["Generated"], split.inputs[0])
    links.new(split.outputs["Z"], ramp.inputs[0])
    links.new(coord.outputs["Generated"], dot.inputs[0])
    links.new(dot.outputs["Value"], power.inputs[0])
    links.new(power.outputs[0], blend.inputs["Factor"])
    links.new(ramp.outputs[0], blend.inputs["A"])
    links.new(blend.outputs["Result"], back.inputs["Color"])
    links.new(back.outputs[0], out.inputs["Surface"])


def fog(size, location, density, color=(1, 1, 1), anisotropy=0.5,
        cloud=False):
    """A box of haze (a world volume would hide the sky in EEVEE).

    With cloud on, the haze is patchy and fades toward the box sides.
    """
    material = bpy.data.materials.new("Fog")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    haze = nodes.new("ShaderNodeVolumeScatter")
    haze.inputs["Density"].default_value = density
    haze.inputs["Color"].default_value = (*color, 1)
    haze.inputs["Anisotropy"].default_value = anisotropy
    out = nodes.new("ShaderNodeOutputMaterial")
    links = material.node_tree.links
    links.new(haze.outputs[0], out.inputs["Volume"])
    if cloud:
        coord = nodes.new("ShaderNodeTexCoord")
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 2.5
        ball = nodes.new("ShaderNodeTexGradient")
        ball.gradient_type = "SPHERICAL"
        grow = nodes.new("ShaderNodeVectorMath")
        grow.operation = "SCALE"
        grow.inputs["Scale"].default_value = 2.0
        both = nodes.new("ShaderNodeMath")
        both.operation = "MULTIPLY"
        scale = nodes.new("ShaderNodeMath")
        scale.operation = "MULTIPLY"
        scale.inputs[1].default_value = density * 2.5
        links.new(coord.outputs["Object"], noise.inputs["Vector"])
        links.new(coord.outputs["Object"], grow.inputs[0])
        links.new(grow.outputs[0], ball.inputs["Vector"])
        links.new(noise.outputs[0], both.inputs[0])
        links.new(ball.outputs["Fac"], both.inputs[1])
        links.new(both.outputs[0], scale.inputs[0])
        links.new(scale.outputs[0], haze.inputs["Density"])
    return box("Fog", size, location, material)


def paint_civic(body, color):
    """Repaints the red body swatch of the Civic colormap material."""
    material = body.material_slots[0].material
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes["Principled BSDF"]
    source = shader.inputs["Base Color"].links[0].from_socket
    split = nodes.new("ShaderNodeSeparateColor")
    split.mode = "HSV"
    vivid = nodes.new("ShaderNodeMath")
    vivid.operation = "GREATER_THAN"
    vivid.inputs[1].default_value = 0.4
    reddish = nodes.new("ShaderNodeMath")
    reddish.operation = "LESS_THAN"
    reddish.inputs[1].default_value = 0.07
    both = nodes.new("ShaderNodeMath")
    both.operation = "MULTIPLY"
    blend = nodes.new("ShaderNodeMix")
    blend.data_type = "RGBA"
    blend.inputs["B"].default_value = (*color, 1)
    gloss = nodes.new("ShaderNodeMapRange")
    gloss.inputs["To Min"].default_value = 0.6
    gloss.inputs["To Max"].default_value = 0.2
    links.new(source, split.inputs[0])
    links.new(split.outputs[1], vivid.inputs[0])
    links.new(split.outputs[0], reddish.inputs[0])
    links.new(vivid.outputs[0], both.inputs[0])
    links.new(reddish.outputs[0], both.inputs[1])
    links.new(both.outputs[0], blend.inputs["Factor"])
    links.new(source, blend.inputs["A"])
    links.new(blend.outputs["Result"], shader.inputs["Base Color"])
    links.new(both.outputs[0], gloss.inputs["Value"])
    links.new(gloss.outputs[0], shader.inputs["Roughness"])


def tint(prefix, color, rough=0.9):
    """Flat-colors every material whose name starts with the prefix."""
    for material in bpy.data.materials:
        if material.name.startswith(prefix) and material.node_tree:
            shader = material.node_tree.nodes.get("Principled BSDF")
            for link in list(shader.inputs["Base Color"].links):
                material.node_tree.links.remove(link)
            shader.inputs["Base Color"].default_value = (*color, 1)
            shader.inputs["Roughness"].default_value = rough


def mat(name, color, rough=0.8, metallic=0.0, emit=None, power=0.0,
        alpha=1.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = rough
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Alpha"].default_value = alpha
    if emit:
        shader.inputs["Emission Color"].default_value = (*emit, 1)
        shader.inputs["Emission Strength"].default_value = power
    return material


def box(name, size, location, material, rotation=(0, 0, 0), parent=None):
    """A box with the given full size (x, y, z), centered on location."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    obj.rotation_euler = rotation
    obj.data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def empty(name, location=(0, 0, 0), scale=1.0, parent=None):
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.scale = (scale, scale, scale)
    obj.parent = parent
    return obj


def append(blend, names, actions=()):
    """Appends objects (and actions) from a source file under one empty.

    The empty is scaled by the file's unit scale, so centimeter files
    come out in meters. Returns (root, {name: object}).
    """
    with bpy.data.libraries.load(blend, link=False) as (source, target):
        target.objects = [n for n in names if n in source.objects]
        target.actions = [n for n in actions if n in source.actions]
        target.scenes = [source.scenes[0]]
    unit = target.scenes[0].unit_settings.scale_length
    bpy.data.scenes.remove(target.scenes[0])
    root = empty("Root_" + names[0], scale=unit)
    found = {}
    for obj in target.objects:
        bpy.context.scene.collection.objects.link(obj)
        found[obj.name.split(".")[0]] = obj
        if obj.parent is None:
            obj.parent = root
    fix_colormaps("car-kit")
    shades = bpy.data.materials.get("M_Sunglasses")
    if shades and "Lens" not in shades:
        shades["Lens"] = True
        shader = shades.node_tree.nodes["Principled BSDF"]
        for socket in shader.inputs:
            for link in list(socket.links):
                shades.node_tree.links.remove(link)
        shader.inputs["Base Color"].default_value = (0.01, 0.01, 0.012, 1)
        shader.inputs["Roughness"].default_value = 0.06
        shader.inputs["Metallic"].default_value = 0.85
    return root, found


def fix_colormaps(kit):
    """Points the missing Kenney colormap images at Kenney/_textures."""
    name = "T_" + kit.replace("-", "_") + "_colormap.png"
    for image in bpy.data.images:
        if not image.name.startswith("colormap"):
            continue
        if os.path.exists(bpy.path.abspath(image.filepath)):
            continue
        image.filepath = os.path.join(KENNEY, "_textures", name)
        image.reload()
    for material in bpy.data.materials:
        for node in material.node_tree.nodes if material.node_tree else ():
            if node.type == "TEX_IMAGE":
                node.interpolation = "Closest"


def play(armature, name, start=1, repeat=1.0, scale=1.0, offset=0.0,
         blend_in=0):
    """Adds an action to the armature as an NLA strip on its own track."""
    action = bpy.data.actions[name]
    if armature.animation_data is None:
        armature.animation_data_create()
    track = armature.animation_data.nla_tracks.new()
    strip = track.strips.new(name, int(start), action)
    strip.action_slot = action.slots[0]
    strip.action_frame_start = action.frame_range[0] + offset
    strip.scale = scale
    strip.repeat = repeat
    strip.blend_in = blend_in
    strip.extrapolation = "HOLD"
    return strip


def hold(prop, armature, bone, toward, offset=(0, 0, 0)):
    """Parents a prop to a bone head, its +X along toward (bone space)."""
    prop.parent = armature
    prop.parent_type = "BONE"
    prop.parent_bone = bone
    length = armature.data.bones[bone].length
    prop.matrix_parent_inverse = Matrix.Translation((0, -length, 0))
    turn = Vector((1, 0, 0)).rotation_difference(Vector(toward))
    prop.matrix_basis = (
        Matrix.Translation(offset) @ turn.to_matrix().to_4x4())


def neon(text, location, size, color, power=25.0, font=None):
    """Glowing tube letters standing upright, facing -Y."""
    bpy.ops.object.text_add(location=location, rotation=(1.5708, 0, 0))
    obj = bpy.context.object
    obj.data.body = text
    obj.data.size = size
    obj.data.align_x = "CENTER"
    obj.data.fill_mode = "NONE"
    obj.data.bevel_depth = size * 0.035
    obj.data.space_character = 1.15
    if font:
        obj.data.font = bpy.data.fonts.load(font)
    obj.data.materials.append(
        mat("Neon" + text, (0, 0, 0), emit=color, power=power))
    obj.visible_shadow = False
    return obj


def glb(path, height=None, location=(0, 0, 0), yaw=0.0, name=None):
    """Imports a GLB under an empty, standing on z = 0, scaled to height."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(KENNEY, path))
    new = [obj for obj in bpy.data.objects if obj not in before]
    root = empty(name or os.path.basename(path)[:-4])
    bpy.context.view_layer.update()
    meshes = [obj for obj in new if obj.type == "MESH"]
    heights = [(obj.matrix_world @ Vector(corner)).z
               for obj in meshes for corner in obj.bound_box]
    low, top = min(heights), max(heights)
    for obj in meshes:
        world = obj.matrix_world.copy()
        world.translation.z -= low
        obj.parent = root
        obj.matrix_world = world
    top -= low
    for obj in new:
        if obj.type != "MESH":
            bpy.data.objects.remove(obj)
    fix_colormaps(path.split("/")[0])
    if height and top:
        size = height / top
        root.scale = (size, size, size)
    root.location = location
    root.rotation_euler = (0, 0, yaw)
    return root


def fill(material, amount):
    """Lets a plant glow faintly in its own colors, like light passing
    through leaves. Without it, leaf cards turned away from a low sun go
    near black next to lit ones, and those hard dark shards flicker as
    the camera moves."""
    if not amount or "Fill" in material:
        return
    material["Fill"] = True
    shader = material.node_tree.nodes["Principled BSDF"]
    source = shader.inputs["Base Color"].links[0].from_socket
    material.node_tree.links.new(source, shader.inputs["Emission Color"])
    shader.inputs["Emission Strength"].default_value = amount


def trees(sizes=(("pine", 13.0), ("pine", 11.0), ("spruce", 11.0),
                 ("spruce", 8.0), ("birch", 9.0), ("oak", 9.0)), glow=0.0):
    """Plant prototypes (Meshy models), parked out of sight, for
    copy_tree. Roots dip 3% into the ground."""
    kinds = []
    for name, tall in sizes:
        kind = glb(os.path.join(MODELS, name + ".glb"), height=tall,
                   location=(0, 0, -300))
        for part in kind.children:
            part.location.z -= 0.03 * tall / kind.scale.z
            fill(part.material_slots[0].material, glow)
        kinds.append(kind)
    return kinds


def vehicle(name, height, gloss=None):
    """A Meshy vehicle under an empty, its front toward -Y."""
    root = empty(name)
    body = glb(os.path.join(MODELS, name + ".glb"), height=height,
               yaw=math.pi / 2)
    body.parent = root
    if gloss is not None:
        material = body.children[0].material_slots[0].material
        shader = material.node_tree.nodes["Principled BSDF"]
        for link in list(shader.inputs["Roughness"].links):
            material.node_tree.links.remove(link)
        shader.inputs["Roughness"].default_value = gloss
        shader.inputs["Coat Weight"].default_value = 1.0
    return root


def civic(beams=2500.0, tail=6.0, haze=True, lamps=40.0, gloss=0.25,
          coat=1.0):
    """The black Civic, front toward -Y, with glowing lamps and beams.

    With haze off, the beams light the road but not the mist, so the
    car has no halo when seen from the front.
    """
    car = vehicle("civic", 1.42, gloss=gloss)
    paint = car.children[0].children[0].material_slots[0].material
    shader = paint.node_tree.nodes["Principled BSDF"]
    shader.inputs["Coat Weight"].default_value = coat
    # A mirror-like black car turns orange under a sunset sky.
    shader.inputs["Specular IOR Level"].default_value = min(1.0, coat + 0.1)
    for link in list(shader.inputs["Metallic"].links):
        paint.node_tree.links.remove(link)
    shader.inputs["Metallic"].default_value = 0.0
    white = mat("Headlamp", (0, 0, 0), emit=(1.0, 0.9, 0.75), power=lamps)
    red = mat("Taillamp", (0, 0, 0), emit=(1.0, 0.03, 0.01), power=tail)
    for side in (-1, 1):
        box("Head", (0.26, 0.06, 0.05), (side * 0.64, -2.12, 0.71), white,
            rotation=(0, 0, side * -0.35), parent=car)
        box("Tail", (0.36, 0.05, 0.07), (side * 0.56, 2.27, 0.9), red,
            rotation=(0, 0, side * -0.25), parent=car)
        if beams:
            lamp = light("SPOT", (side * 0.64, -2.2, 0.7), beams,
                         (1.0, 0.9, 0.75), cone=70.0, size=0.1)
            look_at(lamp, (side * 0.64, -32.0, -1.0))
            lamp.data.volume_factor = 1.0 if haze else 0.0
            lamp.parent = car
    glow = light("POINT", (0, 2.7, 0.7), tail * 0.6, (1.0, 0.05, 0.02))
    glow.parent = car
    return car


def copy_tree(root, location, yaw=0.0, scale=1.0):
    """Linked duplicate of an empty and its children (shared meshes)."""
    twin = root.copy()
    bpy.context.scene.collection.objects.link(twin)
    twin.location = location
    twin.rotation_euler = (0, 0, yaw)
    twin.scale = root.scale * scale
    twins = {root.name: twin}
    children = list(root.children_recursive)
    for child in children:
        twins[child.name] = child.copy()
        bpy.context.scene.collection.objects.link(twins[child.name])
    for child in children:
        twins[child.name].parent = twins[child.parent.name]
    return twin


def light(kind, location, energy, color=(1, 1, 1), aim=None, size=0.2,
          cone=60.0, name="Light", parent=None):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.color = color
    if kind == "SPOT":
        data.spot_size = math.radians(cone)
        data.spot_blend = 0.4
    if kind == "SUN":
        data.angle = size
    elif kind == "AREA":
        data.size = size
    else:
        data.shadow_soft_size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    if aim is not None:
        look_at(obj, aim)
    obj.parent = parent
    return obj


def look_at(obj, target):
    direction = Vector(target) - Vector(obj.location)
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def camera(lens=50.0, fstop=None, focus=None):
    data = bpy.data.cameras.new("Camera")
    data.lens = lens
    data.sensor_width = 36.0
    data.clip_start = 0.05
    data.clip_end = 2000.0
    if fstop:
        data.dof.use_dof = True
        data.dof.aperture_fstop = fstop
        if isinstance(focus, (int, float)):
            data.dof.focus_distance = focus
        else:
            data.dof.focus_object = focus
    obj = bpy.data.objects.new("Camera", data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.scene.camera = obj
    track = obj.constraints.new("TRACK_TO")
    track.target = empty("CameraAim")
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    return obj


def key(obj, frame, location=None, aim=None, linear=False, **values):
    """Keys location, a camera aim point and any other paths.

    With linear on, every key of the object (and of the camera aim) is
    made linear before rendering: no easing in or out.
    """
    if linear:
        LINEAR.add(obj.name)
        if aim is not None:
            LINEAR.add(obj.constraints[0].target.name)
    if location is not None:
        obj.location = location
        obj.keyframe_insert("location", frame=frame)
    if aim is not None:
        target = obj.constraints[0].target
        target.location = aim
        target.keyframe_insert("location", frame=frame)
    for path, value in values.items():
        owner, _, attribute = path.rpartition(".")
        target = obj.path_resolve(owner) if owner else obj
        setattr(target, attribute, value)
        target.keyframe_insert(attribute, frame=frame)


def render(shot):
    """Renders the animation, or one half-size still if asked."""
    scene = bpy.context.scene
    rest = args()[1:]
    for name in LINEAR:
        action = bpy.data.objects[name].animation_data.action
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for point in curve.keyframe_points:
                            point.interpolation = "LINEAR"
    scene.render.image_settings.file_format = "PNG"
    if rest and rest[0] == "still":
        for frame in (f for f in rest[1:] if f.isdigit()):
            scene.frame_set(int(frame))
            scene.render.resolution_percentage = (
                100 if "full" in rest else 50)
            scene.render.filepath = os.path.join(
                SAVED, "preview", f"{shot}_{int(frame):04d}.png")
            bpy.ops.render.render(write_still=True)
        return
    scene.render.use_overwrite = False
    scene.render.filepath = os.path.join(SAVED, "frames", shot, "")
    bpy.ops.render.render(animation=True)
