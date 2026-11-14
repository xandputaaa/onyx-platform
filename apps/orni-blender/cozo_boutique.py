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

def build():
    root=cozo_rig.build()
    concrete=cozo_rig.material("CELVANI | cool concrete",(0.24,0.245,0.25))
    steel=cozo_rig.material("CELVANI | steel racks",(0.07,0.075,0.08))
    textile=cozo_rig.material("CELVANI | hanging black garments",(0.03,0.032,0.035))
    walnut=cozo_rig.material("CELVANI | interview table",(0.18,0.12,0.08))
    cube("Boutique concrete floor",(0,0,-.17),(12,12,.3),concrete)
    # Side wall wings leave the central aisle open to the storefront.\n    cube("Boutique rear wall left",(-4.8,3.0,2.5),(2.4,.22,5),concrete)\n    cube("Boutique rear wall right",(4.8,3.0,2.5),(2.4,.22,5),concrete)
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
        (1,(1.8,-5.0,2.3),(0,-.15,1.65)),       # interview, manager shoulder foreground
        (37,(.65,-2.8,2.65),(0,0,2.55)),       # COZO mask and puffer
        (85,(2.6,-5.0,2.7),(0,0,1.6)),        # standing from chair
        (133,(.8,-.9,2.9),(0,2.5,1.4)),       # rear view toward glass storefront
        (169,(.9,-5.0,2.6),(0,-3.55,2.1)),    # manager reaction
    ]
    for frame,loc,target in shots:
        cam.location=loc
        cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
        cam.keyframe_insert(data_path="location",frame=frame)
        cam.keyframe_insert(data_path="rotation_euler",frame=frame)
    if cam.animation_data and cam.animation_data.action:
        for fc in cam.animation_data.action.fcurves:
            for kp in fc.keyframe_points:kp.interpolation="CONSTANT"
    scene.frame_start=1;scene.frame_end=180;scene.render.fps=12
    scene.render.resolution_x=720;scene.render.resolution_y=1280
    scene.render.resolution_percentage=100
    scene.frame_set(1)
    return {"scene":"CELVANI boutique","character":"COZO procedural blockout","duration":15,"fps":12,"aspectRatio":"9:16","status":"scene_blockout"}

if __name__=="__main__":
    import sys
    build()
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    bpy.ops.wm.save_as_mainfile(filepath=args[0] if args else "/tmp/cozo_boutique_blockout.blend")
