"""COZO replacement mesh importer and rig validation.

Import a legally usable rigged GLB, verify a real deformable humanoid exists,
and save a Blender staging file for original COZO sculpt/clothing work.
This intentionally does NOT call a generic humanoid 'finished COZO'.

Usage:
 blender -b --python-exit-code 1 --python apps/orni-blender/import_cozo_base.py -- /path/to/cc0-human.glb /tmp/cozo-base.blend
"""
import json,sys
from pathlib import Path
import bpy

def prepare(input_path,output_path):
    source=Path(input_path).resolve()
    if source.suffix.lower() not in (".glb",".gltf"):
        raise ValueError("A rigged .glb/.gltf is required")
    if not source.is_file():
        raise FileNotFoundError(source)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes=[o for o in bpy.data.objects if o.type=="MESH"]
    rigs=[o for o in bpy.data.objects if o.type=="ARMATURE"]
    if not meshes or not rigs:
        raise RuntimeError("Asset must contain both mesh and armature; refusing unrigged blockout")
    deform_bones=[b for rig in rigs for b in rig.data.bones if b.use_deform]
    if len(deform_bones)<15:
        raise RuntimeError("Asset must contain >=15 deform bones, got %d"%len(deform_bones))
    skinned=[m for m in meshes if any(mod.type=="ARMATURE" for mod in m.modifiers)]
    if not skinned:
        raise RuntimeError("No skinned mesh found. A skeleton alone cannot animate COZO.")
    vertices=sum(len(m.data.vertices) for m in skinned)
    if vertices<1000:
        raise RuntimeError("Skinned mesh too sparse (%d vertices) for COZO sculpting"%vertices)
    # Keep the CC0 source as an editable, named staging collection.
    for rig in rigs: rig.name="COZO_BASE | "+rig.name
    for mesh in skinned: mesh.name="COZO_BASE | "+mesh.name
    out=Path(output_path).resolve()
    out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    result={"status":"base_imported_not_reference_matched","source":source.name,
            "armatures":len(rigs),"deform_bones":len(deform_bones),
            "skinned_meshes":len(skinned),"skinned_vertices":vertices,
            "output":str(out),"next":"Sculpt original COZO mask, garment meshes, weights and animation"}
    print("COZO_BASE_VALIDATED="+json.dumps(result))
    return result

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=2:
        raise SystemExit("Usage: -- input.glb output.blend")
    prepare(*args)
