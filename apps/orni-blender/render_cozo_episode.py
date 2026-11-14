"""Render a 15-second 9:16 COZO boutique proof-of-animation from Blender.
Offline/free: Blender Workbench + system FFmpeg. This is NOT final production quality.
Run: blender -b --python apps/orni-blender/render_cozo_episode.py -- /tmp/cozo.mp4
"""
import json, subprocess, sys, tempfile
from pathlib import Path
# Blender's --python execution does not always put the script directory on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import cozo_boutique
import cozo_postprocess

def render(output):
    result=cozo_boutique.build()
    scene=bpy.context.scene
    scene.render.engine="BLENDER_WORKBENCH"
    scene.render.resolution_x=360
    scene.render.resolution_y=640
    scene.render.resolution_percentage=100
    scene.render.fps=12
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=False
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="orni_cozo_") as d:
        folder=Path(d)
        scene.render.filepath=str(folder/"frame_")
        bpy.ops.render.render(animation=True)
        frames=sorted(folder.glob("frame_*.png"))
        expected=scene.frame_end-scene.frame_start+1
        if len(frames)!=expected:
            raise RuntimeError("Expected %d frames, got %d"%(expected,len(frames)))
        command=["ffmpeg","-y","-hide_banner","-loglevel","error",
            "-framerate",str(scene.render.fps),"-start_number",str(scene.frame_start),
            "-i",str(folder/"frame_%04d.png"),
            "-c:v","libx264","-preset","veryfast","-crf","22",
            "-pix_fmt","yuv420p","-movflags","+faststart","-an",str(output)]
        subprocess.run(command,check=True,timeout=600)
        raw=output.with_name(output.stem+"_raw.mp4")
        output.replace(raw)
        try:
            cozo_postprocess.run(raw,output)
        except Exception:
            if output.exists(): output.unlink()
            raw.replace(output)
            raise
        finally:
            if raw.exists(): raw.unlink()
    if not output.is_file() or output.stat().st_size<2048:
        raise RuntimeError("COZO episode MP4 missing or empty")
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries",
        "format=duration:stream=width,height,nb_frames","-of","json",str(output)],timeout=30))
    stream=probe["streams"][0]
    duration=float(probe["format"]["duration"])
    if (stream["width"],stream["height"])!=(360,640) or not 14.9<=duration<=15.1:
        raise RuntimeError("COZO MP4 dimensions or duration invalid: "+str(probe))
    return {"ok":True,"file":str(output),"durationSeconds":duration,
            "width":360,"height":640,"fps":12,"frames":expected,
            "mode":"blender_blockout_animation","audio":True,"captions":True,
            "note":"15-second procedural 3D blockout; final COZO assets and voice pending"}

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    print(json.dumps(render(args[0] if args else "/tmp/cozo_episode_001_blockout.mp4")))
