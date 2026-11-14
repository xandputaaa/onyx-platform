"""COZO rigged proof-of-concept for Blender 4.x, with walk/stand/sit actions.
Procedural blockout only: NOT the approved final production mesh.
Usage: blender -b --python cozo_rig.py -- /tmp/cozo_rig.blend
"""
import bpy, math, sys
from mathutils import Vector

def action_curves(obj):
    """Support legacy and Blender 4.4+/5 layered Actions."""
    action = getattr(getattr(obj, "animation_data", None), "action", None)
    if action is None:
        return []
    curves = list(getattr(action, "fcurves", []) or [])
    if curves:
        return curves
    for layer in getattr(action, "layers", []):
        for strip in getattr(layer, "strips", []):
            for bag in getattr(strip, "channelbags", []):
                curves.extend(getattr(bag, "fcurves", []))
    return curves

def material(name, rgb):
    m=bpy.data.materials.new(name); m.diffuse_color=(*rgb,1); m.use_nodes=True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(*rgb,1)
    return m

def part(name, location, scale, mat, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    obj=bpy.context.object; obj.name=name
    obj.dimensions=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat)
    # Beveled, weighted edges preserve PS2 facets without raw cuboid silhouettes.
    if name not in ("HIPS",):
        bevel=obj.modifiers.new("Soft garment edge","BEVEL")
        bevel.width=min(scale)*.16
        bevel.segments=2
        obj.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    if parent:
        obj.parent=parent; obj.location=location
    return obj

def garment_tube(name, loc, levels, mat, parent=None, sides=12, seed=0):
    """Connected, faceted cloth volume with irregular silhouette and fold ridges.
    levels: (local_z, radius_x, radius_y); mesh is in parent's local space.
    """
    verts=[]; faces=[]
    for k,(z,rx,ry) in enumerate(levels):
        for j in range(sides):
            a=2*math.pi*j/sides
            ripple=1+.035*math.sin(j*2.1+k*1.8+seed)+.025*math.sin(j*4.0-k*2.2)
            verts.append((rx*math.cos(a)*ripple,ry*math.sin(a)*ripple,z))
    for k in range(len(levels)-1):
        for j in range(sides):
            n=k*sides+j; q=k*sides+(j+1)%sides
            faces.append((n,q,q+sides,n+sides))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple((len(levels)-1)*sides+j for j in range(sides)))
    mesh=bpy.data.meshes.new(name+" | connected garment topology")
    mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    if parent: obj.parent=parent
    obj.location=loc
    return obj

def animate(obj, frames, field="rotation_euler", index=0):
    for frame,value in frames:
        getattr(obj,field)[index]=value
        obj.keyframe_insert(data_path=field,index=index,frame=frame)
    if obj.animation_data and obj.animation_data.action:
        for curve in action_curves(obj):
            for point in curve.keyframe_points: point.interpolation="BEZIER"

def build():
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    gray=material("COZO | pale matte faceted gray",(0.59,0.60,0.62))
    black=material("CELVANI | quilted charcoal black",(0.017,0.019,0.022))
    denim=material("CELVANI | washed light blue denim",(0.42,0.52,0.62))
    boot=material("COZO | matte black lug boot",(0.025,0.026,0.029))
    eye=material("COZO | black recessed eyes",(0.002,0.002,0.003))
    # Subtle procedural fabric breakup avoids flat plastic color.
    for fabric, scale, strength in ((black,85,0.11),(denim,38,0.17)):
        nodes=fabric.node_tree.nodes
        tex=nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value=scale
        bump=nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value=strength
        bump.inputs["Distance"].default_value=.012
        fabric.node_tree.links.new(tex.outputs["Fac"],bump.inputs["Height"])
        fabric.node_tree.links.new(bump.outputs["Normal"],nodes["Principled BSDF"].inputs["Normal"])
        nodes["Principled BSDF"].inputs["Roughness"].default_value=.88
    root=bpy.data.objects.new("COZO_ROOT | motion controller",None); bpy.context.collection.objects.link(root)
    root.empty_display_type="ARROWS"
    hips=part("HIPS", (0,0,1.05),(.56,.35,.26),denim,root)
    torso=garment_tube("CELVANI PUFFER | torso",(0,0,0),[(1.38,.46,.29),(1.48,.51,.34),(1.65,.53,.36),(1.84,.56,.38),(2.04,.55,.38),(2.23,.49,.33),(2.31,.34,.25)],black,root,sides=16,seed=7)
    # Connected ring-topology face, replacing the former UV sphere.
    # Face looks toward negative Y. Front surface contains two indented eye
    # cavities as real vertices, rather than two floating white eyeballs.
    rings=14; segments=24
    vertices=[]; faces=[]
    for r in range(rings):
        t=r/(rings-1)
        z=2.29+.59*t
        width=.09+.205*math.sin(math.pi*(t**.79))**.72
        depth=.11+.115*math.sin(math.pi*t)**.65
        for j in range(segments):
            a=2*math.pi*j/segments
            x=width*math.cos(a)
            y=-.025-depth*math.sin(a)
            # Carve socket depressions directly into forward face surface.
            for cx in (-.115,.115):
                dx=(x-cx)/.074
                dz=(z-2.62)/.091
                front=max(0,math.sin(a))
                y+=.042*math.exp(-2*(dx*dx+dz*dz))*front
            # Midline nose bridge is a subtle, sharp angular projection.
            y-=.025*math.exp(-((x/.045)**2+((z-2.52)/.20)**2))*max(0,math.sin(a))
            vertices.append((x,y,z))
    for r in range(rings-1):
        for j in range(segments):
            a=r*segments+j
            b=r*segments+(j+1)%segments
            faces.append((a,b,b+segments,a+segments))
    faces.extend([tuple(reversed(tuple(range(segments)))),tuple((rings-1)*segments+j for j in range(segments))])
    mesh=bpy.data.meshes.new("COZO | integrated mask topology")
    mesh.from_pydata(vertices,[],faces);mesh.update()
    head=bpy.data.objects.new("COZO | faceted matte gray mask blockout",mesh)
    bpy.context.collection.objects.link(head)
    head.data.materials.append(gray)
    head.parent=root
    # Recognizable COZO head emblem: flat four-quadrant crash-test disc.
    # This is a geometry approximation pending the approved UV-textured head.
    yellow=material("COZO | crash target amber yellow",(0.79,0.61,0.06))
    for q in range(4):
        a=q*math.pi/2
        center=(.248,-.02,2.61)
        radius=.095
        verts=[center]
        for step in range(9):
            theta=a+(math.pi/2)*step/8
            verts.append((center[0],center[1]+radius*math.cos(theta),center[2]+radius*math.sin(theta)))
        mesh=bpy.data.meshes.new("COZO emblem wedge mesh %d"%q)
        mesh.from_pydata(verts,[],[tuple(range(10))]); mesh.update()
        emblem=bpy.data.objects.new("COZO | temple crash-test quadrant %d"%q,mesh)
        bpy.context.collection.objects.link(emblem)
        emblem.data.materials.append(black if q%2==0 else yellow)
        emblem.parent=root
    # PS2-style mottled low-resolution material color, not glossy plastic.
    for fabric,scale,detail in ((gray,19,2),(black,24,3),(denim,16,4)):
        nt=fabric.node_tree
        bsdf=nt.nodes.get("Principled BSDF")
        noise=nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value=scale
        noise.inputs["Detail"].default_value=detail
        ramp=nt.nodes.new("ShaderNodeValToRGB")
        if fabric==gray:
            ramp.color_ramp.elements[0].color=(.34,.34,.35,1)
            ramp.color_ramp.elements[1].color=(.66,.65,.66,1)
        elif fabric==denim:
            ramp.color_ramp.elements[0].color=(.24,.31,.39,1)
            ramp.color_ramp.elements[1].color=(.60,.67,.70,1)
        else:
            ramp.color_ramp.elements[0].color=(.009,.010,.013,1)
            ramp.color_ramp.elements[1].color=(.045,.047,.052,1)
        nt.links.new(noise.outputs["Fac"],ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"],bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value=.94
    # Puffer seam strips establish a repeatable garment silhouette.
    seam=material("CELVANI | puffer seam",(0.035,0.037,0.04))
    for i in range(5):
        z=1.47+i*.155
        # Quilted front volume, not painted stripes.
        part("CELVANI | quilted front panel %d"%i,(0,-.29,z),(.96,.18,.135),black,root)
        part("CELVANI | horizontal stitch %d"%i,(0,-.391,z+.071),(.93,.009,.008),seam,root)
    # Raised collar/hood rim around COZO's neck.
    for side in (-1,1):
        part("CELVANI | hood shoulder rim %s"%side,(side*.32,-.045,2.30),(.32,.38,.25),black,root)
    part("CELVANI | collar under chin",(0,-.25,2.25),(.52,.22,.18),black,root)
    # Low-poly silhouette is intentionally a blockout, not a final likeness.
    # Dark oval sockets embedded in the faceted face, rather than rectangular cubes.
    for side in (-1,1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,
                                             location=(side*.115,-.175,2.60))
        socket=bpy.context.object
        socket.name="COZO | recessed oval eye %s"%side
        socket.scale=(.052,.014,.070)
        socket.data.materials.append(eye)
        socket.parent=root
        socket.location=(side*.115,-.175,2.60)
    # Chin is now part of the connected mask mesh. A non-rendering locator
    # retains compatibility with the original scene validation contract.
    chin=bpy.data.objects.new("COZO | tapered mask chin",None)
    bpy.context.collection.objects.link(chin)
    chin.parent=root;chin.location=(0,-.09,2.31)
    limbs={}
    for side,label in [(-1,"L"),(1,"R")]:
        arm_pivot=bpy.data.objects.new(label+"_SHOULDER",None); bpy.context.collection.objects.link(arm_pivot)
        arm_pivot.parent=root; arm_pivot.location=(side*.57,0,2.08)
        garment_tube(label+" | puffer sleeve",(side*.04,0,0),[(-.77,.17,.20),(-.62,.22,.24),(-.45,.24,.26),(-.26,.25,.27),(-.08,.22,.25),(.04,.19,.22)],black,arm_pivot,seed=1 if side<0 else 2)
        for band in range(3):
            part(label+" | sleeve quilt %d"%band,(side*.04,-.246,-.18-band*.21),(.38,.035,.015),seam,arm_pivot)
        palm=garment_tube(label+" | articulated palm",(side*.04,0,-.82),[(-.12,.082,.065),(.03,.094,.075),(.10,.080,.064)],gray,arm_pivot,sides=8)
        for finger in range(5):
            fx=side*.04+(finger-2)*.036
            fy=-.018 if finger==0 else 0
            length=.115 if finger in (0,4) else .16
            digit=garment_tube(label+" | finger %d"%finger,(fx,fy,-.94),[(-length,.013,.016),(-length*.5,.017,.018),(0,.019,.020)],gray,arm_pivot,sides=6,seed=finger)
        leg_pivot=bpy.data.objects.new(label+"_HIP",None); bpy.context.collection.objects.link(leg_pivot)
        leg_pivot.parent=root; leg_pivot.location=(side*.23,0,1.02)
        garment_tube(label+" | wide denim",(0,0,0),[(-.90,.31,.30),(-.83,.33,.32),(-.73,.31,.32),(-.61,.30,.29),(-.48,.32,.30),(-.35,.30,.31),(-.20,.28,.29),(-.06,.27,.27),(.04,.26,.25)],denim,leg_pivot,seed=3 if side<0 else 4)
        part(label+" | denim cuff",(0,-.012,-.82),(.54,.54,.12),denim,leg_pivot)
        part(label+" | boot",(0,-.08,-.88),(.37,.61,.23),boot,leg_pivot)
        limbs[label]=(arm_pivot,leg_pivot)
    # Frames 1–45: seated pose; 46–90: stand; 91–180: walk.\n    # Parent local coordinates are explicit to keep limbs aligned to pivots.
    animate(root,[(1,-.40),(84,-.40),(132,0),(180,0)],"location",2)
    for label,(arm,leg) in limbs.items():
        sign=1 if label=="L" else -1
        animate(leg,[(1,-1.0),(84,-1.0),(132,0),(133,0),(143,sign*.34),(153,0),(163,-sign*.34),(180,0)])
        animate(arm,[(1,-.12),(84,-.12),(132,0),(133,0),(143,-sign*.20),(153,0),(163,sign*.20),(180,0)])
    animate(root,[(1,0),(132,0),(133,0),(168,3.8),(180,3.8)],"location",1)
    scene=bpy.context.scene; scene.frame_start=1; scene.frame_end=180; scene.render.fps=12
    scene.render.resolution_x=720; scene.render.resolution_y=1280; scene.render.resolution_percentage=100
    # Reference camera and light for visual inspection, not a finished boutique scene.
    bpy.ops.object.camera_add(location=(4,-8,3.2))
    cam=bpy.context.object
    direction=Vector((0,0,1.45))-cam.location
    cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    scene.camera=cam
    bpy.ops.object.light_add(type="AREA",location=(1,-3,5))
    bpy.context.object.data.energy=650; bpy.context.object.data.shape="DISK"; bpy.context.object.data.size=5
    return root

if __name__=="__main__":
    build()
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    output=args[0] if args else "/tmp/cozo_rig.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output)
    print("COZO rig proof of concept saved:",output)
