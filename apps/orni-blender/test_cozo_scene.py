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
assert scene.camera.animation_data is not None
for name in ("L_SHOULDER","R_SHOULDER","L_HIP","R_HIP"):
    obj=bpy.data.objects.get(name)
    assert obj and obj.animation_data, name
scene.render.engine="BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in {x.identifier for x in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_WORKBENCH"
scene.render.resolution_percentage=25
scene.render.image_settings.file_format="PNG"
with tempfile.TemporaryDirectory() as d:
    target=Path(d)/"cozo_frame.png"
    scene.render.filepath=str(target)
    scene.frame_set(95)
    bpy.ops.render.render(write_still=True)
    assert target.is_file() and target.stat().st_size>1024, "No preview frame"
    print("PASS COZO headless Blender scene and rendered preview:",target.stat().st_size)
