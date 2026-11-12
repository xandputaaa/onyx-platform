import bpy, json, os, threading, queue, subprocess, shutil, math, time, urllib.request, tempfile, zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from mathutils import Vector, Matrix

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
    for obj in meshes:
        if not obj.data.polygons:
            raise RuntimeError("UV validation failed: mesh has no polygon data: "+obj.name)
        if not obj.data.uv_layers or not obj.data.uv_layers.active:
            raise RuntimeError("UV validation failed: missing UV map on "+obj.name)
        uv_data=obj.data.uv_layers.active.data
        if len(uv_data)!=len(obj.data.loops):
            raise RuntimeError("UV validation failed: incomplete UV coordinates on "+obj.name)
        for item in uv_data:
            if not (math.isfinite(item.uv.x) and math.isfinite(item.uv.y)):
                raise RuntimeError("UV validation failed: non-finite UV coordinate on "+obj.name)
        for material in obj.data.materials:
            if not material or not material.use_nodes: continue
            for node in material.node_tree.nodes:
                if node.type=="TEX_IMAGE":
                    if not node.image or not node.image.has_data:
                        raise RuntimeError("Texture validation failed: missing image data in "+material.name+" on "+obj.name)
                    node.interpolation="Closest"
                    try: node.image.pack()
                    except Exception: pass
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



def fetch_polyhaven_photo(asset_id, label):
    """Fetch a real CC0 photographic diffuse map, reduce it to PSX texels, dither and pack it."""
    api_url="https://api.polyhaven.com/files/"+asset_id
    request=urllib.request.Request(api_url,headers={"User-Agent":"ORNI-Creative-Asset-Pipeline/1.0"})
    with urllib.request.urlopen(request,timeout=35) as response:
        tree=json.loads(response.read().decode("utf-8"))
    candidates=[]
    def walk(node,path=()):
        if isinstance(node,dict):
            if isinstance(node.get("url"),str):
                p="/".join(path).lower()
                candidates.append((p,node["url"]))
            for key,value in node.items(): walk(value,path+(str(key),))
        elif isinstance(node,list):
            for index,value in enumerate(node): walk(value,path+(str(index),))
    walk(tree)
    def score(item):
        p,url=item
        return (100 if "1k" in p else 60 if "2k" in p else 10,
                50 if "jpg" in p or url.lower().endswith(".jpg") else 0,
                40 if "diff" in p or "color" in p or "albedo" in p else 0)
    jpg=[item for item in candidates if "jpg" in item[0] or ".jpg" in item[1].lower()]
    diffuse=[item for item in jpg if any(token in item[0] for token in ("diff","color","albedo"))]
    pool=diffuse or jpg
    if not pool:
        raise RuntimeError("Poly Haven returned no JPG diffuse map for "+asset_id)
    source_url=sorted(pool,key=score,reverse=True)[0][1]
    req=urllib.request.Request(source_url,headers={"User-Agent":"ORNI-Creative-Asset-Pipeline/1.0"})
    with urllib.request.urlopen(req,timeout=60) as response: image_bytes=response.read()
    fd,temp_path=tempfile.mkstemp(prefix="orni-photo-",suffix=".jpg")
    os.close(fd)
    try:
        with open(temp_path,"wb") as handle: handle.write(image_bytes)
        image=bpy.data.images.load(temp_path,check_existing=False)
        image.name=label+" | real photographic source"
        image.scale(64,64)
        px=list(image.pixels[:])
        bayer=((0,8,2,10),(12,4,14,6),(3,11,1,9),(15,7,13,5))
        for y in range(64):
            for x in range(64):
                threshold=(bayer[y%4][x%4]/16.0)-0.46875
                i=(y*64+x)*4
                for channel in range(3):
                    value=max(0.0,min(1.0,px[i+channel]))
                    px[i+channel]=max(0.0,min(1.0,(math.floor(value*31.0+threshold+0.5))/31.0))
        image.pixels.foreach_set(px)
        image.pack()
        return image
    finally:
        try: os.unlink(temp_path)
        except OSError: pass


def import_oga_psx_vehicle(car_root, photo_maps):
    """Import a CC0 PSX car from OpenGameArt when the free source pack is reachable."""
    url="https://opengameart.org/sites/default/files/psx_style_cars_by_ggbot_august2023.zip"
    cache=Path("/tmp/orni_psx_style_cars.zip")
    if not cache.exists() or cache.stat().st_size<10000:
        req=urllib.request.Request(url,headers={"User-Agent":"ORNI-Creative-Asset-Pipeline/1.0"})
        with urllib.request.urlopen(req,timeout=60) as response: data=response.read()
        cache.write_bytes(data)
    extract=Path("/tmp/orni_psx_style_cars")
    if not extract.exists():
        extract.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(cache) as archive: archive.extractall(extract)
    blend_files=sorted(extract.rglob("*.blend"))
    if not blend_files:
        raise RuntimeError("The CC0 GGBotNet vehicle archive contained no Blender model files.")
    chosen=next((p for p in blend_files if any(k in p.stem.lower() for k in ("car1","car_1","car-1","vehicle1","vehicle_1"))),blend_files[0])
    with bpy.data.libraries.load(str(chosen),link=False) as (source,target):
        names=list(source.objects)
        target.objects=names
    imported=[obj for obj in target.objects if obj and obj.type=="MESH"]
    if not imported:
        raise RuntimeError("The selected CC0 GGBotNet vehicle project contained no usable mesh objects.")
    for obj in imported:
        bpy.context.scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in imported: obj.select_set(True)
    bpy.context.view_layer.objects.active=imported[0]
    bpy.ops.object.join()
    vehicle=bpy.context.object
    vehicle.name="Imported CC0 PSX vehicle | GGBotNet"
    # Preserve original imported textures; add a photo-derived enamel atlas only where the model has none.
    for material in list(vehicle.data.materials):
        if material and material.use_nodes:
            image_nodes=[node for node in material.node_tree.nodes if node.type=="TEX_IMAGE"]
            has_image=any(node.image and node.image.has_data for node in image_nodes)
            for node in image_nodes:
                if node.image and node.image.has_data:
                    node.interpolation="Closest"
                    try: node.image.pack()
                    except Exception: pass
            shader=material.node_tree.nodes.get("Principled BSDF")
            if not has_image and shader:
                tex=material.node_tree.nodes.new("ShaderNodeTexImage")
                tex.name="CC0 photographic PSX enamel | nearest"
                tex.image=photo_maps["Weathered car paint"]; tex.interpolation="Closest"
                material.node_tree.links.new(tex.outputs["Color"],shader.inputs["Base Color"])
    if not vehicle.data.materials:
        fallback=mat("Imported vehicle | photo-derived enamel",(0.22,0.025,0.035),0.1,0.62)
        tex=fallback.node_tree.nodes.new("ShaderNodeTexImage")
        tex.name="CC0 photographic PSX enamel | nearest"
        tex.image=photo_maps["Weathered car paint"]; tex.interpolation="Closest"
        fallback.node_tree.links.new(tex.outputs["Color"],fallback.node_tree.nodes.get("Principled BSDF").inputs["Base Color"])
        vehicle.data.materials.append(fallback)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    dims=vehicle.dimensions
    if dims.x>dims.y:
        vehicle.rotation_euler[2]=math.radians(90)
        bpy.ops.object.transform_apply(location=False,rotation=True,scale=False)
    dims=vehicle.dimensions
    factor=min(2.35/max(dims.x,0.001),4.25/max(dims.y,0.001),1.8/max(dims.z,0.001))
    vehicle.scale=(factor,factor,factor)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    corners=[Vector(corner) for corner in vehicle.bound_box]
    min_x=min(v.x for v in corners); max_x=max(v.x for v in corners)
    min_y=min(v.y for v in corners); max_y=max(v.y for v in corners)
    min_z=min(v.z for v in corners)
    vehicle.location.x=-(min_x+max_x)/2
    vehicle.location.y=-(min_y+max_y)/2
    vehicle.location.z=-min_z
    vehicle.parent=car_root
    vehicle.matrix_parent_inverse=Matrix.Identity(4)
    # Source archives are temporary; imported mesh and packed materials remain in the scene.
    shutil.rmtree(extract,ignore_errors=True)
    try: cache.unlink()
    except OSError: pass
    return vehicle


def import_cc0_forest_pack(scene, photo_maps):
    """Import real CC0 low-poly tree assets; pack materials and remove temporary archive."""
    url="https://opengameart.org/sites/default/files/trees_and_plants_0.zip"
    cache=Path("/tmp/orni_cc0_trees.zip")
    extract=Path("/tmp/orni_cc0_trees")
    if not cache.exists() or cache.stat().st_size<10000:
        req=urllib.request.Request(url,headers={"User-Agent":"ORNI-Creative-Asset-Pipeline/1.0"})
        with urllib.request.urlopen(req,timeout=60) as response: cache.write_bytes(response.read())
    if extract.exists(): shutil.rmtree(extract,ignore_errors=True)
    extract.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(cache) as archive: archive.extractall(extract)
    blend_files=sorted(extract.rglob("*.blend"))
    if not blend_files:
        raise RuntimeError("The CC0 forest pack downloaded but contained no Blender project.")
    prototypes=[]
    for blend_path in blend_files[:8]:
        with bpy.data.libraries.load(str(blend_path),link=False) as (source,target):
            target.objects=list(source.objects)
        imported=[]
        for obj in target.objects:
            if not obj: continue
            if obj.type=="MESH":
                scene.collection.objects.link(obj)
                imported.append(obj)
            else:
                bpy.data.objects.remove(obj,do_unlink=True)
        meshes=imported
        if not meshes: continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in meshes: obj.select_set(True)
        bpy.context.view_layer.objects.active=meshes[0]
        bpy.ops.object.join()
        tree=bpy.context.object
        tree.name="Imported CC0 low-poly forest tree | "+blend_path.stem
        # Retain source maps; any untextured material receives a real photo-derived map.
        for slot in tree.data.materials:
            if not slot: continue
            nodes=slot.node_tree.nodes if slot.use_nodes else None
            image_nodes=[n for n in nodes or [] if n.type=="TEX_IMAGE"]
            has_image=any(n.image and n.image.has_data for n in image_nodes)
            if has_image:
                for n in image_nodes:
                    if n.image and n.image.has_data:
                        n.interpolation="Closest"
                        try: n.image.pack()
                        except Exception: pass
                continue
            if not slot.use_nodes: slot.use_nodes=True
            shader=slot.node_tree.nodes.get("Principled BSDF")
            if not shader: continue
            key="Tree bark" if any(word in slot.name.lower() for word in ("bark","trunk","wood")) else "Forest leaves"
            uv=slot.node_tree.nodes.new("ShaderNodeUVMap"); uv.uv_map="UVMap"
            tex=slot.node_tree.nodes.new("ShaderNodeTexImage"); tex.image=photo_maps[key]; tex.interpolation="Closest"; tex.extension="REPEAT"
            slot.node_tree.links.new(uv.outputs["UV"],tex.inputs["Vector"])
            slot.node_tree.links.new(tex.outputs["Color"],shader.inputs["Base Color"])
        if not tree.data.materials:
            slot=mat("CC0 tree | photo-derived forest leaves",(0.04,0.12,0.065),0,1)
            uv=slot.node_tree.nodes.new("ShaderNodeUVMap"); uv.uv_map="UVMap"
            tex=slot.node_tree.nodes.new("ShaderNodeTexImage"); tex.image=photo_maps["Forest leaves"]; tex.interpolation="Closest"
            slot.node_tree.links.new(uv.outputs["UV"],tex.inputs["Vector"])
            slot.node_tree.links.new(tex.outputs["Color"],slot.node_tree.nodes.get("Principled BSDF").inputs["Base Color"])
            tree.data.materials.append(slot)
        bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
        verts=tree.data.vertices
        if not verts: continue
        min_x=min(v.co.x for v in verts); max_x=max(v.co.x for v in verts)
        min_y=min(v.co.y for v in verts); max_y=max(v.co.y for v in verts)
        min_z=min(v.co.z for v in verts); max_z=max(v.co.z for v in verts)
        height=max(max_z-min_z,0.001); factor=7.5/height
        center_x=(min_x+max_x)/2; center_y=(min_y+max_y)/2
        for v in verts:
            v.co.x=(v.co.x-center_x)*factor
            v.co.y=(v.co.y-center_y)*factor
            v.co.z=(v.co.z-min_z)*factor
        tree.data.update(); tree.location=(0,0,0)
        prototypes.append(tree)
    shutil.rmtree(extract,ignore_errors=True)
    try: cache.unlink()
    except OSError: pass
    if not prototypes:
        raise RuntimeError("No usable mesh models were found in the CC0 forest pack.")
    return prototypes


def create_crash_woods_cinema():
    """Rebuilt PS1/PS2 crash-woods short with authored geometry, grunge maps and edited shots."""
    import random
    set_job_status(stage="Rebuilding custom PSX assets",progress=4)
    clear_scene()
    scene=bpy.context.scene
    set_compatible_eevee(scene)
    scene.render.resolution_x=180; scene.render.resolution_y=320
    scene.render.resolution_percentage=100; scene.render.fps=12
    scene.frame_start=1; scene.frame_end=180
    scene.world.color=(0.004,0.008,0.018)
    scene.world.use_nodes=True
    world_bg=scene.world.node_tree.nodes.get("Background")
    if world_bg:
        world_bg.inputs["Color"].default_value=(0.001,0.002,0.008,1)
        world_bg.inputs["Strength"].default_value=0.08
    scene.view_settings.view_transform="Standard"
    scene.view_settings.look="Medium High Contrast"
    if hasattr(scene.view_settings,"dither_intensity"): scene.view_settings.dither_intensity=0.35
    random.seed(27)

    photo_maps={}
    for asset_id,label in (("asphalt_01","Road asphalt"),("pine_bark","Tree bark"),("forest_ground_04","Forest floor"),("forest_leaves_04","Forest leaves"),("rusty_painted_metal","Weathered car paint"),("polystyrene","Crash dummy composite"),("rubber_tiles","Tire rubber"),("metal_plate","Road hardware")):
        try:
            photo_maps[label]=fetch_polyhaven_photo(asset_id,label)
        except Exception as exc:
            raise RuntimeError("Required CC0 photographic texture download failed for "+asset_id+": "+str(exc))

    def textured_mat(name, base, rough=0.9, seed=1, metallic=0.0, photo=None):
        m=mat(name,base,metallic,rough)
        image=photo_maps.get(photo) if photo else None
        if image is None:
            raise RuntimeError("No photographic PSX texture assigned to major material: "+name)
        nodes=m.node_tree.nodes; shader=nodes.get("Principled BSDF")
        uv=nodes.new("ShaderNodeUVMap"); uv.uv_map="UVMap"; uv.name=name+" | explicit UV coordinates"
        tex=nodes.new("ShaderNodeTexImage"); tex.name=name+" | 64px photo-derived PSX atlas"
        tex.image=image; tex.interpolation="Closest"; tex.extension="REPEAT"
        m.node_tree.links.new(uv.outputs["UV"],tex.inputs["Vector"])
        m.node_tree.links.new(tex.outputs["Color"],shader.inputs["Base Color"])
        return m

    def mesh_obj(name, verts, faces, material, bevel=0):
        mesh=bpy.data.meshes.new(name+" mesh"); mesh.from_pydata(verts,[],faces); mesh.materials.append(material); mesh.update()
        obj=bpy.data.objects.new(name,mesh); scene.collection.objects.link(obj)
        if bevel:
            mod=obj.modifiers.new("Controlled low-poly edge chamfer","BEVEL"); mod.width=bevel; mod.segments=1
            obj.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
        return obj

    def box_mesh(name, center, size, material, bevel=0):
        x,y,z=center; a,b,c=(v/2 for v in size)
        verts=[(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
               (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)]
        faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        return mesh_obj(name,verts,faces,material,bevel)

    def tapered_limb(name, p1, p2, r1, r2, material, sides=7):
        a=Vector(p1); b=Vector(p2); axis=(b-a).normalized()
        helper=Vector((0,0,1)) if abs(axis.z)<0.92 else Vector((0,1,0))
        u=axis.cross(helper).normalized(); v=axis.cross(u).normalized()
        verts=[]
        for point,radius in ((a,r1),(b,r2)):
            for i in range(sides):
                angle=2*math.pi*i/sides
                q=(point-a)+radius*(math.cos(angle)*u+math.sin(angle)*v)
                verts.append(tuple(q))
        faces=[]
        for i in range(sides):
            j=(i+1)%sides
            faces.append((i,j,sides+j,sides+i))
        faces.extend([tuple(range(sides-1,-1,-1)),tuple(range(sides,2*sides))])
        obj=mesh_obj(name,verts,faces,material)
        obj.location=a
        return obj

    def parent_local(obj, root):
        obj.parent=root
        obj.matrix_parent_inverse=Matrix.Identity(4)
        return obj

    road=textured_mat("Wet asphalt | photographed road grit",(0.035,0.045,0.06),0.98,4,photo="Road asphalt")
    soil=textured_mat("Forest loam | photographed forest soil",(0.07,0.085,0.055),1,7,photo="Forest floor")
    bark=textured_mat("Bark | photographed pine bark",(0.20,0.105,0.055),1,11,photo="Tree bark")
    foliage=textured_mat("Pine | photographic leaf-litter atlas",(0.035,0.12,0.075),1,14,photo="Forest leaves")
    paint=textured_mat("Car paint | photographed weathered red enamel",(0.25,0.025,0.035),0.68,18,0.12,photo="Weathered car paint")
    glass=mat("Glass | smoked blue reflections",(0.025,0.09,0.13),0.45,0.16)
    tire=textured_mat("Tire rubber | photographed worn rubber",(0.018,0.022,0.027),0.92,24,photo="Tire rubber")
    dummy_mat=textured_mat("Crash dummy | scratched polystyrene composite",(0.62,0.58,0.48),0.72,29,photo="Crash dummy composite")
    joint_mat=textured_mat("Crash dummy | photographed graphite joint material",(0.035,0.045,0.055),0.76,32,0.1,photo="Road hardware")
    metal=textured_mat("Road hardware | photographed worn metal",(0.12,0.14,0.16),0.72,35,0.45,photo="Road hardware")
    warm=mat("Headlamp | amber glass",(0.9,0.42,0.12),0.15,0.22)
    moon_mat=mat("Moon | bone-white",(0.78,0.79,0.72),0.0,0.82)

    set_job_status(stage="Importing CC0 forest models and building textured road",progress=12)
    box_mesh("Roadbed | beveled shoulder",(0,0,-0.34),(8,62,0.48),soil)
    box_mesh("Asphalt ribbon",(0,0,-0.07),(6.5,62,0.18),road)
    for x in (-3.25,3.25):
        box_mesh("Broken road edge", (x,0,0.01),(0.18,62,0.12),metal)
    # Populate the set with real imported CC0 low-poly tree models, not repeated cones.
    tree_models=import_cc0_forest_pack(scene,photo_maps)
    tree_index=0
    for side in (-1,1):
        for i in range(27):
            y=-28+i*2.1+random.uniform(-0.65,0.65)
            x=side*random.uniform(5.1,11.5)
            prototype=tree_models[tree_index%len(tree_models)]; tree_index+=1
            tree=prototype if tree_index<=len(tree_models) else prototype.copy()
            if tree is not prototype:
                tree.data=prototype.data
                scene.collection.objects.link(tree)
            tree.name="Forest pine | imported CC0 low-poly model"
            scale=random.uniform(0.78,1.22)
            tree.scale=(scale,scale,scale)
            tree.location=(x,y,0)
            tree.rotation_euler[2]=random.uniform(-math.pi,math.pi)
    impact_tree=tree_models[0].copy(); impact_tree.data=tree_models[0].data
    scene.collection.objects.link(impact_tree)
    impact_tree.name="Impact cedar | imported CC0 low-poly model"
    impact_tree.scale=(1.35,1.35,1.35); impact_tree.location=(1.18,-1.8,0)
    impact_tree.rotation_euler[2]=0.42

    # Vehicle is a single authored assembly parented to a moving root.
    car_root=bpy.data.objects.new("Car rig | vehicle root",None); scene.collection.objects.link(car_root)
    car_parts=[]
    def car_part(obj): car_parts.append(parent_local(obj,car_root)); return obj
    # Longitudinal Y axis; body profile tapers at nose and tail.
    body_verts=[(-1.12,-2.1,0.58),(1.12,-2.1,0.58),(1.2,1.9,0.58),(-1.2,1.9,0.58),
                (-1.05,-1.9,1.25),(1.05,-1.9,1.25),(1.08,1.7,1.25),(-1.08,1.7,1.25)]
    body_faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    car_part(mesh_obj("Car shell | sculpted compact coupe",body_verts,body_faces,paint,0.09))
    # Hood, rear deck, cabin glass and roof are separate shaped surfaces.
    car_part(box_mesh("Long hood",(0,-1.28,1.24),(2.05,1.45,0.16),paint,0.06))
    car_part(box_mesh("Rear deck",(0,1.45,1.28),(2.08,0.72,0.18),paint,0.05))
    cabin_verts=[(-0.83,-0.72,1.28),(0.83,-0.72,1.28),(0.78,1.12,1.28),(-0.78,1.12,1.28),
                 (-0.68,-0.42,2.05),(0.68,-0.42,2.05),(0.65,0.87,2.05),(-0.65,0.87,2.05)]
    cabin_faces=[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
    car_part(mesh_obj("Cabin | window frame and roof geometry",cabin_verts,cabin_faces,paint))
    car_part(mesh_obj("Windshield | smoked front glass",[(-.63,-.43,1.36),(.63,-.43,1.36),(.57,-.35,1.97),(-.57,-.35,1.97)],[(0,1,2,3)],glass))
    car_part(mesh_obj("Rear glass | smoked pane",[(-.57,.84,1.38),(.57,.84,1.38),(.61,.91,1.97),(-.61,.91,1.97)],[(0,1,2,3)],glass))
    for side in (-1,1):
        car_part(mesh_obj("Side window | driver/passenger",[(side*.84,-.58,1.38),(side*.84,.78,1.38),(side*.68,.72,1.96),(side*.68,-.35,1.96)],[(0,1,2,3)],glass))
        for y in (-1.35,1.25):
            bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=0.48,depth=0.22,location=(side*1.08,y,0.52),rotation=(0,math.pi/2,0))
            wheel=bpy.context.object; wheel.name="Tire | chunky polygon tread"; wheel.data.materials.append(tire); car_part(wheel)
            bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=0.23,depth=0.235,location=(side*1.20,y,0.52),rotation=(0,math.pi/2,0))
            hub=bpy.context.object; hub.name="Wheel hub | stamped metal"; hub.data.materials.append(metal); car_part(hub)
        for y in (-1.95,):
            car_part(box_mesh("Amber headlight",(side*0.73,y,1.02),(0.42,0.09,0.22),warm,0.025))
        car_part(box_mesh("Side sill",(side*1.12,0,0.62),(0.12,2.55,0.22),metal,0.02))
    car_part(box_mesh("Front bumper",(0,-2.12,0.62),(2.28,0.18,0.22),metal,0.035))
    car_part(box_mesh("Rear bumper",(0,2.0,0.62),(2.28,0.18,0.22),metal,0.035))
    car_part(box_mesh("Front grille",(0,-2.18,0.91),(0.72,0.05,0.22),tire))
    # Impact damage: buckled hood seam and broken glass shards.
    for i in range(5):
        x=-0.55+i*0.27
        car_part(tapered_limb("Hood crease | impact damage",(x,-1.95,1.34),(x+0.12,-0.95,1.37),0.018,0.012,metal,4))
    external_vehicle=None
    try:
        external_vehicle=import_oga_psx_vehicle(car_root,photo_maps)
    except Exception as exc:
        raise RuntimeError("CC0 PSX vehicle asset import failed: "+str(exc))
    if not external_vehicle:
        raise RuntimeError("Required CC0 GGBotNet PSX vehicle was not imported; refusing to render a procedural substitute.")
    for part in car_parts: part.hide_render=True; part.hide_viewport=True
    external_vehicle.name="GGBotNet CC0 PSX car | main hero vehicle"
    car_root.location=(0,-13,0); car_root.keyframe_insert(data_path="location",frame=1)
    car_root.location=(0,0,0); car_root.keyframe_insert(data_path="location",frame=27)
    car_root.location=(0,0.65,0); car_root.keyframe_insert(data_path="location",frame=34)
    car_root.location=(0,0.65,0); car_root.keyframe_insert(data_path="location",frame=180)

    # Articulated crash dummy with tapered limbs, real pivots and a grouped root.
    dummy_root=bpy.data.objects.new("Crash dummy rig | pelvis root",None); scene.collection.objects.link(dummy_root)
    dummy_root.parent=car_root; dummy_root.matrix_parent_inverse=Matrix.Identity(4)
    dummy_root.location=(0,0,0)
    def dummy_piece(obj):
        obj.parent=dummy_root; obj.matrix_parent_inverse=Matrix.Identity(4); return obj
    # Local character origin at ground level; cabin is centered around z=1.2.
    dummy_piece(box_mesh("Dummy torso | tapered suit shell",(0,0,1.34),(0.62,0.38,0.88),dummy_mat,0.035))
    dummy_piece(box_mesh("Dummy pelvis | graphite core",(0,0,0.83),(0.52,0.34,0.3),joint_mat,0.025))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=0.31,location=(0,0,2.02))
    head=bpy.context.object; head.name="Dummy head | faceted helmet"; head.data.materials.append(dummy_mat); dummy_piece(head)
    # Face plate, dark visor and serial-marking stripe.
    dummy_piece(box_mesh("Dummy faceplate",(0,-0.285,2.02),(0.34,0.035,0.20),joint_mat,0.01))
    dummy_piece(box_mesh("Dummy serial stripe",(0,-0.309,1.68),(0.42,0.025,0.055),metal,0.008))
    limb_rigs=[]
    for side in (-1,1):
        shoulder=(side*0.39,0,1.66); elbow=(side*0.53,-0.015,1.18); wrist=(side*0.58,-0.07,0.78)
        hip=(side*0.18,0,0.75); knee=(side*0.22,-0.02,0.38); ankle=(side*0.24,-0.10,0.08)
        upper=dummy_piece(tapered_limb("Dummy upper arm | tapered shell",shoulder,elbow,0.15,0.105,dummy_mat))
        lower=dummy_piece(tapered_limb("Dummy forearm | tapered shell",elbow,wrist,0.11,0.075,dummy_mat))
        thigh=dummy_piece(tapered_limb("Dummy thigh | tapered shell",hip,knee,0.16,0.115,dummy_mat))
        shin=dummy_piece(tapered_limb("Dummy shin | tapered shell",knee,ankle,0.12,0.075,dummy_mat))
        for joint_loc in (shoulder,elbow,wrist,hip,knee,ankle):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=0.105,location=joint_loc)
            j=bpy.context.object; j.name="Dummy joint | dark mechanical bearing"; j.data.materials.append(joint_mat); dummy_piece(j)
        foot_obj=box_mesh("Dummy foot | broad planted sole",(side*0.24,-0.28,0.07),(0.28,0.48,0.13),joint_mat,0.025)
        bpy.ops.object.select_all(action="DESELECT"); foot_obj.select_set(True); bpy.context.view_layer.objects.active=foot_obj
        bpy.context.scene.cursor.location=Vector(ankle)
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        bpy.context.scene.cursor.location=(0,0,0)
        foot=dummy_piece(foot_obj)
        limb_rigs.append((side,upper,lower,thigh,shin,foot))
    # Door swings open to camera-facing side; door is a custom panel on a hinge empty.
    door_hinge=bpy.data.objects.new("Driver door | hinge",None); scene.collection.objects.link(door_hinge)
    door_hinge.location=(1.0,-0.62,1.18); parent_local(door_hinge,car_root)
    door=box_mesh("Driver door | sculpted burgundy panel",(0,0,0),(0.12,1.18,0.78),paint,0.035)
    door.parent=door_hinge; door.matrix_parent_inverse=Matrix.Identity(4)
    door.location=(0.06,0.59,0)
    door_hinge.rotation_euler[2]=0; door_hinge.keyframe_insert(data_path="rotation_euler",frame=34)
    door_hinge.rotation_euler[2]=math.radians(-68); door_hinge.keyframe_insert(data_path="rotation_euler",frame=43)
    door_hinge.rotation_euler[2]=math.radians(-68); door_hinge.keyframe_insert(data_path="rotation_euler",frame=68)
    door.hide_render=False
    door_hinge.hide_render=False

    # Dummy remains in the moving cabin through impact, then exits and walks away.
    dummy_root.location=(0,0,0); dummy_root.keyframe_insert(data_path="location",frame=1)
    dummy_root.location=(0,0,0); dummy_root.keyframe_insert(data_path="location",frame=27)
    dummy_root.location=(0,0,0); dummy_root.keyframe_insert(data_path="location",frame=34)
    dummy_root.location=(0.85,0.05,0); dummy_root.keyframe_insert(data_path="location",frame=38)
    dummy_root.location=(1.85,0.45,0); dummy_root.keyframe_insert(data_path="location",frame=55)
    dummy_root.location=(2.4,1.6,0); dummy_root.keyframe_insert(data_path="location",frame=70)
    dummy_root.location=(3.2,4.8,0); dummy_root.keyframe_insert(data_path="location",frame=105)
    dummy_root.location=(4.2,8.2,0); dummy_root.keyframe_insert(data_path="location",frame=145)
    dummy_root.location=(4.4,8.8,0); dummy_root.keyframe_insert(data_path="location",frame=180)
    # Alternating arm and leg rotations around authored limb origins, with clear foot contact beats.
    for side,upper,lower,thigh,shin,foot in limb_rigs:
        phase=0 if side<0 else math.pi
        for frame in range(70,146,5):
            t=(frame-70)*0.38+phase
            upper.rotation_euler[1]=0.32*math.sin(t)
            upper.keyframe_insert(data_path="rotation_euler",frame=frame)
            lower.rotation_euler[1]=0.20*math.sin(t+0.7)
            lower.keyframe_insert(data_path="rotation_euler",frame=frame)
            thigh.rotation_euler[1]=0.38*math.sin(t+math.pi)
            thigh.keyframe_insert(data_path="rotation_euler",frame=frame)
            shin.rotation_euler[1]=max(0,0.25*math.sin(t+math.pi+0.5))
            shin.keyframe_insert(data_path="rotation_euler",frame=frame)
            foot.rotation_euler[1]=0.10*math.sin(t+math.pi)
            foot.keyframe_insert(data_path="rotation_euler",frame=frame)

    # A subtle EEVEE volumetric haze gives depth without washing out the foreground.
    fog_mesh=bpy.data.meshes.new("Atmospheric fog bounds mesh")
    fog_obj=bpy.data.objects.new("Atmospheric fog | low-density forest volume",fog_mesh); scene.collection.objects.link(fog_obj)
    fog_verts=[(-22,-32,-1),(22,-32,-1),(22,32,-1),(-22,32,-1),(-22,-32,25),(22,-32,25),(22,32,25),(-22,32,25)]
    fog_faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    fog_mesh.from_pydata(fog_verts,[],fog_faces)
    fog_mat=bpy.data.materials.new("Atmosphere | cool forest fog"); fog_mat.use_nodes=True
    fog_nodes=fog_mat.node_tree.nodes; fog_nodes.clear()
    fog_out=fog_nodes.new("ShaderNodeOutputMaterial"); fog_vol=fog_nodes.new("ShaderNodeVolumePrincipled")
    fog_vol.inputs["Color"].default_value=(0.12,0.18,0.27,1)
    fog_vol.inputs["Density"].default_value=0.012
    fog_mat.node_tree.links.new(fog_vol.outputs["Volume"],fog_out.inputs["Volume"])
    fog_obj.data.materials.append(fog_mat)
    # Moon, roadside debris, power pole and wires add authored environmental scale cues.
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=2.1,location=(-1,16,17))
    moon=bpy.context.object; moon.name="Moon | low-poly cutscene reveal"; moon.data.materials.append(moon_mat)
    for i in range(36):
        x=random.uniform(-25,25); y=random.uniform(-8,24); z=random.uniform(11,23)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=0.045,location=(x,y,z))
        star=bpy.context.object; star.name="Sky pixel | distant star"; star.data.materials.append(moon_mat)
    for i in range(12):
        x=random.choice((-1,1))*random.uniform(3.8,5.4); y=random.uniform(-24,12)
        pebble=box_mesh("Roadside debris | angular stone",(x,y,0.08),(random.uniform(.12,.4),random.uniform(.12,.5),.13),bark)
    set_job_status(stage="Rigging shots, lighting and PSX post look",progress=25)
    bpy.ops.object.light_add(type="SUN",location=(0,0,12))
    sun=bpy.context.object; sun.name="Cold moonlight"; sun.data.energy=0.48; sun.data.color=(0.43,0.55,1.0)
    sun.rotation_euler=(0.38,-0.42,-0.25)
    bpy.ops.object.light_add(type="AREA",location=(0,-3,3.0))
    key=bpy.context.object; key.name="Amber headlamp bounce"; key.data.energy=120; key.data.shape="DISK"; key.data.size=4
    key.data.color=(1.0,0.54,0.28); key.rotation_euler=(math.radians(24),0,0)
    bpy.ops.object.light_add(type="AREA",location=(4.8,1.5,3.8))
    rim=bpy.context.object; rim.name="Blue moon rim | character separation"; rim.data.energy=180; rim.data.shape="DISK"; rim.data.size=3
    rim.data.color=(0.28,0.42,1.0); rim.rotation_euler=(math.radians(32),0,math.radians(155))
    bpy.ops.object.light_add(type="POINT",location=(0,-2.1,1.15))
    lamp=bpy.context.object; lamp.name="Car headlamp practical"; lamp.data.energy=42; lamp.data.shadow_soft_size=0.8; lamp.data.color=(1.0,0.48,0.2)
    bpy.ops.object.camera_add(location=(0,-25,6))
    cam=bpy.context.object; cam.name="ORNI locked 9:16 PS2 cutscene camera"; scene.camera=cam; cam.data.lens=52; cam.data.clip_start=0.1; cam.data.clip_end=250
    cam.data.dof.use_dof=False; cam.data.dof.aperture_fstop=5.6
    def camera_shot(frame, location, target):
        cam.location=location
        cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
        cam.keyframe_insert(data_path="location",frame=frame)
        cam.keyframe_insert(data_path="rotation_euler",frame=frame)
    # Four composed vertical shots: tracking approach, impact/exit, over-shoulder walk, moon reveal.
    camera_shot(1,(0,-25,6),(0,-13,1.25))
    camera_shot(27,(0,-12,5.4),(0,0,1.25))
    camera_shot(33,(0,-12,5.4),(0,0,1.25))
    camera_shot(34,(0,-9.0,5.1),(1.0,0.0,1.2))
    camera_shot(68,(0,-7.5,4.8),(2.4,1.2,1.2))
    camera_shot(69,(0,-3.5,5.2),(2.8,1.8,1.2))
    camera_shot(145,(0,2.5,5.6),(4.2,8.2,1.3))
    camera_shot(146,(0,10,8),(-1,16,17))
    camera_shot(180,(0,10,8),(-1,16,17))
    # Camera gate: sample every authored cut/track key and reject out-of-frame targets.
    from bpy_extras.object_utils import world_to_camera_view
    framing_targets=[
        (1,(0,-13,1.25)),(27,(0,0,1.25)),(33,(0,0,1.25)),
        (34,(1.0,0.0,1.2)),(68,(2.4,1.2,1.2)),(69,(2.8,1.8,1.2)),
        (145,(4.2,8.2,1.3)),(146,(-1,16,17)),(180,(-1,16,17))
    ]
    camera_report=[]
    for sample_frame,target in framing_targets:
        scene.frame_set(sample_frame)
        bpy.context.view_layer.update()
        projected=world_to_camera_view(scene,cam,Vector(target))
        inside=(0.06<=projected.x<=0.94 and 0.06<=projected.y<=0.94 and projected.z>0)
        camera_report.append({"frame":sample_frame,"x":round(projected.x,3),"y":round(projected.y,3),"depth":round(projected.z,3),"inside":inside})
        if not inside:
            raise RuntimeError("Camera framing validation failed at frame "+str(sample_frame)+": "+str(camera_report[-1]))
    # Sample every authored shot segment, not just its endpoints, and check camera near-plane clearance.
    target_keys=[(1,(0,-13,1.25)),(27,(0,0,1.25)),(33,(0,0,1.25)),(34,(1.0,0.0,1.2)),(68,(2.4,1.2,1.2)),(69,(2.8,1.8,1.2)),(145,(4.2,8.2,1.3)),(146,(-1,16,17)),(180,(-1,16,17))]
    depsgraph=bpy.context.evaluated_depsgraph_get()
    for (fa,ta),(fb,tb) in zip(target_keys,target_keys[1:]):
        for sample_frame in range(fa,fb+1,3):
            scene.frame_set(sample_frame); bpy.context.view_layer.update()
            t=(sample_frame-fa)/max(1,fb-fa)
            target=Vector(ta).lerp(Vector(tb),t)
            projected=world_to_camera_view(scene,cam,target)
            if not (0.025<=projected.x<=0.975 and 0.025<=projected.y<=0.975 and projected.z>0):
                raise RuntimeError("Intermediate camera framing failed at frame "+str(sample_frame)+": "+str((round(projected.x,3),round(projected.y,3),round(projected.z,3))))
            # Test the actual camera near-plane footprint, not an arbitrary 16cm center-ray bubble.
            # The previous 0.16m ray falsely rejected trees that were close to, but safely beyond,
            # the 0.10m camera clip plane. Sample center + four near-plane corners against geometry.
            camera_origin=cam.matrix_world.translation
            near_clip=max(float(cam.data.clip_start),0.01)
            local_frame=cam.data.view_frame(scene=scene)
            near_samples=[Vector((0.0,0.0,-near_clip))]
            for corner in local_frame:
                direction=Vector((corner.x,corner.y,corner.z))
                if direction.length>0:
                    near_samples.append(direction.normalized()*near_clip)
            obstruction=None
            for near_point in near_samples:
                direction=(cam.matrix_world.to_3x3() @ near_point).normalized()
                hit,hit_location,_,_,hit_obj,_=scene.ray_cast(
                    depsgraph,camera_origin,direction,distance=near_clip*1.02
                )
                if hit and hit_obj and "fog" not in hit_obj.name.lower():
                    obstruction=hit_obj
                    break
            if obstruction:
                raise RuntimeError(
                    "Camera near-plane obstruction at frame "+str(sample_frame)+
                    " by "+obstruction.name+" (within "+str(round(near_clip,3))+"m clip plane)"
                )
    scene["ORNI_Camera_Frames_Validated"]=True
    scene["ORNI_Camera_Validation_Report"]=json.dumps(camera_report)
    scene["ORNI_Texture_Provenance"]="Poly Haven CC0 photographic diffuse maps; 64px; 5-bit/channel Bayer dither; nearest-neighbour"
    scene["ORNI_Model_Provenance"]="GGBotNet PSX Style Cars; OpenGameArt; CC0; https://opengameart.org/content/psx-style-cars"
    scene["ORNI_Forest_Model_Provenance"]="methodical pixel; OpenGameArt; CC0; https://opengameart.org/content/tree-and-plants-low-poly-3d-models"
    scene["ORNI_Asset_License"]="CC0 1.0 Universal for imported vehicle, forest models and Poly Haven photo textures"
    for obj in scene.objects:
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation=("LINEAR" if int(round(kp.co.x)) in (1,34,69,146) else "CONSTANT") if obj==cam else "LINEAR"
    # UV unwrap all scene meshes and apply packed pixel-grain maps with nearest sampling.
    set_job_status(stage="UV unwrapping and texture validation",progress=32)
    uv_mesh_count=unwrap_scene_meshes()
    scene.render.image_settings.file_format="PNG"
    preview_dir=OUT/"orni_crash_woods_shot_previews"
    if preview_dir.exists(): shutil.rmtree(preview_dir,ignore_errors=True)
    preview_dir.mkdir(parents=True,exist_ok=True)
    set_job_status(stage="Rendering four-shot contact sheet",progress=36)
    preview_frames=(14,50,100,165)
    for index,preview_frame in enumerate(preview_frames,1):
        scene.frame_set(preview_frame)
        scene.render.filepath=str(preview_dir/("shot_%02d.png"%index))
        bpy.ops.render.render(write_still=True)
    preview_file=OUT/"orni_crash_woods_preview.png"
    try:
        subprocess.run([
            "ffmpeg","-y","-i",str(preview_dir/"shot_01.png"),"-i",str(preview_dir/"shot_02.png"),
            "-i",str(preview_dir/"shot_03.png"),"-i",str(preview_dir/"shot_04.png"),
            "-filter_complex",
            "[0:v]scale=360:640:flags=neighbor[a];[1:v]scale=360:640:flags=neighbor[b];[2:v]scale=360:640:flags=neighbor[c];[3:v]scale=360:640:flags=neighbor[d];[a][b][c][d]xstack=inputs=4:layout=0_0|360_0|0_640|360_640[out]",
            "-map","[out]","-frames:v","1",str(preview_file)
        ],check=True,capture_output=True,text=True,timeout=60)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("Four-shot contact sheet generation failed: "+(exc.stderr or "unknown error")[-900:])
    finally:
        shutil.rmtree(preview_dir,ignore_errors=True)
    set_job_status(stage="Saving editable Blender project",progress=40)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"orni_crash_woods.blend"))
    frames_dir=OUT/"orni_crash_woods_frames"
    if frames_dir.exists(): shutil.rmtree(frames_dir,ignore_errors=True)
    frames_dir.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(frames_dir/"frame_")
    set_job_status(stage="Rendering animation frames",progress=42,frame=0,frames=scene.frame_end)
    bpy.ops.render.render(animation=True)
    video_file=OUT/"orni_crash_woods_15s.mp4"
    set_job_status(stage="Encoding PSX film with FFmpeg",progress=92)
    try:
        subprocess.run(["ffmpeg","-y","-framerate","12","-i",str(frames_dir/"frame_%04d.png"),"-vf","scale=iw*3:ih*3:flags=neighbor","-c:v","libx264","-pix_fmt","yuv420p","-crf","20","-preset","ultrafast","-movflags","+faststart",str(video_file)],check=True,capture_output=True,text=True,timeout=480)
    except FileNotFoundError: raise RuntimeError("FFmpeg is not installed in the Blender worker.")
    except subprocess.CalledProcessError as exc: raise RuntimeError("FFmpeg encoding failed: "+(exc.stderr or "unknown error")[-1200:])
    finally: shutil.rmtree(frames_dir,ignore_errors=True)
    if not video_file.is_file() or video_file.stat().st_size<1024: raise RuntimeError("Rebuilt crash-woods MP4 was not created.")
    probe=subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height,r_frame_rate","-show_entries","format=duration","-of","json",str(video_file)],check=True,capture_output=True,text=True,timeout=30)
    probe_data=json.loads(probe.stdout); stream=(probe_data.get("streams") or [{}])[0]
    duration=float((probe_data.get("format") or {}).get("duration",0))
    if (stream.get("width"),stream.get("height"))!=(540,960): raise RuntimeError("MP4 dimensions failed validation.")
    if stream.get("r_frame_rate")!="12/1" or not 14.5<=duration<=15.5: raise RuntimeError("MP4 frame rate or duration failed validation.")
    subprocess.run(["ffmpeg","-v","error","-i",str(video_file),"-f","null","-"],check=True,capture_output=True,text=True,timeout=180)
    set_job_status(stage="Validating deliverables",progress=98)
    if not (OUT/"orni_crash_woods.blend").is_file() or not (OUT/"orni_crash_woods_preview.png").is_file():
        raise RuntimeError("Required Blender project or style-frame preview is missing.")
    return {"ok":True,"scene":"ORNI rebuilt PS1/PS2 crash-woods short","style":"authored-psx-cutscene","blend":"/outputs/orni_crash_woods.blend","preview":"/outputs/orni_crash_woods_preview.png","video":"/outputs/orni_crash_woods_15s.mp4","frames":180,"fps":12,"durationSeconds":15,"resolutionX":540,"resolutionY":960,"sourceResolution":"180x320","aspectRatio":"9:16","uvMappedMeshes":uv_mesh_count,"textureResolution":"64x64 photo-derived CC0 maps with 5-bit Bayer dithering and nearest-neighbour sampling","cameraShots":4,"cameraContactSheet":true,"cameraFramingValidated":true,"externalVehicleAsset":"OpenGameArt PSX Style Cars by GGBotNet (CC0)","textureSources":["Poly Haven Asphalt 01","Poly Haven Pine Bark","Poly Haven Forest Ground 04","Poly Haven Forest Leaves 04","Poly Haven Rusty Painted Metal","Poly Haven Polystyrene","Poly Haven Rubber Tiles","Poly Haven Metal Plate"],"forestModelSource":"OpenGameArt Tree and plants low poly 3d models by methodical pixel (CC0)","forestModelSourceURL":"https://opengameart.org/content/tree-and-plants-low-poly-3d-models","assetAttribution":"Powered by Poly Haven API; CC0 assets. Vehicle: GGBotNet/OpenGameArt CC0. Forest models: methodical pixel/OpenGameArt CC0.","decodeValidated":True,"note":"Imported CC0 PSX vehicle, custom low-poly forest and articulated crash dummy, real CC0 photo-derived texture maps, four-shot vertical contact sheet, camera framing validation and 9:16 master. Technical validation is not human playback approval."}

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
    arms=[]
    for side in (-1,1):
        arm=cube("Retro protagonist | sleeve",(side*0.72,0,1.62),(0.42,0.48,1.05),mats["blue"],0.02)
        arm.rotation_euler[1]=side*0.12
        arms.append((side,arm))
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
    # PS1 gets a smooth game-camera push. PS2 gets five deliberate cutscene framings.
    if ps1:
        cam.location=(4.2,-7.8,3.35); cam.keyframe_insert(data_path="location",frame=1)
        cam.location=(3.35,-6.6,3.0); cam.keyframe_insert(data_path="location",frame=scene.frame_end)
    else:
        shots=[
            (1,(4.2,-7.8,3.35),(0,0.9,1.65)),
            (max(2,int(scene.frame_end*0.24)),(2.7,-6.1,2.95),(0,0,2.0)),
            (max(3,int(scene.frame_end*0.48)),(0.9,-4.3,2.55),(0,0,2.45)),
            (max(4,int(scene.frame_end*0.74)),(2.2,-5.2,2.8),(0,0,1.9)),
            (scene.frame_end,(1.15,-4.5,2.5),(0,0,2.45))
        ]
        for frame,location,look_at in shots:
            cam.location=location
            cam.rotation_euler=(Vector(look_at)-cam.location).to_track_quat("-Z","Y").to_euler()
            cam.keyframe_insert(data_path="location",frame=frame)
            cam.keyframe_insert(data_path="rotation_euler",frame=frame)
        for frame in range(1,scene.frame_end+1,4):
            mouth.scale=(1,1,0.25 if (frame//4)%2 else 1.0)
            mouth.keyframe_insert(data_path="scale",frame=frame)
        # Shoulder-pivoted gestures, head nods and deliberate deadpan holds.
        for side,arm in arms:
            bpy.ops.object.select_all(action="DESELECT")
            arm.select_set(True)
            bpy.context.view_layer.objects.active=arm
            bpy.context.scene.cursor.location=Vector((side*0.52,0,2.10))
            bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
            gesture_keys=[
                (1,0.0),
                (max(2,int(scene.frame_end*0.16)),0.32 if side<0 else -0.32),
                (max(3,int(scene.frame_end*0.34)),-0.22 if side<0 else 0.22),
                (max(4,int(scene.frame_end*0.52)),0.48 if side<0 else -0.48),
                (max(5,int(scene.frame_end*0.70)),-0.12 if side<0 else 0.12),
                (scene.frame_end,0.0)
            ]
            for frame,angle in gesture_keys:
                arm.rotation_euler[0]=angle
                arm.keyframe_insert(data_path="rotation_euler",frame=frame)
        for frame,angle in [(1,0.0),(max(2,int(scene.frame_end*0.18)),0.10),(max(3,int(scene.frame_end*0.42)),-0.08),(max(4,int(scene.frame_end*0.70)),0.13),(scene.frame_end,0.0)]:
            head.rotation_euler[0]=angle
            head.keyframe_insert(data_path="rotation_euler",frame=frame)
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
    if ps1:
        for index,(key,color) in enumerate(palette.items()):
            apply_psx_pixel_texture(mats[key],color,"PS1 "+key,index)
    set_job_status(stage="UV unwrapping retro character and environment",progress=16)
    retro_uv_mesh_count=unwrap_scene_meshes()
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
    probe=subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height,r_frame_rate","-show_entries","format=duration","-of","json",str(video_file)],check=True,capture_output=True,text=True,timeout=30)
    probe_data=json.loads(probe.stdout)
    stream=(probe_data.get("streams") or [{}])[0]
    duration_probe=float((probe_data.get("format") or {}).get("duration",0))
    if (stream.get("width"),stream.get("height"))!=(base_width*3,base_height*3) or stream.get("r_frame_rate")!="12/1":
        raise RuntimeError("Retro MP4 dimensions or frame rate failed validation.")
    if not duration-0.5<=duration_probe<=duration+0.5:
        raise RuntimeError("Retro MP4 duration failed validation.")
    subprocess.run(["ffmpeg","-v","error","-i",str(video_file),"-f","null","-"],check=True,capture_output=True,text=True,timeout=180)
    return {"ok":True,"scene":"ORNI "+("PS1 low-poly" if ps1 else "PS2 cutscene")+" retro cinema","style":style,"blend":"/outputs/orni_retro_cinema.blend","preview":"/outputs/orni_retro_preview.png","video":"/outputs/orni_retro_cinema.mp4","frames":scene.frame_end,"fps":12,"durationSeconds":duration,"resolutionX":base_width*3,"resolutionY":base_height*3,"sourceResolutionX":base_width,"sourceResolutionY":base_height,"aspectRatio":aspect_ratio,"uvMappedMeshes":retro_uv_mesh_count,"decodeValidated":True,"note":"Procedural proof-of-pipeline scene with UV-mapped meshes and validated MP4 metadata/full decode. Replace placeholder character and set with approved CELVANI assets for campaigns. PS2 includes five-shot framing, mouth timing and shoulder-pivoted gestures; it still has no generated voice or audio."}


JOBS=queue.Queue()
JOB_LOCK=threading.Lock()
JOB_STATUS={"status":"idle","stage":"Waiting for a production brief","progress":0,"frame":0,"frames":0,"error":None,"result":None,"updatedAt":time.time()}

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
        set_job_status(status="failed",stage="Production failed",error=str(e),progress=0,result=job["result"])
    finally:
        if job["result"] and job["result"].get("ok"):
            set_job_status(status="complete",stage="Files validated · human review pending",progress=100,error=None,result=job["result"])
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
        with JOB_LOCK:
            if JOB_STATUS.get("status") in ("queued","running"):
                return self.reply(409,{"error":"A Blender job is already running. Wait for it to finish before starting another."})
            JOB_STATUS.update(status="queued",stage="Waiting for Blender render slot",progress=0,frame=0,frames=0,error=None,result=None,updatedAt=time.time())
        job={"action":action,"style":body.get("style","ps1") if isinstance(body,dict) else "ps1","duration":body.get("duration",5) if isinstance(body,dict) else 5,"aspect_ratio":body.get("aspectRatio","16:9") if isinstance(body,dict) else "16:9","caption":str(body.get("caption",""))[:120] if isinstance(body,dict) else "","done":threading.Event(),"result":None}
        JOBS.put(job)
        # Accept immediately. Blender renders in its timer-driven queue while
        # the threaded HTTP server remains free for progress and health requests.
        return self.reply(202,{"ok":True,"accepted":True,"status":"queued","message":"Blender job accepted; poll /job-status for progress."})
    def log_message(self,*args): pass

def serve():
    ThreadingHTTPServer(("0.0.0.0",8765),Handler).serve_forever()
threading.Thread(target=serve,daemon=True).start()
print("ORNI Blender control API listening on 8765")
