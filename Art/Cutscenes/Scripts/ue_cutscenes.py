"""Builds the stop 0 cutscenes as level sequences (run in the editor).

py "C:/Users/vvovchenko/repo/acrpg/Art/Cutscenes/Scripts/ue_cutscenes.py"
with L0_BorderBazaar open. Imports the sounds from Art/Audio first.
Names after the file name (intro, tow, exit, van, drive_off) rebuild
only those sequences and import no sounds.

The actors of a sequence are spawnables: copies of the level's art (the
Civic, a queue truck as the tow truck, a van) and of the chicken. The
level's own Civic and the main gate are hidden by BP_StoryDirector. The
intro is the exception: it drives the level's own day Civic
(Art_Civic_Start) in, so there is one car and it ends where the game
picks it up; run this again after ue_dress_lot.py has placed that car
anew. She is never shown inside the car: her model does not fit it.
The sequences are rebuilt from scratch on every run.

World axes: +X north (river side), +Y east; the lot is south of X = 0.
The Meshy cars face their local +Y, so a car heading h has yaw h - 90.
"""
import json
import math
import sys
import traceback

import unreal

REPO = "C:/Users/vvovchenko/repo/acrpg/"
FOLDER = "/Game/Story/Stop0/Cutscenes"
AUDIO = "/Game/Audio/Radio"
FPS = 30
eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
log = []

SOUNDS = ["SW_Radio_Intro", "SW_Radio_News", "SW_Radio_Exit", "SW_Engine",
          "SW_GateCrash"]


def import_sounds():
    tasks = []
    for name in SOUNDS:
        task = unreal.AssetImportTask()
        task.filename = REPO + "Art/Audio/" + name + ".wav"
        task.destination_path = AUDIO
        task.replace_existing = True
        task.automated = True
        task.save = True
        tasks.append(task)
    tools.import_asset_tasks(tasks)
    engine = eal.load_asset(AUDIO + "/SW_Engine")
    engine.set_editor_property("looping", True)
    eal.save_loaded_asset(engine)


def actor(label):
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    raise RuntimeError("no actor " + label)


def frames(seconds):
    return unreal.FrameNumber(int(round(seconds * FPS)))


def new_sequence(name, seconds):
    path = FOLDER + "/" + name
    if eal.does_asset_exist(path):
        seq = eal.load_asset(path)
        for b in seq.get_bindings():
            b.remove()
        for t in seq.get_tracks():
            seq.remove_track(t)
    else:
        seq = tools.create_asset(name, FOLDER, unreal.LevelSequence,
                                 unreal.LevelSequenceFactoryNew())
    seq.set_display_rate(unreal.FrameRate(FPS, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(int(seconds * FPS))
    return seq


SCALES = {}


def spawnable(seq, template, name):
    """A spawnable copy of a level actor (or of a temporary one). Its
    scale is kept: a transform track would reset it to 1 otherwise."""
    b = seq.add_spawnable_from_instance(template)
    b.set_display_name(name)
    s = template.get_actor_scale3d()
    SCALES[name] = (s.x, s.y, s.z)
    return b


def temp_mesh(mesh, scale=(1, 1, 1), material=None):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                   unreal.Vector(0, 0, -5000))
    c = a.static_mesh_component
    c.set_static_mesh(eal.load_asset(mesh))
    if material:
        c.set_material(0, eal.load_asset(material))
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    a.set_actor_scale3d(unreal.Vector(*scale))
    return a


def key_transforms(binding, samples, seconds):
    """samples: list of (t, (x, y, z), (roll, pitch, yaw)), whole length."""
    sec = binding.add_track(unreal.MovieScene3DTransformTrack).add_section()
    sec.set_range(0, int(seconds * FPS))
    ch = sec.get_all_channels()
    last_yaw = None
    for t, loc, rot in samples:
        yaw = rot[2]
        if last_yaw is not None:
            # Keep the yaw continuous so the car does not spin around
            while yaw - last_yaw > 180:
                yaw -= 360
            while yaw - last_yaw < -180:
                yaw += 360
        last_yaw = yaw
        values = (loc[0], loc[1], loc[2], rot[0], rot[1], yaw)
        for i, v in enumerate(values):
            ch[i].add_key(frames(t), v)
    for i, v in enumerate(SCALES.get(str(binding.get_display_name()),
                                      (1, 1, 1))):
        ch[6 + i].set_default(v)
    return sec


def static_transform(binding, loc, rot, seconds):
    key_transforms(binding, [(0, loc, rot)], seconds)


def look(frm, to):
    dx, dy, dz = to[0] - frm[0], to[1] - frm[1], to[2] - frm[2]
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    return (0.0, pitch, yaw)


# Auto exposure bias of the cine cameras: the day ones came out about a
# stop brighter than the game camera, the night lot is very dark
EXPOSURE = {"bias": -0.8}


def headlights(seq, samples, z, seconds, spawn=None):
    """Two headlights riding with the car."""
    out = []
    # A fill light above her washed her out to a white blob: headlights only
    for name, local, kind in (("HeadlightL", (125, -38, 40), "spot"),
                              ("HeadlightR", (125, 38, 40), "spot")):
        if kind == "spot":
            temp = eas.spawn_actor_from_class(unreal.SpotLight,
                                              unreal.Vector(0, 0, -5000))
            c = temp.spot_light_component
            c.set_intensity(300.0)
            c.set_attenuation_radius(2600.0)
            c.set_inner_cone_angle(16.0)
            c.set_outer_cone_angle(30.0)
            c.set_light_color(unreal.LinearColor(1.0, 0.92, 0.75, 1.0))
        else:
            temp = eas.spawn_actor_from_class(unreal.PointLight,
                                              unreal.Vector(0, 0, -5000))
            c = temp.point_light_component
            c.set_intensity(60.0)
            c.set_attenuation_radius(420.0)
            c.set_light_color(unreal.LinearColor(1.0, 0.85, 0.65, 1.0))
        c.set_cast_shadows(kind == "spot")
        temp.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        b = spawnable(seq, temp, name)
        temp.destroy_actor()
        keys = offset_keys(samples, local, z)
        if kind == "spot":
            keys = [(t, l, (0.0, -6.0, r[2])) for t, l, r in keys]
        keys.insert(0, (0.0, keys[0][1], keys[0][2]))
        keys.append((seconds, keys[-1][1], keys[-1][2]))
        key_transforms(b, keys, seconds)
        if spawn:
            spawned(b, spawn)
        out.append(b)
    return out


def camera(seq, name, seconds, samples=None, loc=None, at=None, fov=None):
    temp = eas.spawn_actor_from_class(unreal.CineCameraActor,
                                      unreal.Vector(0, 0, -5000))
    comp = temp.get_cine_camera_component()
    focus = comp.focus_settings
    focus.focus_method = unreal.CameraFocusMethod.DISABLE
    comp.focus_settings = focus
    # No letterbox in viewports that are not 16:9
    comp.set_editor_property("constrain_aspect_ratio", False)
    # The cine camera came out about a stop brighter than the game camera
    pp = comp.get_editor_property("post_process_settings")
    pp.set_editor_property("override_auto_exposure_bias", True)
    pp.set_editor_property("auto_exposure_bias", EXPOSURE["bias"])
    comp.set_editor_property("post_process_settings", pp)
    if fov:
        comp.set_editor_property("current_focal_length", fov)
    b = spawnable(seq, temp, name)
    temp.destroy_actor()
    if samples:
        key_transforms(b, samples, seconds)
    else:
        static_transform(b, loc, look(loc, at), seconds)
    return b


def cuts(seq, shots):
    """shots: list of (camera binding, start s, end s)."""
    track = seq.add_track(unreal.MovieSceneCameraCutTrack)
    for b, start, end in shots:
        s = track.add_section()
        s.set_range(int(start * FPS), int(end * FPS))
        s.set_camera_binding_id(seq.get_binding_id(b))


def sound(seq, name, start, end, volume=1.0, loop=False):
    s = seq.add_track(unreal.MovieSceneAudioTrack).add_section()
    s.set_sound(eal.load_asset(AUDIO + "/" + name if "/" not in name
                               else name))
    s.set_range(int(start * FPS), int(end * FPS))
    s.set_looping(loop)
    s.get_all_channels()[0].set_default(volume)
    return s


def fade(seq, keys):
    ch = seq.add_track(unreal.MovieSceneFadeTrack).add_section()
    ch.set_range(0, int(seq.get_playback_end()))
    channel = ch.get_all_channels()[0]
    for t, v in keys:
        channel.add_key(frames(t), v)


def spawned(binding, keys):
    """keys: (t, bool) for the binding's spawn track."""
    track = binding.find_tracks_by_type(unreal.MovieSceneSpawnTrack)[0]
    ch = track.get_sections()[0].get_all_channels()[0]
    for t, v in keys:
        ch.add_key(frames(t), v)


def anim(binding, path, seconds, start=0.0):
    s = binding.add_track(
        unreal.MovieSceneSkeletalAnimationTrack).add_section()
    params = s.get_editor_property("params")
    params.set_editor_property("animation", eal.load_asset(path))
    s.set_editor_property("params", params)
    s.set_range(int(start * FPS), int(seconds * FPS))


def path_pose(points, dist):
    """Point and heading at a distance along a polyline (x, y)."""
    for i in range(len(points) - 1):
        (x0, y0), (x1, y1) = points[i], points[i + 1]
        seg = math.hypot(x1 - x0, y1 - y0)
        if dist <= seg or i == len(points) - 2:
            k = min(1.0, dist / seg) if seg else 0.0
            heading = math.degrees(math.atan2(y1 - y0, x1 - x0))
            return (x0 + (x1 - x0) * k, y0 + (y1 - y0) * k), heading
        dist -= seg
    return points[-1], 0.0


def smooth(points, radius=250.0, steps=6):
    """Rounds the corners of a polyline with quadratic curves."""
    out = [points[0]]
    for i in range(1, len(points) - 1):
        p0, p1, p2 = points[i - 1], points[i], points[i + 1]
        d0 = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        d2 = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        r = min(radius, d0 / 2, d2 / 2)
        a = (p1[0] + (p0[0] - p1[0]) * r / d0, p1[1] + (p0[1] - p1[1]) * r / d0)
        b = (p1[0] + (p2[0] - p1[0]) * r / d2, p1[1] + (p2[1] - p1[1]) * r / d2)
        for s in range(steps + 1):
            k = s / steps
            out.append(((1 - k) ** 2 * a[0] + 2 * (1 - k) * k * p1[0]
                        + k * k * b[0],
                        (1 - k) ** 2 * a[1] + 2 * (1 - k) * k * p1[1]
                        + k * k * b[1]))
    out.append(points[-1])
    return out


def length(points):
    return sum(math.hypot(points[i + 1][0] - points[i][0],
                          points[i + 1][1] - points[i][1])
               for i in range(len(points) - 1))


def drive(points, start, end, accel=1.0, decel=1.5, step=0.1):
    """Samples (t, (x, y), heading) along points from start to end s.

    Speeds up over accel seconds, cruises, slows over decel seconds.
    """
    total = length(points)
    move = end - start
    cruise = total / (move - accel / 2 - decel / 2)
    out = []
    t = start
    while t <= end + 1e-6:
        u = t - start
        if u < accel:
            d = cruise * u * u / (2 * accel)
        elif u < move - decel:
            d = cruise * (accel / 2 + u - accel)
        else:
            r = move - u
            d = total - cruise * r * r / (2 * decel)
        p, h = path_pose(points, max(0.0, min(total, d)))
        out.append((round(t, 3), p, h, d))
        t += step
    return out, cruise


def car_keys(samples, z, hold_before=None, hold_after=None):
    """Transform samples for a Meshy car (yaw = heading - 90)."""
    keys = [(t, (p[0], p[1], z), (0.0, 0.0, h - 90.0))
            for t, p, h, _ in samples]
    if hold_before is not None:
        keys.insert(0, (hold_before, keys[0][1], keys[0][2]))
    if hold_after is not None:
        keys.append((hold_after, keys[-1][1], keys[-1][2]))
    return keys


def offset_keys(samples, local, z, yaw_add=0.0):
    """Keys for something riding in the car at a local offset (forward,
    right, up) from the car's center."""
    out = []
    for t, p, h, _ in samples:
        r = math.radians(h)
        fx, fy = math.cos(r), math.sin(r)
        rx, ry = -fy, fx
        x = p[0] + fx * local[0] + rx * local[1]
        y = p[1] + fy * local[0] + ry * local[1]
        out.append((t, (x, y, z + local[2]), (0.0, 0.0, h + yaw_add)))
    return out


def chase_keys(samples, back, up, ahead, side=0.0):
    out = []
    for t, p, h, _ in samples:
        r = math.radians(h)
        fx, fy = math.cos(r), math.sin(r)
        rx, ry = -fy, fx
        cam = (p[0] - fx * back + rx * side, p[1] - fy * back + ry * side, up)
        tgt = (p[0] + fx * ahead, p[1] + fy * ahead, 60.0)
        out.append((t, cam, look(cam, tgt)))
    return out


def chicken(seq, name, seconds):
    temp = eas.spawn_actor_from_class(unreal.SkeletalMeshActor,
                                      unreal.Vector(0, 0, -5000))
    comp = temp.skeletal_mesh_component
    comp.set_skinned_asset_and_update(eal.load_asset(
        "/Game/Characters/Chicken/Meshes/SK_Chicken"))
    comp.set_editor_property("animation_mode",
                             unreal.AnimationMode.ANIMATION_CUSTOM_MODE)
    b = spawnable(seq, temp, name)
    temp.destroy_actor()
    return b


CHICKEN_IDLE = "/Game/Characters/Chicken/Anims/A_Chicken_Idle"
CHICKEN_WALK = "/Game/Characters/Chicken/Anims/A_Chicken_Walk"
# The chicken mesh faces +Y: a heading h needs yaw h - 90


def build_intro():
    """The Civic comes over the bridge to the border, the radio ad."""
    T = 18.0
    EXPOSURE["bias"] = -0.8
    seq = new_sequence("LS_Intro", T)
    # The level's own car, not a copy: it stays where the drive ends
    car = actor("Art_Civic_Start")
    civic = seq.add_possessable(car)
    civic.set_display_name("Civic")
    s = car.get_actor_scale3d()
    SCALES["Civic"] = (s.x, s.y, s.z)
    stop = actor("Civic_Start").get_actor_location()
    z = car.get_actor_location().z
    # From the west end of the bridge (the far bank is forest)
    pts = [(stop.x, stop.y - 2700.0), (stop.x, stop.y)]
    samples, _ = drive(pts, 0.0, 12.0, accel=0.01, decel=4.0)
    key_transforms(civic, car_keys(samples, z, hold_after=T), T)
    # Low on the bridge, aimed low so the car sits above the subtitles
    a = camera(seq, "Cam_Bridge", T, loc=(stop.x + 220, stop.y - 1500, 120),
               at=(stop.x, stop.y - 2600, 0), fov=50.0)
    side = []
    for t, p, h, _ in samples:
        if 5.5 <= t <= 10.1:
            # Driver side (north), a little ahead, looking back in
            cam = (p[0] + 380, p[1] + 260, 150)
            side.append((t, cam, look(cam, (p[0], p[1] - 20, 95))))
    b = camera(seq, "Cam_Window", T, samples=side, fov=45.0)
    # The car stops at Kotlet's booth. No fade out: his dialog opens
    # over this shot (BP_StoryDirector), so the booth and the car sit in
    # the upper part of the frame, clear of the dialog box
    booth = actor("MK_NPC_Kotlet").get_actor_location()
    mid = ((stop.x + booth.x) / 2, (stop.y + booth.y) / 2)
    c = camera(seq, "Cam_Booth", T, loc=(mid[0] + 640, mid[1] + 60, 340),
               at=(mid[0] - 40, mid[1], -30), fov=20.0)
    cuts(seq, [(a, 0, 5.5), (b, 5.5, 10), (c, 10, T)])
    sound(seq, "SW_Radio_Intro", 0, 16.0)
    sound(seq, "SW_Engine", 0, 12.5, 0.35, loop=True)
    fade(seq, [(0, 1.0), (0.9, 0.0)])
    eal.save_loaded_asset(seq)
    log.append("LS_Intro")


def build_tow():
    """A tow truck pulls the Civic away to the impound lot."""
    T = 12.0
    EXPOSURE["bias"] = -0.8
    seq = new_sequence("LS_Tow", T)
    stop = actor("Civic_Start").get_actor_location()
    z = actor("Art_Civic_Start").get_actor_location().z
    # Wheels on the road: the art actor's origin is not at its bottom
    to, te = actor("Art_Truck_Queue_1").get_actor_bounds(False)
    tz = actor("Art_Truck_Queue_1").get_actor_location().z - (to.z - te.z)
    truck = spawnable(seq, actor("Art_Truck_Queue_1"), "TowTruck")
    civic = spawnable(seq, actor("Art_Civic_Start"), "Civic")
    gap = 560.0  # truck center ahead of the car center while towing
    lane = stop.x - 40
    in_pts = smooth([(lane + 380, stop.y - 2600), (lane + 380, stop.y - 900),
                     (lane, stop.y + gap - 80), (lane, stop.y + gap)], 300)
    arrive, _ = drive(in_pts, 0.0, 5.0, accel=0.01, decel=1.6)
    out_pts = smooth([(lane, stop.y + gap), (lane, stop.y + 1900),
                      (2650, stop.y + 2700)], 400)
    leave, _ = drive(out_pts, 6.5, T, accel=1.5, decel=0.01)
    # The truck's yaw follows the Meshy convention (heading + 90) but its
    # model is flipped in the level (fit flip=True): add 180
    tk = [(t, (p[0], p[1], tz), (0.0, 0.0, h + 270.0))
          for t, p, h, _ in arrive + leave]
    key_transforms(truck, tk, T)
    ck = [(0.0, (stop.x, stop.y, z), (0.0, 0.0, 0.0)),
          (5.6, (stop.x, stop.y, z), (0.0, 0.0, 0.0)),
          (6.3, (lane, stop.y + 40, z + 25), (0.0, 0.0, 0.0))]
    for t, p, h, d in leave:
        back, bh = path_pose(out_pts, max(0.0, d - gap + 40))
        ck.append((t, (back[0], back[1], z + 25), (0.0, 0.0, bh - 90.0)))
    key_transforms(civic, ck, T)
    a = camera(seq, "Cam_Scale", T, loc=(stop.x + 600, stop.y - 500, 300),
               at=(stop.x + 20, stop.y + 350, 60))
    # Tracking high beside the convoy (south side, over the booth): the tow
    # truck and the Civic in frame through the barrier toward the arch
    side = [k for k in chase_keys(leave, 0, 950, -330, 1600)]
    b = camera(seq, "Cam_Road", T, samples=side)
    cuts(seq, [(a, 0, 7.5), (b, 7.5, T)])
    sound(seq, "SW_Engine", 0, T, 0.5, loop=True)
    sound(seq, "SW_GateCrash", 5.6, 7.2, 0.25)
    fade(seq, [(0, 0.0), (11.2, 0.0), (T, 1.0)])
    eal.save_loaded_asset(seq)
    log.append("LS_Tow")


EXIT_PTS = smooth([(-3958, 0), (-2900, 0), (-2400, 200), (-2000, 2460),
                   (0, 2460), (700, 2480), (1650, 2250), (1650, 1700),
                   (1650, 200), (1750, 0), (2200, -40), (3000, -40)], 260)


def build_exit():
    """She gets in, rams the main gate, drives out through the bazaar."""
    T = 19.5
    EXPOSURE["bias"] = -0.5
    seq = new_sequence("LS_Exit", T)
    z = actor("Art_Civic_Start").get_actor_location().z
    civic = spawnable(seq, actor("Art_Civic_Start"), "Civic")
    samples, speed = drive(EXIT_PTS, 4.0, 18.5, accel=1.2, decel=1.8)
    key_transforms(civic, car_keys(samples, z, hold_before=0.0,
                                   hold_after=T), T)
    ram = next(t for t, p, h, d in samples if p[0] > -150 and p[1] > 2300)
    # She walks to the driver's door and gets in (is gone) at 2 s
    start = EXIT_PTS[0]
    hen = chicken(seq, "Chicken", T)
    door = (start[0] + 20, start[1] - 150)
    key_transforms(hen, [
        (0.0, (door[0] - 60, door[1] - 140, 0), (0.0, 0.0, 70.0 - 90.0)),
        (1.6, (door[0], door[1], 0), (0.0, 0.0, 90.0 - 90.0))], T)
    anim(hen, CHICKEN_WALK, 1.7)
    anim_sec = hen.find_tracks_by_type(
        unreal.MovieSceneSkeletalAnimationTrack)[0]
    s2 = anim_sec.add_section()
    params = s2.get_editor_property("params")
    params.set_editor_property("animation", eal.load_asset(CHICKEN_IDLE))
    s2.set_editor_property("params", params)
    s2.set_range(int(1.7 * FPS), int(T * FPS))
    spawned(hen, [(0.0, True), (2.05, False)])
    # Gate debris: two leaves fly off at the ram
    leaves = []
    for i, gy in enumerate((2300.0, 2560.0)):
        temp = temp_mesh("/Engine/BasicShapes/Cube", (0.06, 2.5, 2.2),
                         "/Engine/EngineMaterials/DefaultMaterial")
        leaf = spawnable(seq, temp, "GateLeaf_%d" % i)
        temp.destroy_actor()
        side = -1 if i == 0 else 1
        key_transforms(leaf, [
            (ram, (0, gy, 115), (0.0, 0.0, 0.0)),
            (ram + 0.35, (260, gy + side * 160, 160), (side * 35.0, 20.0,
                                                       side * 40.0)),
            (ram + 0.8, (520, gy + side * 330, 20), (side * 85.0, 10.0,
                                                     side * 75.0)),
            (T, (540, gy + side * 340, 12), (side * 88.0, 5.0,
                                             side * 78.0))], T)
        spawned(leaf, [(0.0, False), (ram, True)])
        leaves.append(leaf)
    a = camera(seq, "Cam_Civic", T, loc=(start[0] + 430, start[1] - 380, 150),
               at=(start[0], start[1] - 60, 60))
    headlights(seq, samples, z, T)
    # High behind her, over the containers along the inner lot
    chase = [k for k in chase_keys(samples, 450, 220, 400) if k[0] <= ram]
    b = camera(seq, "Cam_Chase", T, samples=chase)
    # Outside the gate, low and at three quarters
    c = camera(seq, "Cam_Gate", T, loc=(450, 2280, 110), at=(-150, 2500, 90))
    over = []
    for t, p, h, _ in samples:
        if ram + 1.6 <= t <= 16.6:
            cam = (p[0] - 260, p[1] + 380, 480)
            over.append((t, cam, look(cam, (p[0], p[1] - 150, 0))))
    d = camera(seq, "Cam_Bazaar", T, samples=over)
    e = camera(seq, "Cam_Arch", T, loc=(3080, 560, 170), at=(2900, -60, 80))
    cuts(seq, [(a, 0, 4.2), (b, 4.2, ram - 0.6), (c, ram - 0.6, ram + 1.6),
               (d, ram + 1.6, 16.6), (e, 16.6, T)])
    sound(seq, "SW_Engine", 2.2, 18.8, 0.6, loop=True)
    sound(seq, "SW_GateCrash", ram, ram + 1.6, 1.0)
    for i, (dt, vol) in enumerate(((0.25, 0.9), (0.7, 0.7), (1.3, 0.8),
                                   (2.0, 0.6), (3.1, 0.45), (4.4, 0.3))):
        sound(seq, "/Game/Audio/SW_CarAlarm", ram + dt, ram + dt + 2.5, vol)
    fade(seq, [(0, 1.0), (0.6, 0.0)])
    eal.save_loaded_asset(seq)
    log.append("LS_Exit ram %.2f speed %.0f" % (ram, speed))
    return ram


VAN = (2950.0, -700.0)


def build_van():
    """Zbyszek waits by his van outside the arch."""
    T = 4.0
    EXPOSURE["bias"] = 0.4
    seq = new_sequence("LS_Van", T)
    z = actor("Art_Civic_Start").get_actor_location().z
    end = EXIT_PTS[-1]
    civic = spawnable(seq, actor("Art_Civic_Start"), "Civic")
    static_transform(civic, (end[0], end[1], z), (0.0, 0.0, -90.0), T)
    vz = 0.0
    van_src = None
    for a in eas.get_all_level_actors():
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        if c and c.static_mesh and c.static_mesh.get_name() == "SM_Van":
            van_src = a
            vz = a.get_actor_location().z
            break
    van = spawnable(seq, van_src, "ZbyszekVan")
    static_transform(van, (VAN[0], VAN[1], vz), (0.0, 0.0, 0.0), T)
    # His day model (BP_NPC: the idle with the stamp held up, the talk
    # clip while his dialog runs over the last frame). The copy must not
    # be in the day data layer: the scene plays at night
    who = spawnable(seq, actor("ArtNPC_Zbyszek"), "Zbyszek")
    who.get_object_template().set_editor_property("data_layer_assets", [])
    # Turned to the road, between the camera and the Civic: the camera
    # sees his face, not his back
    static_transform(who, (VAN[0] - 40, VAN[1] + 260, 0), (0.0, 0.0, 5.0), T)
    headlights(seq, [(0.0, end, 0.0, 0.0)], z, T)
    cam = camera(seq, "Cam_Van", T, loc=(3260, -1150, 240),
                 at=(2940, -500, 90))
    cuts(seq, [(cam, 0, T)])
    fade(seq, [(0, 1.0), (0.4, 0.0)])
    eal.save_loaded_asset(seq)
    log.append("LS_Van")


def build_drive_off():
    """She drives off east past the frozen truck queue, the sky."""
    T = 11.0
    EXPOSURE["bias"] = 0.4
    seq = new_sequence("LS_DriveOff", T)
    z = actor("Art_Civic_Start").get_actor_location().z
    end = EXIT_PTS[-1]
    civic = spawnable(seq, actor("Art_Civic_Start"), "Civic")
    # On the shoulder between the bazaar wall and the frozen truck queue
    pts = smooth([end, (3060, 220), (3010, 600), (3000, 1000)], 220)
    samples, _ = drive(pts, 0.5, 6.5, accel=1.5, decel=0.01)
    key_transforms(civic, car_keys(samples, z, hold_before=0.0,
                                   hold_after=T), T)
    spawned(civic, [(0.0, True), (6.4, False)])
    headlights(seq, samples, z, T, [(0.0, True), (6.4, False)])
    loc = (2960, -560, 150)
    cam_keys = [(0.0, loc, look(loc, (3000, 0, 80))),
                (4.5, loc, look(loc, (3010, 800, 90))),
                (6.0, loc, look(loc, (3020, 1300, 160))),
                (T, loc, (0.0, 40.0, 88.0))]
    cam = camera(seq, "Cam_Sky", T, samples=cam_keys)
    cuts(seq, [(cam, 0, T)])
    sound(seq, "SW_Engine", 0.0, 6.6, 0.6, loop=True)
    fade(seq, [(0, 0.0), (9.4, 0.0), (T, 1.0)])
    eal.save_loaded_asset(seq)
    log.append("LS_DriveOff")


try:
    world = unreal.EditorLevelLibrary.get_editor_world()
    if "L0_BorderBazaar" not in world.get_path_name():
        unreal.EditorLoadingAndSavingUtils.load_map(
            "/Game/Maps/Stop0/L0_BorderBazaar")
    only = sys.argv[1:]
    if not only:
        import_sounds()
    for name, build in (("intro", build_intro), ("tow", build_tow),
                        ("exit", build_exit), ("van", build_van),
                        ("drive_off", build_drive_off)):
        if only and name not in only:
            continue
        ram = build()
        if name == "exit":
            json.dump({"ram": ram}, open(
                REPO + "Art/Cutscenes/Scripts/cutscene_times.json", "w"))
except Exception:
    log.append(traceback.format_exc())
open(REPO + "Saved/ue_cutscenes.log", "w").write("\n".join(log))
