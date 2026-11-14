"""COZO Episode 001 Blender scene assembly. Uses the reusable COZO blockout.
Produces an editable boutique scene, not a final fully rendered episode.
"""
import bpy
import cozo_rig
from mathutils import Vector

def cube(name, loc, dims, mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    obj=bpy.context.object;obj.name=name;obj.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat)
    return obj

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

def build():
    root=cozo_rig.build()
    concrete=cozo_rig.material("CELVANI | cool concrete",(0.24,0.245,0.25))
    steel=cozo_rig.material("CELVANI | steel racks",(0.07,0.075,0.08))
    textile=cozo_rig.material("CELVANI | hanging black garments",(0.03,0.032,0.035))
    walnut=cozo_rig.material("CELVANI | interview table",(0.18,0.12,0.08))
    cube("Boutique concrete floor",(0,0,-.17),(12,12,.3),concrete)
    # Side wall wings leave the central aisle open to the storefront.
    cube("Boutique rear wall left",(-4.8,3.0,2.5),(2.4,.22,5),concrete)
    cube("Boutique rear wall right",(4.8,3.0,2.5),(2.4,.22,5),concrete)
    glass=cozo_rig.material("CELVANI | tinted storefront",(0.065,0.085,0.11))
    cube("Storefront left glass",(-2.3,4.3,2.15),(3.6,.045,4.2),glass)
    cube("Storefront right glass",(2.3,4.3,2.15),(3.6,.045,4.2),glass)
    cube("Storefront door mullion",(0,4.3,2.15),(.12,.10,4.2),steel)
    cube("Storefront lintel",(0,4.3,4.25),(8,.10,.12),steel)
    sign=bpy.data.curves.new("CELVANI sign text","FONT")
    sign.body="CELVANI"; sign.size=.56; sign.extrude=.005
    sign_obj=bpy.data.objects.new("CELVANI | wall sign",sign)
    bpy.context.scene.collection.objects.link(sign_obj)
    sign_obj.location=(-5.75,2.83,3.15)
    sign_obj.rotation_euler=(1.5708,0,0)
    cube("Interview table",(0,-2.0,.92),(2.5,1.2,.1),walnut)
    cube("Interview table left steel leg",(-1.03,-2.0,.47),(.075,.08,.87),steel)
    cube("Interview table right steel leg",(1.03,-2.0,.47),(.075,.08,.87),steel)
    # Long overhead architectural light bars visible in the cinematic reference.
    luminous=cozo_rig.material("CELVANI | overhead soft white",(0.85,0.87,0.89))
    for y in (-2.7,0.6,2.9):
        cube("Boutique suspended strip light %.1f"%y,(0,y,4.65),(3.5,.12,.055),luminous)
        bpy.ops.object.light_add(type="AREA",location=(0,y,4.5))
        light=bpy.context.object
        light.name="Boutique | softbox %.1f"%y
        light.data.energy=440
        light.data.shape="RECTANGLE"
        light.data.size=3.5
        light.data.size_y=.8
    # Night street silhouettes beyond the glass give the walkaway a destination.
    night=cozo_rig.material("Night street | charcoal",(0.018,.023,.038))
    cube("Exterior dark skyline",(0,6.0,2.1),(12,.18,4.2),night)
    for x in (-3.5,-1.8,1.9,3.3):
        cube("Exterior distant building %s"%x,(x,5.75,1.4),(.8,.12,2.8),steel)
    for side in (-1,1):
        x=side*3.1
        cube("Rack top %s"%side,(x,2.25,2.1),(1.9,.08,.08),steel)
        for offset in (-.7,-.35,0,.35,.7):
            cube("Garment %s %s"%(side,offset),(x+offset,2.25,1.72),(.24,.16,.65),textile)
    cube("Manager chair",(0,-3.55,.55),(.9,.8,.18),steel)
    cube("COZO chair",(0,.05,.55),(.9,.8,.18),steel)
    # Manager is an anonymous neutral mannequin stand-in.
    skin=cozo_rig.material("Manager | neutral warm gray",(0.45,0.39,0.35))
    cube("Manager torso",(0,-3.55,1.65),(.6,.36,.75),steel)
    cube("Manager head",(0,-3.55,2.25),(.35,.32,.43),skin)
    scene=bpy.context.scene
    cam=scene.camera
    cam.location=(3.5,-7.5,3.05)
    direction=Vector((0,-.5,1.45))-cam.location
    cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    # Keyframes for cutscene camera angles (constant interpolation).
    # Camera beats match the user-approved 0-3 / 3-7 / 7-11 / 11-14 / 14-15 storyboard.
    # Frames 1,37,85,133,169 at 12 fps.
    shots=[
        (1,(1.35,-1.1,2.35),(0,-3.55,1.95)),       # manager at desk, shot from COZO side
        (37,(1.65,-1.95,2.72),(0,0,2.52)),       # COZO mask and puffer
        (85,(2.6,-5.0,2.7),(0,0,1.6)),        # standing from chair
        (133,(.8,-1.0,2.85),(0,3.0,1.55)),       # rear view toward glass storefront
        (169,(1.0,-1.15,2.4),(0,-3.55,2.15)),    # manager reaction from front
    ]
    for frame,loc,target in shots:
        cam.location=loc
        cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
        cam.keyframe_insert(data_path="location",frame=frame)
        cam.keyframe_insert(data_path="rotation_euler",frame=frame)
    if cam.animation_data and cam.animation_data.action:
        for fc in action_curves(cam):
            for kp in fc.keyframe_points:kp.interpolation="CONSTANT"
    scene.frame_start=1;scene.frame_end=180;scene.render.fps=12
    scene.render.resolution_x=720;scene.render.resolution_y=1280
    scene.render.resolution_percentage=100
    cam.data.type="PERSP"
    cam.data.lens=35
    scene.frame_set(1)
    return {"scene":"CELVANI boutique","character":"COZO procedural blockout","duration":15,"fps":12,"aspectRatio":"9:16","status":"scene_blockout"}

if __name__=="__main__":
    import sys
    build()
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    bpy.ops.wm.save_as_mainfile(filepath=args[0] if args else "/tmp/cozo_boutique_blockout.blend")
