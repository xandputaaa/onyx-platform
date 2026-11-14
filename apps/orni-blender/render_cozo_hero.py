"""Reference-comparison hero frame. Physically shaded Blender preview, not final likeness.
Run: blender -b --python-exit-code 1 --python apps/orni-blender/render_cozo_hero.py -- /tmp/cozo-hero.png
"""
import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import cozo_boutique

def render(path):
    cozo_boutique.build()
    scene=bpy.context.scene
    # Workbench ignores PBR fabric, lighting, transparency and surface normals.
    # Eevee material rendering is the appropriate reference-quality diagnostic.
    engines=bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys()
    if "BLENDER_EEVEE_NEXT" in engines:
        scene.render.engine="BLENDER_EEVEE_NEXT"
    elif "BLENDER_EEVEE" in engines:
        scene.render.engine="BLENDER_EEVEE"
    else:
        raise RuntimeError("Eevee engine unavailable; cannot produce material lookdev preview")
    scene.render.resolution_x=540
    scene.render.resolution_y=960
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=False
    scene.view_settings.view_transform="Standard"
    scene.view_settings.look="Medium High Contrast"
    scene.world.color=(.07,.07,.08)
    # Close-up mask and garment, the reference's most important identity test.
    scene.frame_set(49)
    if hasattr(scene,"eevee"):
        scene.eevee.taa_render_samples=32
    output=Path(path)
    output.parent.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(output)
    bpy.ops.render.render(write_still=True)
    if not output.is_file() or output.stat().st_size<15000:
        raise RuntimeError("Material hero render missing or suspiciously small")
    print("COZO_HERO_FRAME="+str(output))
if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    render(args[0] if args else "/tmp/cozo-hero.png")
