import bpy, json, os, threading, queue, subprocess, shutil, math, time
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
    """Rebuilt PS1/PS2 crash-woods short with authored geometry, grunge maps and edited shots."""
    import random
    set_job_status(stage="Rebuilding custom PSX assets",progress=4)
    clear_scene()
    scene=bpy.context.scene
    set_compatible_eevee(scene)
    scene.render.resolution_x=320; scene.render.resolution_y=180
    scene.render.resolution_percentage=100; scene.render.fps=12
    scene.frame_start=1; scene.frame_end=180
    scene.world.color=(0.008,0.012,0.026)
    scene.view_settings.view_transform="Standard"
    scene.view_settings.look="Medium High Contrast"
    if hasattr(scene.view_settings,"dither_intensity"): scene.view_settings.dither_intensity=0.35
    random.seed(27)

    def textured_mat(name, base, rough=0.9, seed=1, metallic=0.0):
        m=mat(name,base,metallic,rough)
        image=bpy.data.images.new(name+" | authored 64px grunge",width=64,height=64,alpha=False)
        pixels=[]
        for y in range(64):
            for x in range(64):
                n=((x*37+y*19+seed*53+(x*y*7))%31)/100.0
                grain=0.78+n
                seam=0.58 if ((x+seed*3)%17 in (0,1) or (y+seed)%23==0) else 1.0
                fleck=1.22 if ((x*13+y*29+seed)%47)<3 else 1.0
                shade=max(0.25,min(1.35,grain*seam*fleck))
                pixels.extend((min(1,base[0]*shade),min(1,base[1]*shade),min(1,base[2]*shade),1))
        image.pixels.foreach_set(pixels); image.pack()
        nodes=m.node_tree.nodes; shader=nodes.get("Principled BSDF")
        tex=nodes.new("ShaderNodeTexImage"); tex.name=name+" | pixel-grain atlas"
        tex.image=image; tex.interpolation="Closest"; tex.extension="REPEAT"
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
                q=point+radius*(math.cos(angle)*u+math.sin(angle)*v)
                verts.append(tuple(q))
        faces=[]
        for i in range(sides):
            j=(i+1)%sides
            faces.append((i,j,sides+j,sides+i))
        faces.extend([tuple(range(sides-1,-1,-1)),tuple(range(sides,2*sides))])
        return mesh_obj(name,verts,faces,material)

    def parent_local(obj, root):
        obj.parent=root
        obj.matrix_parent_inverse=Matrix.Identity(4)
        return obj

    road=textured_mat("Wet asphalt | charcoal tar, cracks and grit",(0.035,0.045,0.06),0.98,4)
    soil=textured_mat("Forest loam | leaf litter and mud",(0.07,0.085,0.055),1,7)
    bark=textured_mat("Bark | rough striped cedar",(0.20,0.105,0.055),1,11)
    foliage=textured_mat("Pine | mottled midnight needles",(0.035,0.12,0.075),1,14)
    paint=textured_mat("Car paint | oxidized burgundy enamel",(0.34,0.055,0.045),0.72,18,0.12)
    glass=textured_mat("Glass | smoky blue reflections",(0.035,0.12,0.17),0.3,22,0.25)
    tire=textured_mat("Tire rubber | dusty tread",(0.018,0.022,0.027),1,24)
    dummy_mat=textured_mat("Crash dummy | aged ivory composite",(0.72,0.69,0.58),0.82,29)
    joint_mat=textured_mat("Crash dummy | graphite joints",(0.09,0.105,0.12),0.75,32,0.1)
    metal=textured_mat("Road hardware | rusted steel",(0.16,0.18,0.19),0.7,35,0.45)
    warm=textured_mat("Headlamp | amber glass",(0.9,0.58,0.24),0.28,39)
    moon_mat=textured_mat("Moon | grainy bone-white",(0.78,0.79,0.72),0.8,43)

    set_job_status(stage="Building road, custom car and forest silhouettes",progress=12)
    box_mesh("Roadbed | beveled shoulder",(0,0,-0.34),(8,62,0.48),soil)
    box_mesh("Asphalt ribbon",(0,0,-0.07),(6.5,62,0.18),road)
    for x in (-3.25,3.25):
        box_mesh("Broken road edge", (x,0,0.01),(0.18,62,0.12),metal)
    # Distinctive trees: tapered trunks with irregular, tiered polygonal boughs.
    for side in (-1,1):
        for i in range(27):
            y=-28+i*2.1+random.uniform(-0.65,0.65)
            x=side*random.uniform(5.1,11.5)
            h=random.uniform(5.5,9.5)
            trunk=tapered_limb("Cedar trunk | faceted",(x,y,0),(x+random.uniform(-0.25,0.25),y,h*0.53),0.32,0.12,bark,7)
            for tier in range(3):
                z=h*(0.34+tier*0.19)
                radius=h*(0.27-tier*0.055)
                verts=[]
                for zz,rr in ((z-radius*0.55,radius),(z+radius*0.75,0.06)):
                    for k in range(7):
                        ang=2*math.pi*k/7+(tier%2)*0.18
                        verts.append((x+math.cos(ang)*rr,y+math.sin(ang)*rr,zz))
                faces=[(k,(k+1)%7,7+(k+1)%7,7+k) for k in range(7)]+[tuple(range(6,-1,-1)),tuple(range(7,14))]
                mesh_obj("Cedar bough tier | irregular low-poly",verts,faces,foliage)
    # One broad trunk and layered boughs form the impact obstacle.
    impact_x,impact_y=1.18,-1.8
    tapered_limb("Impact cedar | scarred trunk",(impact_x,impact_y,0),(impact_x-0.08,impact_y,4.3),0.48,0.25,bark,8)
    for tier in range(3):
        z=2.9+tier*0.85; radius=2.15-tier*0.35
        verts=[]
        for zz,rr in ((z-radius*0.55,radius),(z+radius*0.8,0.08)):
            for k in range(8):
                ang=2*math.pi*k/8+tier*0.2
                verts.append((impact_x+math.cos(ang)*rr,impact_y+math.sin(ang)*rr,zz))
        faces=[(k,(k+1)%8,8+(k+1)%8,8+k) for k in range(8)]+[tuple(range(7,-1,-1)),tuple(range(8,16))]
        mesh_obj("Impact cedar | sculpted canopy",verts,faces,foliage)

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
    car_root.location=(0,-13,0); car_root.keyframe_insert(data_path="location",frame=1)
    car_root.location=(0,0,0); car_root.keyframe_insert(data_path="location",frame=27)
    car_root.location=(0,0.65,0); car_root.keyframe_insert(data_path="location",frame=34)
    car_root.location=(0,0.65,0); car_root.keyframe_insert(data_path="location",frame=180)

    # Articulated crash dummy with tapered limbs, real pivots and a grouped root.
    dummy_root=bpy.data.objects.new("Crash dummy rig | pelvis root",None); scene.collection.objects.link(dummy_root)
    dummy_root.location=(0,-18.25,0)
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
        foot=dummy_piece(box_mesh("Dummy foot | broad planted sole",(side*0.24,-0.28,0.07),(0.28,0.48,0.13),joint_mat,0.025))
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

    # Dummy remains in the moving cabin through impact, then exits and walks away.
    dummy_root.location=(0,-18.25,0); dummy_root.keyframe_insert(data_path="location",frame=1)
    dummy_root.location=(0,-5.25,0); dummy_root.keyframe_insert(data_path="location",frame=27)
    dummy_root.location=(0,-4.60,0); dummy_root.keyframe_insert(data_path="location",frame=38)
    dummy_root.location=(1.85,-4.15,0); dummy_root.keyframe_insert(data_path="location",frame=55)
    dummy_root.location=(2.4,-2.7,0); dummy_root.keyframe_insert(data_path="location",frame=70)
    dummy_root.location=(3.2,0.2,0); dummy_root.keyframe_insert(data_path="location",frame=105)
    dummy_root.location=(4.2,4.2,0); dummy_root.keyframe_insert(data_path="location",frame=145)
    dummy_root.location=(4.4,4.8,0); dummy_root.keyframe_insert(data_path="location",frame=180)
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
    bpy.ops.object.camera_add(location=(8,-18,5))
    cam=bpy.context.object; cam.name="ORNI edited PS2 camera"; scene.camera=cam; cam.data.lens=48
    def camera_shot(frame, location, target):
        cam.location=location
        cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
        cam.keyframe_insert(data_path="location",frame=frame)
        cam.keyframe_insert(data_path="rotation_euler",frame=frame)
    # Four deliberate editorial shots: establish/impact, wreck/exit, walk, moon hold.
    camera_shot(1,(8,-18,5),(0,-8,1))
    camera_shot(34,(6,-10,3.2),(0,-4.4,1.2))
    camera_shot(35,(5,-9.5,3.1),(0,-4.3,1.2))
    camera_shot(68,(4.8,-7.4,2.8),(1.3,-3.8,1.2))
    camera_shot(69,(8,-2,3.8),(2.4,-2.7,1.2))
    camera_shot(145,(10,5,4.4),(4.2,4.2,1.3))
    camera_shot(146,(7,7,4.5),(3.5,4,1))
    camera_shot(180,(0,12,7),(-1,16,17))
    for obj in scene.objects:
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation="CONSTANT" if obj==cam else "LINEAR"
    # UV unwrap all scene meshes and apply packed pixel-grain maps with nearest sampling.
    set_job_status(stage="UV unwrapping and texture validation",progress=32)
    uv_mesh_count=unwrap_scene_meshes()
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(OUT/"orni_crash_woods_preview.png")
    scene.frame_set(35)
    set_job_status(stage="Rendering style-frame preview",progress=36)
    bpy.ops.render.render(write_still=True)
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
    if (stream.get("width"),stream.get("height"))!=(960,540): raise RuntimeError("MP4 dimensions failed validation.")
    if stream.get("r_frame_rate")!="12/1" or not 14.5<=duration<=15.5: raise RuntimeError("MP4 frame rate or duration failed validation.")
    subprocess.run(["ffmpeg","-v","error","-i",str(video_file),"-f","null","-"],check=True,capture_output=True,text=True,timeout=180)
    set_job_status(stage="Validating deliverables",progress=98)
    if not (OUT/"orni_crash_woods.blend").is_file() or not (OUT/"orni_crash_woods_preview.png").is_file():
        raise RuntimeError("Required Blender project or style-frame preview is missing.")
    return {"ok":True,"scene":"ORNI rebuilt PS1/PS2 crash-woods short","style":"authored-psx-cutscene","blend":"/outputs/orni_crash_woods.blend","preview":"/outputs/orni_crash_woods_preview.png","video":"/outputs/orni_crash_woods_15s.mp4","frames":180,"fps":12,"durationSeconds":15,"resolutionX":960,"resolutionY":540,"sourceResolution":"320x180","aspectRatio":"16:9","uvMappedMeshes":uv_mesh_count,"textureResolution":"64x64 authored grunge maps with nearest-neighbour sampling","cameraShots":4,"decodeValidated":True,"note":"Custom vehicle/forest geometry, authored low-resolution grunge maps, articulated crash dummy, staged door exit and four-shot camera edit. Technical validation is not human playback approval."}

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
