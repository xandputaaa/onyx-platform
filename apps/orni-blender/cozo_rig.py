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
    torso=part("CELVANI PUFFER | torso",(0,0,1.82),(.98,.55,.88),black,root)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,location=(0,-.02,2.55))
    head=bpy.context.object
    head.name="COZO | faceted matte gray mask blockout"
    head.scale=(.27,.225,.36)
    head.data.materials.append(gray)
    head.parent=root
    head.location=(0,-.02,2.55)
    # Recognizable COZO head emblem: flat four-quadrant crash-test disc.
    # This is a geometry approximation pending the approved UV-textured head.
    white=material("COZO | emblem off-white",(0.78,0.78,0.75))
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
        emblem.data.materials.append(black if q%2==0 else white)
        emblem.parent=root
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
                                             location=(side*.115,-.235,2.60))
        socket=bpy.context.object
        socket.name="COZO | recessed oval eye %s"%side
        socket.scale=(.065,.035,.083)
        socket.data.materials.append(eye)
        socket.parent=root
        socket.location=(side*.115,-.235,2.60)
    # Tapered chin plane is a deliberately simple mesh, to be replaced by a
    # sculpted production mask once the five-shot render is visually checked.
    bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=.115,radius2=.22,
                                    depth=.19,location=(0,-.075,2.27))
    chin=bpy.context.object
    chin.name="COZO | tapered mask chin"
    chin.data.materials.append(gray)
    chin.parent=root
    chin.location=(0,-.075,2.27)
    limbs={}
    for side,label in [(-1,"L"),(1,"R")]:
        arm_pivot=bpy.data.objects.new(label+"_SHOULDER",None); bpy.context.collection.objects.link(arm_pivot)
        arm_pivot.parent=root; arm_pivot.location=(side*.57,0,2.08)
        part(label+" | puffer sleeve",(side*.04,0,-.37),(.40,.47,.79),black,arm_pivot)
        for band in range(3):
            part(label+" | sleeve quilt %d"%band,(side*.04,-.246,-.18-band*.21),(.38,.035,.015),seam,arm_pivot)
        part(label+" | gray hand",(side*.04,0,-.82),(.19,.19,.23),gray,arm_pivot)
        leg_pivot=bpy.data.objects.new(label+"_HIP",None); bpy.context.collection.objects.link(leg_pivot)
        leg_pivot.parent=root; leg_pivot.location=(side*.23,0,1.02)
        part(label+" | wide denim",(0,0,-.43),(.52,.51,.88),denim,leg_pivot)
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
