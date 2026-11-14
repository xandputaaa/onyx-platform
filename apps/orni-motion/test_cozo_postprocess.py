"""Smoke-test offline COZO finishing with generated video; no Blender required."""
import json, subprocess, tempfile
from pathlib import Path
import cozo_postprocess

with tempfile.TemporaryDirectory(prefix="cozo_finish_ci_") as d:
    folder=Path(d)
    source=folder/"source.mp4"
    target=folder/"finished.mp4"
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","lavfi",
        "-i","color=c=gray:s=360x640:r=12:d=15",
        "-c:v","libx264","-pix_fmt","yuv420p",str(source)],check=True,timeout=60)
    result=cozo_postprocess.run(source,target)
    assert result["duration"]==15.0, result
    assert target.stat().st_size>10000
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries",
        "stream=codec_name,codec_type,width,height:format=duration","-of","json",str(target)]))
    assert any(s.get("codec_name")=="h264" and s.get("width")==360 and s.get("height")==640 for s in probe["streams"])
    assert abs(float(probe["format"]["duration"])-15)<0.1
    print("PASS COZO post-production: playable 15-second H264 MP4")
