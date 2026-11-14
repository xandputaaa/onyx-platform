"""Headless validation for COZO boutique scene: rig, keyframes and render.
Run: blender -b --python apps/orni-blender/test_cozo_scene.py
"""
import os, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import cozo_boutique

result=cozo_boutique.build()
scene=bpy.context.scene
assert scene.camera is not None
assert scene.render.resolution_x==720 and scene.render.resolution_y==1280
assert scene.frame_end-scene.frame_start+1==180
assert scene.render.fps==12
assert bpy.data.objects.get("COZO_ROOT | motion controller") is not None
assert bpy.data.objects.get("Interview table") is not None
assert bpy.data.objects.get("Manager head") is not None
assert bpy.data.objects.get("COZO | recessed oval eye -1") is not None
assert bpy.data.objects.get("COZO | recessed oval eye 1") is not None
assert bpy.data.objects.get("COZO | tapered mask chin") is not None
assert bpy.data.objects.get("CELVANI | wall sign") is not None
assert bpy.data.objects.get("Storefront left glass") is not None
assert scene.camera.animation_data is not None
for name in ("L_SHOULDER","R_SHOULDER","L_HIP","R_HIP"):
    obj=bpy.data.objects.get(name)
    assert obj and obj.animation_data, name
# Validate standing foot contact before rendering.
root=bpy.data.objects["COZO_ROOT | motion controller"]
scene.frame_set(132)
assert abs(root.location.z)<0.05, "COZO should finish standing at floor height"
from mathutils import Vector
for side in ("L","R"):
    boot=bpy.data.objects[side+" | boot"]
    bottom=min((boot.matrix_world @ Vector(v)).z for v in boot.bound_box)
    assert -0.08<=bottom<=0.18, ("Boot hovering or clipping",side,bottom)
scene.render.engine="BLENDER_WORKBENCH"
scene.render.resolution_percentage=25
scene.render.image_settings.file_format="PNG"
# Persist contact frames for GitHub Actions artifacts; temp output otherwise.
artifact_dir=os.environ.get("COZO_PREVIEW_DIR")
def verify_frames(folder):
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    for frame in (1,37,85,133,169):
        target=folder/("cozo_frame_%03d.png"%frame)
        scene.render.filepath=str(target)
        scene.frame_set(frame)
        bpy.ops.render.render(write_still=True)
        assert target.is_file() and target.stat().st_size>1024, "Missing frame %d"%frame
        print("PASS COZO reference shot frame",frame,target.stat().st_size)
if artifact_dir:
    verify_frames(artifact_dir)
else:
    with tempfile.TemporaryDirectory() as d:
        verify_frames(d)
