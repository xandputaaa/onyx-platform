"""Offline CI integration test for COZO's skinned-humanoid GLB import gate.
A synthetic fixture tests the importer; it is NOT the production character asset.
"""
import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from import_cozo_base import prepare

def fixture(path):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.object.armature_add()
    rig=bpy.context.object
    rig.name="TEST | deform skeleton"
    bpy.ops.object.mode_set(mode="EDIT")
    base=rig.data.edit_bones[0]
    base.name="root"
    base.head=(0,0,0)
    base.tail=(0,0,.12)
    parent=base
    for i in range(20):
        bone=rig.data.edit_bones.new("bone_%02d"%i)
        bone.head=(0,0,(i+1)*.12)
        bone.tail=(0,0,(i+2)*.12)
        bone.parent=parent
        parent=bone
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,location=(0,0,1))
    mesh=bpy.context.object
    mesh.name="TEST | humanoid placeholder"
    group=mesh.vertex_groups.new(name="root")
    group.add(list(range(len(mesh.data.vertices))),1.0,"REPLACE")
    mod=mesh.modifiers.new("Armature","ARMATURE")
    mod.object=rig
    mesh.parent=rig
    bpy.ops.export_scene.gltf(filepath=str(path),export_format="GLB",
                              export_apply=False,export_skins=True)
    assert path.is_file() and path.stat().st_size>1000

def test():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d)
        glb=root/"fixture.glb"
        fixture(glb)
        result=prepare(glb,root/"imported.blend")
        assert result["deform_bones"]>=15,result
        assert result["skinned_vertices"]>=1000,result
        assert (root/"imported.blend").is_file()
        print("COZO_RIG_IMPORT_SMOKE_TEST=PASS")
if __name__=="__main__":
    test()
