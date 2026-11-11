import bpy, json, os, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

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
    direction=bpy.mathutils.Vector((0,0,2.3))-cam.location; cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    cam.data.lens=55; bpy.context.scene.camera=cam
    for name,loc,power,size in [("Key softbox",(1,-5,7),1100,5),("Fill softbox",(-5,-2,4),700,4),("Rim light",(2,4,6),1300,3)]:
        bpy.ops.object.light_add(type="AREA", location=loc); l=bpy.context.object; l.name=name; l.data.energy=power; l.data.shape="DISK"; l.data.size=size
        d=bpy.mathutils.Vector((0,0,2.4))-l.location; l.rotation_euler=d.to_track_quat("-Z","Y").to_euler()
    scene=bpy.context.scene; scene.render.engine="BLENDER_EEVEE_NEXT"
    scene.render.resolution_x=1200; scene.render.resolution_y=1200; scene.render.resolution_percentage=100
    scene.world.color=(0.12,0.12,0.12); scene.camera.data.lens=55
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(OUT/"celvani_hoodie_blockout.png")
    scene.view_settings.view_transform="Standard"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"celvani_hoodie_blockout.blend"))
    return {"ok":True,"scene":"CELVANI oversized hoodie blockout","blend":"/outputs/celvani_hoodie_blockout.blend","render":"/outputs/celvani_hoodie_blockout.png","note":"Concept blockout only; not a manufacturing-accurate garment or approved logo."}

class Handler(BaseHTTPRequestHandler):
    def reply(self, code, data):
        raw=json.dumps(data).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path=="/health": return self.reply(200,{"ok":True,"service":"orni-blender-control","blender":bpy.app.version_string})
        if self.path=="/outputs": return self.reply(200,{"files":[p.name for p in OUT.iterdir() if p.is_file()]})
        return self.reply(404,{"error":"not_found"})
    def do_POST(self):
        if not TOKEN or self.headers.get("Authorization")!="Bearer "+TOKEN: return self.reply(401,{"error":"unauthorized"})
        n=int(self.headers.get("Content-Length","0"))
        if n>4096: return self.reply(413,{"error":"payload_too_large"})
        body=json.loads(self.rfile.read(n) or b"{}")
        if self.path=="/api/scene/celvani-hoodie":
            try: return self.reply(200,create_hoodie())
            except Exception as e: return self.reply(500,{"error":str(e)})
        if self.path=="/api/render":
            try:
                scene=bpy.context.scene; scene.render.filepath=str(OUT/"celvani_render.png"); bpy.ops.render.render(write_still=True)
                return self.reply(200,{"ok":True,"render":"/outputs/celvani_render.png"})
            except Exception as e: return self.reply(500,{"error":str(e)})
        return self.reply(404,{"error":"unknown_action"})
    def log_message(self,*args): pass

def serve():
    HTTPServer(("0.0.0.0",8765),Handler).serve_forever()
threading.Thread(target=serve,daemon=True).start()
print("ORNI Blender control API listening on 8765")
