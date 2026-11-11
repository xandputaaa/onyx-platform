import bpy, json, os, threading, queue, subprocess, shutil, math, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from mathutils import Vector

TOKEN = os.environ.get("ORNI_BLENDER_TOKEN", "")
OUT = Path("/workspace/outputs")
OUT.mkdir(parents=True, exist_ok=True)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

def mat(name, color, metallic=0.0, roughness=0.55):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF"); bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Metallic"].default_value=metallic; bs.inputs["Roughness"].default_value=roughness
    return m

def cube(name, loc, scale, material, bevel=0.12):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o=bpy.context.object; o.name=name; o.dimensions=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material: o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new("Soft garment edges","BEVEL"); mod.width=bevel; mod.segments=3
        o.modifiers.new("Weighted corner normals","WEIGHTED_NORMAL")
    return o

def set_compatible_eevee(scene):
    """Choose the Eevee engine identifier supported by this Blender build."""
    supported = {item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items}
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if engine in supported:
            scene.render.engine = engine
            return engine
    raise RuntimeError("This Blender build supports neither Eevee Next nor Eevee.")

def unwrap_scene_meshes():
    """Create deliberate UVs for every mesh using Blender's native smart projection."""
    meshes=[obj for obj in bpy.context.scene.objects if obj.type=="MESH"]
    if not meshes:
        return 0
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(island_margin=0.025)
    bpy.ops.object.mode_set(mode="OBJECT")
    return len(meshes)


def apply_psx_pixel_texture(material, base_color, label, seed=0):
    """Build a tiny deterministic 16x16 texture with nearest-neighbour sampling."""
    if not material or not material.use_nodes:
        return
    image=bpy.data.images.new(label+" | 16px pixel texture",width=16,height=16,alpha=False)
    pixels=[]
    for y in range(16):
        for x in range(16):
            variation=0.84+(((x*11+y*7+seed*13)%9)/100.0)
            band=0.94 if (x+y+seed)%7==0 else 1.0
            shade=variation*band
            pixels.extend((min(1.0,base_color[0]*shade),min(1.0,base_color[1]*shade),min(1.0,base_color[2]*shade),1.0))
    image.pixels.foreach_set(pixels)
    image.pack()
    nodes=material.node_tree.nodes
    shader=nodes.get("Principled BSDF")
    if shader:
        tex=nodes.new("ShaderNodeTexImage")
        tex.name=label+" | nearest-neighbour"
        tex.image=image
        tex.interpolation="Closest"
        tex.extension="REPEAT"
        material.node_tree.links.new(tex.outputs["Color"],shader.inputs["Base Color"])


def create_hoodie():
    clear_scene()
    black=mat("CELVANI | deep black fleece",(0.012,0.014,0.018),0.0,0.82)
    rib=mat("CELVANI | rib knit",(0.025,0.027,0.032),0.0,0.9)
    thread=mat("CELVANI | raised embroidery thread",(0.66,0.64,0.58),0.0,0.78)
    floor=mat("Studio | warm graphite",(0.055,0.058,0.063),0.0,0.9)
    # stylized first-pass garment blockout; proportions are editable, not a production pattern
    cube("Hoodie body | oversized", (0,0,2.35),(2.45,0.72,2.55),black,0.28)
    cube("Bottom rib band",(0,0,1.12),(2.42,0.76,0.28),rib,0.09)
    for side in (-1,1):
        sleeve=cube("Sleeve | dropped shoulder",(side*1.48,0,2.48),(0.88,0.68,2.05),black,0.25)
        sleeve.rotation_euler[1]=side*-0.20
        cuff=cube("Rib cuff",(side*1.63,0,1.47),(0.78,0.72,0.26),rib,0.08); cuff.rotation_euler[1]=side*-0.20
    hood=cube("Hood | volume",(0,-0.02,4.0),(1.08,0.82,1.05),black,0.34)
    cube("Kangaroo pocket",(0,-0.405,1.92),(1.25,0.12,0.55),rib,0.10)
    # raised, abstract interlocking monogram placeholder, replace with approved CELVANI vector
    for i in range(3):
        bar=cube("Embroidery study | vertical",(0,-0.49,2.7),(0.13,0.055,1.05),thread,0.025)
        bar.rotation_euler[1]=(i-1)*0.34
    for i in range(2):
        bar=cube("Embroidery study | cross",(0,-0.50,2.7),(1.0,0.055,0.12),thread,0.025)
        bar.rotation_euler[1]=(-0.35 if i==0 else 0.35)
    cube("Studio floor",(0,0,-0.12),(200,200,0.2),floor,0)
    bpy.ops.object.camera_add(location=(6,-10,6))
    cam=bpy.context.object; cam.name="CELVANI product camera"
    direction=Vector((0,0,2.3))-cam.location; cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    cam.data.lens=55; bpy.context.scene.camera=cam
    for name,loc,power,size in [("Key softbox",(1,-5,7),1100,5),("Fill softbox",(-5,-2,4),700,4),("Rim light",(2,4,6),1300,3)]:
        bpy.ops.object.light_add(type="AREA", location=loc); l=bpy.context.object; l.name=name; l.data.energy=power; l.data.shape="DISK"; l.data.size=size
        d=Vector((0,0,2.4))-l.location; l.rotation_euler=d.to_track_quat("-Z","Y").to_euler()
    scene=bpy.context.scene; set_compatible_eevee(scene)
    scene.render.resolution_x=1200; scene.render.resolution_y=1200; scene.render.resolution_percentage=100
    scene.world.color=(0.12,0.12,0.12); scene.camera.data.lens=55
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(OUT/"celvani_hoodie_blockout.png")
    scene.view_settings.view_transform="Standard"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"celvani_hoodie_blockout.blend"))
    bpy.ops.render.render(write_still=True)
    return {"ok":True,"scene":"CELVANI oversized hoodie blockout","blend":"/outputs/celvani_hoodie_blockout.blend","render":"/outputs/celvani_hoodie_blockout.png","note":"Concept blockout only; not a manufacturing-accurate garment or approved logo."}


def create_crash_woods_cinema():
    """15-second PS1-style crash-dummy short: crash, exit, forest walk, moon pan."""
    set_job_status(stage="Building forest, car and character", progress=3)
    clear_scene()
    scene=bpy.context.scene
    set_compatible_eevee(scene)
    scene.render.resolution_x=320; scene.render.resolution_y=180; scene.render.resolution_percentage=100
    scene.render.fps=12; scene.frame_start=1; scene.frame_end=180
    scene.world.color=(0.006,0.009,0.025)
    scene.view_settings.view_transform="Standard"
    scene.view_settings.look="Medium High Contrast"
    if hasattr(scene.view_settings,"dither_intensity"):
        scene.view_settings.dither_intensity=0.0
    scene.render.image_settings.file_format="PNG"
    scene.render.resolution_percentage=100

    asphalt=mat("Night road | blue-black",(0.018,0.025,0.04),0,1)
    dirt=mat("Forest floor | midnight",(0.025,0.045,0.035),0,1)
    bark=mat("Tree bark | dark umber",(0.12,0.075,0.045),0,1)
    pine=mat("Pine needles | deep green",(0.025,0.10,0.065),0,1)
    carpaint=mat("Car | faded midnight red",(0.34,0.045,0.035),0,0.9)
    glass=mat("Car glass | dark blue",(0.025,0.075,0.12),0,0.5)
    rubber=mat("Tires",(0.012,0.014,0.018),0,1)
    metal=mat("Crash dummy | ivory polymer",(0.78,0.76,0.66),0,0.85)
    joint=mat("Crash dummy | dark joints",(0.12,0.13,0.14),0,0.9)
    moonmat=mat("Moon | pale ivory",(0.78,0.82,0.91),0,1)
    headlight=mat("Headlights | pale yellow",(0.95,0.78,0.42),0,0.5)
    # Native, packed 16x16 pixel textures for the low-poly PSX palette.
    for index,(material,color) in enumerate([(asphalt,(0.018,0.025,0.04)),(dirt,(0.025,0.045,0.035)),(bark,(0.12,0.075,0.045)),(pine,(0.025,0.10,0.065)),(carpaint,(0.34,0.045,0.035)),(glass,(0.025,0.075,0.12)),(rubber,(0.012,0.014,0.018)),(metal,(0.78,0.76,0.66)),(joint,(0.12,0.13,0.14)),(moonmat,(0.78,0.82,0.91)),(headlight,(0.95,0.78,0.42))]):
        apply_psx_pixel_texture(material,color,material.name,index)


    cube("Forest ground",(0,3,-0.22),(70,90,0.4),dirt,0)
    cube("Narrow forest road",(0,-7,0),(7,55,0.12),asphalt,0)
    # Roadside stones and low-poly pines create a dense dark tree line.
    import random
    random.seed(17)
    for side in (-1,1):
        for i in range(34):
            y=-29+i*1.75+random.uniform(-0.5,0.5)
            x=side*random.uniform(5.0,12.0)
            h=random.uniform(4.5,8.5)
            bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=h*0.34, radius2=0, depth=h*0.72, location=(x,y,h*0.52))
            crown=bpy.context.object; crown.name="PS1 pine canopy"; crown.data.materials.append(pine)
            for p in crown.data.polygons: p.use_smooth=False
            bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.22, radius2=0.12, depth=h*0.42, location=(x,y,h*0.19))
            trunk=bpy.context.object; trunk.name="Low-poly pine trunk"; trunk.data.materials.append(bark)
    # A chunky compact car, built as separate readable game meshes.
    # Crash marker tree at the road edge: the front-right corner reaches it on impact.
    bpy.ops.mesh.primitive_cone_add(vertices=7,radius1=0.34,radius2=0.24,depth=2.9,location=(1.22,-1.62,1.45))
    impact_trunk=bpy.context.object; impact_trunk.name="Impact tree trunk"; impact_trunk.data.materials.append(bark)
    bpy.ops.mesh.primitive_cone_add(vertices=7,radius1=1.65,radius2=0,depth=3.8,location=(1.22,-1.62,4.1))
    impact_crown=bpy.context.object; impact_crown.name="Impact tree canopy"; impact_crown.data.materials.append(pine)
    car_parts=[]
    body=cube("Car body",(0,-5,0.95),(2.35,4.2,0.85),carpaint,0.12); car_parts.append(body)
    # Open-window cabin keeps the crash dummy readable inside the car.
    roof=cube("Car roof",(0,-5.10,2.30),(1.78,2.10,0.20),carpaint,0.07); car_parts.append(roof)
    for x in (-0.78,0.78):
        for y in (-6.05,-4.12):
            post=cube("Cabin window pillar",(x,y,1.92),(0.12,0.14,0.78),carpaint,0.025); car_parts.append(post)
    rear_glass=cube("Rear window",(0,-6.13,1.98),(1.42,0.045,0.46),glass,0.015); car_parts.append(rear_glass)
    hood=cube("Car hood",(0,-3.45,1.25),(2.25,1.05,0.25),carpaint,0.04); car_parts.append(hood)
    front_bumper=cube("Front bumper",(0,-2.88,0.72),(2.28,0.20,0.22),rubber,0.035); car_parts.append(front_bumper)
    rear_bumper=cube("Rear bumper",(0,-7.12,0.72),(2.28,0.20,0.22),rubber,0.035); car_parts.append(rear_bumper)
    grille=cube("Front grille",(0,-2.91,1.02),(0.72,0.045,0.22),rubber,0.02); car_parts.append(grille)
    for x in (-1.02,1.02):
        for y in (-6.35,-3.65):
            bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=0.43,depth=0.22,location=(x,y,0.48),rotation=(0,math.pi/2,0))
            w=bpy.context.object; w.name="Car wheel"; w.data.materials.append(rubber); car_parts.append(w)
    for x in (-0.72,0.72):
        lamp=cube("Headlamp",(x,-2.88,1.0),(0.34,0.08,0.18),headlight,0.025); car_parts.append(lamp)
    # Dummy is assembled from primitive pieces, with articulated limbs.
    dummy_parts=[]
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=0.34,location=(0,-5.25,2.15))
    dhead=bpy.context.object; dhead.name="Crash dummy | faceted head"; dhead.data.materials.append(metal); dummy_parts.append(dhead)
    torso=cube("Crash dummy | torso",(0,-5.25,1.25),(0.72,0.42,0.95),metal,0.05); dummy_parts.append(torso)
    pelvis=cube("Crash dummy | pelvis",(0,-5.25,0.78),(0.62,0.40,0.34),joint,0.04); dummy_parts.append(pelvis)
    limbs=[]
    for side in (-1,1):
        upper=cube("Crash dummy | upper arm",(side*0.52,-5.25,1.36),(0.22,0.25,0.72),metal,0.04)
        lower=cube("Crash dummy | forearm",(side*0.52,-5.25,0.98),(0.19,0.22,0.55),metal,0.035)
        thigh=cube("Crash dummy | thigh",(side*0.2,-5.25,0.43),(0.25,0.28,0.65),metal,0.04)
        shin=cube("Crash dummy | shin",(side*0.2,-5.25,0.08),(0.22,0.25,0.55),metal,0.035)
        limbs.extend([upper,lower,thigh,shin]); dummy_parts.extend([upper,lower,thigh,shin])
    # Dark mechanical joints make the crash-test dummy silhouette immediately legible.
    for x in (-0.52,0.52):
        for z in (1.36,0.98):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=0.15,location=(x,-5.25,z))
            j=bpy.context.object; j.name="Crash dummy | articulated arm joint"; j.data.materials.append(joint); dummy_parts.append(j)
    for x in (-0.20,0.20):
        for z in (0.43,0.08):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=0.16,location=(x,-5.25,z))
            j=bpy.context.object; j.name="Crash dummy | articulated leg joint"; j.data.materials.append(joint); dummy_parts.append(j)
    # Move each limb origin to its anatomical joint so animation rotates at shoulders, elbows, hips and knees.
    for limb in limbs:
        side=-1 if limb.location.x<0 else 1
        if "upper arm" in limb.name: pivot=(side*0.52,-5.25,1.72)
        elif "forearm" in limb.name: pivot=(side*0.52,-5.25,0.99)
        elif "thigh" in limb.name: pivot=(side*0.20,-5.25,0.75)
        else: pivot=(side*0.20,-5.25,0.40)
        bpy.ops.object.select_all(action="DESELECT")
        limb.select_set(True)
        bpy.context.view_layer.objects.active=limb
        bpy.context.scene.cursor.location=Vector(pivot)
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    # Dummy begins inside the car, then is staged beside it and walks into the trees.
    # Animate grouped pieces as a simple articulated game character.
    for obj in dummy_parts:
        obj.location.x += 0
    def key_loc(obj, frame, loc):
        obj.location=loc; obj.keyframe_insert(data_path="location",frame=frame)
    # Car drives toward a roadside tree and jolts to a stop at ~3 seconds.
    for obj in car_parts:
        start=obj.location.copy()
        obj.location.y=start.y-13.0; obj.keyframe_insert(data_path="location",frame=1)
        obj.location.y=start.y; obj.keyframe_insert(data_path="location",frame=27)
        obj.location.y=start.y+0.9; obj.keyframe_insert(data_path="location",frame=34)
        obj.location.y=start.y+0.9; obj.keyframe_insert(data_path="location",frame=180)
    # Dummy appears in the driver's seat, exits on the near side, then walks away.
    # Use a coherent group translation; staggered arm/leg swings suggest a PS1 walk cycle.
    for obj in dummy_parts:
        base=obj.location.copy()
        obj.location=base+Vector((0,0.2,0)); obj.keyframe_insert(data_path="location",frame=1)
        obj.location=base+Vector((0,0.2,0)); obj.keyframe_insert(data_path="location",frame=38)
        obj.location=base+Vector((1.8,0.0,0)); obj.keyframe_insert(data_path="location",frame=65)
        obj.location=base+Vector((3.0,3.0,0)); obj.keyframe_insert(data_path="location",frame=105)
        obj.location=base+Vector((4.5,8.0,0)); obj.keyframe_insert(data_path="location",frame=142)
        obj.location=base+Vector((5.0,10.0,0)); obj.keyframe_insert(data_path="location",frame=150)
    # Alternating limb swings sell a simple low-frame-rate PS1 walk cycle.
    for limb_index, limb in enumerate(limbs):
        phase=0 if limb_index%2==0 else math.pi
        for frame in (65,75,85,95,105,115,125,135,145):
            limb.rotation_euler[0]=0.22*math.sin((frame-65)*0.42+phase)
            limb.keyframe_insert(data_path="rotation_euler",frame=frame)
    # Forest moon, deliberately faceted like a PS1 skybox prop.
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=2.0,location=(0,18,17))
    moon=bpy.context.object; moon.name="Moon | final reveal"; moon.data.materials.append(moonmat)
    # Small star points.
    for i in range(45):
        x=random.uniform(-28,28); y=random.uniform(-8,30); z=random.uniform(10,24)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=0.055,location=(x,y,z))
        star=bpy.context.object; star.name="Pixel-star"; star.data.materials.append(moonmat)

    set_job_status(stage="Lighting and camera choreography", progress=12)
    # Cold moonlight and weak warm headlamp spill.
    bpy.ops.object.light_add(type="SUN",location=(0,0,12))
    sun=bpy.context.object; sun.name="Moonlit forest"; sun.data.energy=0.65; sun.data.color=(0.42,0.55,1.0)
    sun.rotation_euler=(0.45,-0.35,-0.3)
    bpy.ops.object.light_add(type="AREA",location=(0,-1,3))
    glow=bpy.context.object; glow.name="Car headlamp spill"; glow.data.energy=90; glow.data.shape="DISK"; glow.data.size=5
    glow.data.color=(1.0,0.65,0.35); glow.rotation_euler=(math.radians(25),0,0)

    bpy.ops.object.camera_add(location=(7,-15,5))
    cam=bpy.context.object; cam.name="ORNI crash-film camera"; scene.camera=cam; cam.data.lens=42
    def aim(frame, loc, target):
        cam.location=loc; cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
        cam.keyframe_insert(data_path="location",frame=frame); cam.keyframe_insert(data_path="rotation_euler",frame=frame)
    # 0-3.0s: establish the road and follow the impact.
    aim(1,(7,-16,5),(0,-7,1))
    aim(28,(5,-11,3.2),(0,-4,1))
    # 3-6s: hold on the wreck as the dummy gets out.
    aim(48,(6,-10,3.0),(0,-4,1.2))
    aim(70,(4,-7,2.6),(1.4,-4,1.2))
    # 6-12.5s: follow the dummy deeper into the forest.
    aim(105,(9,-1,3.2),(3,3,1.2))
    aim(145,(10,5,4.2),(4.5,8,1.2))
    # 12.5-15s: tilt/pan up to the moon and hold the final image.
    aim(151,(7,8,5),(5,10,1))
    aim(180,(0,13,8),(0,18,17))
    for obj in scene.objects:
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points: kp.interpolation="LINEAR"
    set_job_status(stage="UV unwrapping and pixel texturing", progress=15)
    uv_mesh_count=unwrap_scene_meshes()
    scene.render.filepath=str(OUT/"orni_crash_woods_preview.png")
    scene.frame_set(1)
    set_job_status(stage="Saving editable Blender project", progress=18)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"orni_crash_woods.blend"))
    set_job_status(stage="Rendering cinematic preview", progress=22)
    bpy.ops.render.render(write_still=True)
    frames_dir=OUT/"orni_crash_woods_frames"
    if frames_dir.exists(): shutil.rmtree(frames_dir,ignore_errors=True)
    frames_dir.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(frames_dir/"frame_")
    set_job_status(stage="Rendering animation frames", progress=25, frame=0, frames=scene.frame_end)
    bpy.ops.render.render(animation=True)
    video_file=OUT/"orni_crash_woods_15s.mp4"
    set_job_status(stage="Encoding MP4 with FFmpeg", progress=92)
    try:
        subprocess.run(["ffmpeg","-y","-framerate","12","-i",str(frames_dir/"frame_%04d.png"),"-vf","scale=iw*3:ih*3:flags=neighbor","-c:v","libx264","-pix_fmt","yuv420p","-crf","21","-preset","ultrafast","-movflags","+faststart",str(video_file)],check=True,capture_output=True,text=True,timeout=480)
    except FileNotFoundError: raise RuntimeError("FFmpeg is not installed in the Blender worker.")
    except subprocess.CalledProcessError as exc: raise RuntimeError("FFmpeg encoding failed: "+(exc.stderr or "unknown error")[-1200:])
    finally: shutil.rmtree(frames_dir,ignore_errors=True)
    if not video_file.is_file() or video_file.stat().st_size<1024: raise RuntimeError("15-second crash-woods MP4 was not created.")
    # Probe stream metadata and decode the complete file before exposing it as a deliverable.
    probe=subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height,r_frame_rate","-show_entries","format=duration","-of","json",str(video_file)],check=True,capture_output=True,text=True,timeout=30)
    probe_data=json.loads(probe.stdout)
    stream=(probe_data.get("streams") or [{}])[0]
    duration=float((probe_data.get("format") or {}).get("duration",0))
    if (stream.get("width"),stream.get("height"))!=(960,540):
        raise RuntimeError("MP4 dimensions failed validation: expected 960x540 nearest-neighbour upscale.")
    if stream.get("r_frame_rate")!="12/1" or not 14.5<=duration<=15.5:
        raise RuntimeError("MP4 frame rate or duration failed validation.")
    subprocess.run(["ffmpeg","-v","error","-i",str(video_file),"-f","null","-"],check=True,capture_output=True,text=True,timeout=180)
    set_job_status(stage="Validating MP4, preview and editable scene", progress=98)
    if not (OUT/"orni_crash_woods.blend").is_file() or not (OUT/"orni_crash_woods_preview.png").is_file(): raise RuntimeError("One or more required Blender deliverables are missing.")
    return {"ok":True,"scene":"ORNI PS1 crash dummy in the woods","style":"ps1-crash-woods","blend":"/outputs/orni_crash_woods.blend","preview":"/outputs/orni_crash_woods_preview.png","video":"/outputs/orni_crash_woods_15s.mp4","frames":180,"fps":12,"durationSeconds":15,"resolutionX":960,"resolutionY":540,"sourceResolution":"320x180","aspectRatio":"16:9","uvMappedMeshes":uv_mesh_count,"pixelTextureResolution":"16x16 per material","decodeValidated":True,"note":"Native UVs and packed 16x16 nearest-sampled material textures; MP4 metadata and full decode validated. Story beats still require human playback review."}


def create_retro_cinema(style="ps1", duration=5, aspect_ratio="16:9", caption=""):
    if style == "crash-woods": return create_crash_woods_cinema()
    clear_scene()
    ps1 = style == "ps1"
    duration = max(3,min(15,int(duration or 5)))
    aspect_ratio = aspect_ratio if aspect_ratio in ("9:16","16:9","1:1") else "16:9"
    palette = {
        "ink": (0.025,0.035,0.065), "blue": (0.08,0.20,0.55),
        "red": (0.72,0.12,0.16), "cream": (0.78,0.72,0.58),
        "skin": (0.58,0.34,0.22), "cloth": (0.045,0.055,0.075),
        "floor": (0.10,0.12,0.16), "accent": (0.22,0.62,0.60)
    }
    mats={k:mat("ORNI Retro | "+k,v,0.0,0.95) for k,v in palette.items()}
    # Low-poly game character: deliberately angular silhouette, not a photoreal human.
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1 if ps1 else 2, radius=0.48, location=(0,0,2.45))
    head=bpy.context.object; head.name="Retro protagonist | low-poly head"; head.data.materials.append(mats["skin"])
    for p in head.data.polygons: p.use_smooth=False
    cube("Retro protagonist | oversized jacket",(0,0,1.55),(1.05,0.55,1.35),mats["cloth"],0.03)
    if not ps1:
        cube("PS2 face | left eye",(-0.16,-0.425,2.57),(0.075,0.035,0.07),mats["ink"],0.008)
        cube("PS2 face | right eye",(0.16,-0.425,2.57),(0.075,0.035,0.07),mats["ink"],0.008)
        mouth=cube("PS2 face | dialogue mouth",(0,-0.455,2.34),(0.19,0.035,0.075),mats["ink"],0.008)
    for side in (-1,1):
        arm=cube("Retro protagonist | sleeve",(side*0.72,0,1.62),(0.42,0.48,1.05),mats["blue"],0.02)
        arm.rotation_euler[1]=side*0.12
        leg=cube("Retro protagonist | trouser",(side*0.25,0,0.58),(0.42,0.48,1.05),mats["ink"],0.02)
        cube("Retro protagonist | shoe",(side*0.25,-0.12,0.08),(0.48,0.72,0.2),mats["red"],0.02)
    # A sparse, game-like alley / stage with block geometry and a long vanishing point.
    cube("Retro stage floor",(0,1,-0.12),(18,22,0.2),mats["floor"],0)
    for x in (-5.2,5.2):
        for y in (1,5,9):
            cube("Low-poly environment block",(x,y,1.8),(1.5,2.8,3.6),mats["blue"] if x<0 else mats["ink"],0)
    for x in (-3.0,3.0):
        cube("Retro set light",(x,3,3.1),(0.16,0.16,4.8),mats["accent"],0)
    bpy.ops.object.camera_add(location=(4.2,-7.8,3.35))
    cam=bpy.context.object; cam.name="ORNI retro tracking camera"
    target=Vector((0,0.9,1.65)); cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.lens=42 if ps1 else 48; bpy.context.scene.camera=cam
    for name,loc,power,size,color in [
        ("Retro key",(1,-4,7),900,5,(0.55,0.68,1.0)),
        ("Retro rim",(-4,2,5),1100,3,(0.18,0.65,0.8)),
        ("Retro warm fill",(4,4,4),650,4,(1.0,0.38,0.2))
    ]:
        bpy.ops.object.light_add(type="AREA",location=loc); light=bpy.context.object
        light.name=name; light.data.energy=power; light.data.shape="DISK"; light.data.size=size
        light.data.color=color
        light.rotation_euler=(Vector((0,0.8,1.8))-light.location).to_track_quat("-Z","Y").to_euler()
    scene=bpy.context.scene
    set_compatible_eevee(scene)
    base_width=320 if ps1 else 480
    base_height=180 if ps1 else 270
    if aspect_ratio=="9:16": base_width,base_height=base_height,base_width
    elif aspect_ratio=="1:1": base_width=base_height=min(base_width,base_height)
    scene.render.resolution_x=base_width
    scene.render.resolution_y=base_height
    scene.render.resolution_percentage=100
    scene.render.fps=12
    scene.frame_start=1; scene.frame_end=scene.render.fps*duration
    scene.world.color=(0.025,0.025,0.035)
    scene.view_settings.view_transform="Standard"
    scene.view_settings.look="Medium High Contrast"
    if hasattr(scene.view_settings,"dither_intensity"):
        scene.view_settings.dither_intensity=0.0 if ps1 else 0.5
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(OUT/"orni_retro_preview.png")
    # PS1 gets a smooth game-camera push. PS2 gets three deliberate cutscene framings.
    if ps1:
        cam.location=(4.2,-7.8,3.35); cam.keyframe_insert(data_path="location",frame=1)
        cam.location=(3.35,-6.6,3.0); cam.keyframe_insert(data_path="location",frame=scene.frame_end)
    else:
        shots=[
            (1,(4.2,-7.8,3.35),(0,0.9,1.65)),
            (max(2,int(scene.frame_end*0.34)),(2.7,-6.1,2.95),(0,0,2.0)),
            (max(3,int(scene.frame_end*0.68)),(0.9,-4.3,2.55),(0,0,2.45)),
            (scene.frame_end,(1.15,-4.5,2.5),(0,0,2.45))
        ]
        for frame,location,look_at in shots:
            cam.location=location
            cam.rotation_euler=(Vector(look_at)-cam.location).to_track_quat("-Z","Y").to_euler()
            cam.keyframe_insert(data_path="location",frame=frame)
            cam.keyframe_insert(data_path="rotation_euler",frame=frame)
        for frame in range(1,scene.frame_end+1,4):
            mouth.scale=(1,0.15 if (frame//4)%2 else 1.0,1)
            mouth.keyframe_insert(data_path="scale",frame=frame)
    if not ps1 and caption.strip():
        # Camera-parented subtitle card for the PS2 dialogue/meme format.
        words=caption.strip().split()
        lines=[]; line=""
        for word in words:
            candidate=(line+" "+word).strip()
            if len(candidate)>34 and line:
                lines.append(line); line=word
            else: line=candidate
        if line: lines.append(line)
        text_data=bpy.data.curves.new("ORNI PS2 dialogue caption","FONT")
        text_data.body="\n".join(lines[:3]); text_data.align_x="CENTER"; text_data.align_y="CENTER"; text_data.size=0.22
        caption_obj=bpy.data.objects.new("PS2 dialogue caption",text_data); scene.collection.objects.link(caption_obj)
        caption_obj.parent=cam; caption_obj.location=(0,-1.35,-4.2); caption_obj.rotation_euler=(0,0,0)
        caption_obj.data.materials.append(mats["cream"])
    head.rotation_euler[2]=0.0; head.keyframe_insert(data_path="rotation_euler",frame=1)
    head.rotation_euler[2]=0.16; head.keyframe_insert(data_path="rotation_euler",frame=scene.frame_end)
    for obj in scene.objects:
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation="CONSTANT" if (not ps1 and obj==cam) else "LINEAR"
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"orni_retro_cinema.blend"))
    bpy.ops.render.render(write_still=True)
    # Render temporary PNG frames, then encode with the system FFmpeg binary.
    # This avoids relying on Blender being compiled with its optional FFmpeg backend.
    frames_dir=OUT/"orni_retro_frames"
    if frames_dir.exists(): shutil.rmtree(frames_dir,ignore_errors=True)
    frames_dir.mkdir(parents=True,exist_ok=True)
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(frames_dir/"frame_")
    bpy.ops.render.render(animation=True)
    video_file=OUT/"orni_retro_cinema.mp4"
    try:
        subprocess.run(
            ["ffmpeg","-y","-framerate",str(scene.render.fps),"-i",str(frames_dir/"frame_%04d.png"),
             "-vf","scale=iw*3:ih*3:flags=neighbor","-c:v","libx264","-pix_fmt","yuv420p","-crf","20","-preset","veryfast",
             "-movflags","+faststart",str(video_file)],
            check=True,capture_output=True,text=True,timeout=180
        )
    except FileNotFoundError:
        raise RuntimeError("FFmpeg is not installed in the Blender worker.")
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("FFmpeg encoding failed: "+(exc.stderr or "unknown error")[-1200:])
    finally:
        shutil.rmtree(frames_dir,ignore_errors=True)
    preview_file=OUT/"orni_retro_preview.png"
    blend_file=OUT/"orni_retro_cinema.blend"
    if not preview_file.is_file() or preview_file.stat().st_size<256:
        raise RuntimeError("Blender did not produce a valid retro preview image.")
    if not blend_file.is_file() or blend_file.stat().st_size<1024:
        raise RuntimeError("Blender did not save the editable retro scene.")
    if not video_file.is_file() or video_file.stat().st_size<1024:
        raise RuntimeError("Blender did not produce a valid retro MP4. Check FFmpeg support and render logs.")
    return {"ok":True,"scene":"ORNI "+("PS1 low-poly" if ps1 else "PS2 cutscene")+" retro cinema","style":style,"blend":"/outputs/orni_retro_cinema.blend","preview":"/outputs/orni_retro_preview.png","video":"/outputs/orni_retro_cinema.mp4","frames":scene.frame_end,"fps":12,"durationSeconds":duration,"resolutionX":base_width,"resolutionY":base_height,"aspectRatio":aspect_ratio,"note":"Procedural proof-of-pipeline scene. Replace the placeholder character and set with approved CELVANI assets for production campaigns. PS2 mouth motion is a timing placeholder; optional on-screen dialogue caption is included, but no voice or audio is generated."}


JOBS=queue.Queue()
JOB_LOCK=threading.Lock()
JOB_STATUS={"status":"idle","stage":"Waiting for a production brief","progress":0,"frame":0,"frames":0,"error":None,"updatedAt":time.time()}

def set_job_status(**updates):
    with JOB_LOCK:
        JOB_STATUS.update(updates)
        JOB_STATUS["updatedAt"]=time.time()

@bpy.app.handlers.persistent
def track_render_frame(scene):
    with JOB_LOCK:
        if JOB_STATUS.get("status")=="running" and JOB_STATUS.get("stage")=="Rendering animation frames":
            current=max(0,int(scene.frame_current)-int(scene.frame_start)+1)
            total=max(1,int(scene.frame_end)-int(scene.frame_start)+1)
            JOB_STATUS["frame"]=current
            JOB_STATUS["frames"]=total
            JOB_STATUS["progress"]=min(90,25+int(65*current/total))
            JOB_STATUS["updatedAt"]=time.time()

if track_render_frame not in bpy.app.handlers.render_post:
    bpy.app.handlers.render_post.append(track_render_frame)

def process_jobs():
    try:
        job=JOBS.get_nowait()
    except queue.Empty:
        return 0.15
    try:
        set_job_status(status="running",stage="Preparing Blender scene",progress=1,frame=0,frames=0,error=None)
        if job["action"]=="hoodie":
            job["result"]=create_hoodie()
        elif job["action"]=="retro":
            job["result"]=create_retro_cinema(job.get("style","ps1"),job.get("duration",5),job.get("aspect_ratio","16:9"),job.get("caption",""))
        elif job["action"]=="render":
            scene=bpy.context.scene
            scene.render.filepath=str(OUT/"celvani_render.png")
            bpy.ops.render.render(write_still=True)
            job["result"]={"ok":True,"render":"/outputs/celvani_render.png"}
        else:
            job["result"]={"error":"unknown_action"}
    except Exception as e:
        job["result"]={"error":str(e)}
        set_job_status(status="failed",stage="Production failed",error=str(e),progress=0)
    finally:
        if job["result"] and job["result"].get("ok"):
            set_job_status(status="complete",stage="All deliverables verified",progress=100,error=None)
        job["done"].set()
    return 0.05

bpy.app.timers.register(process_jobs, first_interval=0.2, persistent=True)

class Handler(BaseHTTPRequestHandler):
    def reply(self, code, data):
        raw=json.dumps(data).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path=="/job-status":
            if not TOKEN or self.headers.get("Authorization")!="Bearer "+TOKEN: return self.reply(401,{"error":"unauthorized"})
            with JOB_LOCK: return self.reply(200,dict(JOB_STATUS))
        if self.path=="/health": return self.reply(200,{"ok":True,"service":"orni-blender-control","blender":bpy.app.version_string})
        if self.path=="/outputs": return self.reply(200,{"files":[p.name for p in OUT.iterdir() if p.is_file()]})
        if self.path in ("/outputs/celvani_hoodie_blockout.png","/outputs/celvani_hoodie_blockout.blend","/outputs/celvani_render.png","/outputs/orni_retro_preview.png","/outputs/orni_retro_cinema.blend","/outputs/orni_retro_cinema.mp4","/outputs/orni_crash_woods_preview.png","/outputs/orni_crash_woods.blend","/outputs/orni_crash_woods_15s.mp4"):
            if not TOKEN or self.headers.get("Authorization")!="Bearer "+TOKEN: return self.reply(401,{"error":"unauthorized"})
            path=OUT/self.path.rsplit("/",1)[-1]
            if not path.is_file(): return self.reply(404,{"error":"file_not_ready"})
            mime="image/png" if path.suffix==".png" else "video/mp4" if path.suffix==".mp4" else "application/octet-stream"
            data=path.read_bytes()
            self.send_response(200); self.send_header("Content-Type",mime); self.send_header("Content-Length",str(len(data))); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(data)
            return
        return self.reply(404,{"error":"not_found"})
    def do_POST(self):
        if not TOKEN or self.headers.get("Authorization")!="Bearer "+TOKEN: return self.reply(401,{"error":"unauthorized"})
        n=int(self.headers.get("Content-Length","0"))
        if n>4096: return self.reply(413,{"error":"payload_too_large"})
        body=json.loads(self.rfile.read(n) or b"{}")
        action={"/api/scene/celvani-hoodie":"hoodie","/api/scene/retro-cinema":"retro","/api/render":"render"}.get(self.path)
        if not action: return self.reply(404,{"error":"unknown_action"})
        set_job_status(status="queued",stage="Waiting for Blender render slot",progress=0,frame=0,frames=0,error=None)
        job={"action":action,"style":body.get("style","ps1") if isinstance(body,dict) else "ps1","duration":body.get("duration",5) if isinstance(body,dict) else 5,"aspect_ratio":body.get("aspectRatio","16:9") if isinstance(body,dict) else "16:9","caption":str(body.get("caption",""))[:120] if isinstance(body,dict) else "","done":threading.Event(),"result":None}
        JOBS.put(job)
        if not job["done"].wait(540):
            set_job_status(status="failed",stage="Render timed out",error="Blender operation timed out",progress=0)
            return self.reply(504,{"error":"Blender operation timed out"})
        result=job["result"] or {"error":"empty_result"}
        return self.reply(200 if result.get("ok") else 500,result)
    def log_message(self,*args): pass

def serve():
    HTTPServer(("0.0.0.0",8765),Handler).serve_forever()
threading.Thread(target=serve,daemon=True).start()
print("ORNI Blender control API listening on 8765")
