import bpy, json, os, threading, queue
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
    scene=bpy.context.scene; scene.render.engine="BLENDER_EEVEE_NEXT"
    scene.render.resolution_x=1200; scene.render.resolution_y=1200; scene.render.resolution_percentage=100
    scene.world.color=(0.12,0.12,0.12); scene.camera.data.lens=55
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(OUT/"celvani_hoodie_blockout.png")
    scene.view_settings.view_transform="Standard"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"celvani_hoodie_blockout.blend"))
    bpy.ops.render.render(write_still=True)
    return {"ok":True,"scene":"CELVANI oversized hoodie blockout","blend":"/outputs/celvani_hoodie_blockout.blend","render":"/outputs/celvani_hoodie_blockout.png","note":"Concept blockout only; not a manufacturing-accurate garment or approved logo."}


def create_retro_cinema(style="ps1", duration=5, aspect_ratio="16:9", caption=""):
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
    scene.render.engine="BLENDER_EEVEE_NEXT"
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
    # Export a short MP4 using Blender's bundled FFmpeg backend; no external AI service.
    scene.render.image_settings.file_format="FFMPEG"
    scene.render.ffmpeg.format="MPEG4"; scene.render.ffmpeg.codec="H264"
    scene.render.ffmpeg.constant_rate_factor="HIGH"; scene.render.ffmpeg.ffmpeg_preset="REALTIME"
    scene.render.filepath=str(OUT/"orni_retro_cinema.mp4")
    bpy.ops.render.render(animation=True)
    video_file=OUT/"orni_retro_cinema.mp4"
    preview_file=OUT/"orni_retro_preview.png"
    blend_file=OUT/"orni_retro_cinema.blend"
    if not preview_file.is_file() or preview_file.stat().st_size<256:
        raise RuntimeError("Blender did not produce a valid retro preview image.")
    if not blend_file.is_file() or blend_file.stat().st_size<1024:
        raise RuntimeError("Blender did not save the editable retro scene.")
    if not video_file.is_file() or video_file.stat().st_size<1024:
        raise RuntimeError("Blender did not produce a valid retro MP4. Check FFmpeg support and render logs.")
    return {"ok":True,"scene":"ORNI "+("PS1 low-poly" if ps1 else "PS2 cutscene")+" retro cinema","style":style,"blend":"/outputs/orni_retro_cinema.blend","preview":"/outputs/orni_retro_preview.png","video":"/outputs/orni_retro_cinema.mp4","frames":scene.frame_end,"fps":12,"durationSeconds":duration,"aspectRatio":aspect_ratio,"note":"Procedural proof-of-pipeline scene. Replace the placeholder character and set with approved CELVANI assets for production campaigns. PS2 mouth motion is a timing placeholder; optional on-screen dialogue caption is included, but no voice or audio is generated."}


JOBS=queue.Queue()

def process_jobs():
    try:
        job=JOBS.get_nowait()
    except queue.Empty:
        return 0.15
    try:
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
    finally:
        job["done"].set()
    return 0.05

bpy.app.timers.register(process_jobs, first_interval=0.2, persistent=True)

class Handler(BaseHTTPRequestHandler):
    def reply(self, code, data):
        raw=json.dumps(data).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path=="/health": return self.reply(200,{"ok":True,"service":"orni-blender-control","blender":bpy.app.version_string})
        if self.path=="/outputs": return self.reply(200,{"files":[p.name for p in OUT.iterdir() if p.is_file()]})
        if self.path in ("/outputs/celvani_hoodie_blockout.png","/outputs/celvani_hoodie_blockout.blend","/outputs/celvani_render.png","/outputs/orni_retro_preview.png","/outputs/orni_retro_cinema.blend","/outputs/orni_retro_cinema.mp4"):
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
        job={"action":action,"style":body.get("style","ps1") if isinstance(body,dict) else "ps1","duration":body.get("duration",5) if isinstance(body,dict) else 5,"aspect_ratio":body.get("aspectRatio","16:9") if isinstance(body,dict) else "16:9","caption":str(body.get("caption",""))[:120] if isinstance(body,dict) else "","done":threading.Event(),"result":None}
        JOBS.put(job)
        if not job["done"].wait(540): return self.reply(504,{"error":"Blender operation timed out"})
        result=job["result"] or {"error":"empty_result"}
        return self.reply(200 if result.get("ok") else 500,result)
    def log_message(self,*args): pass

def serve():
    HTTPServer(("0.0.0.0",8765),Handler).serve_forever()
threading.Thread(target=serve,daemon=True).start()
print("ORNI Blender control API listening on 8765")
