"""Free offline post-production for COZO Episode 001.
Adds timed captions, synthesized dialogue (when espeak is available), and title card.
Does not replace the underlying 3D animation. Requires FFmpeg; espeak optional.
"""
import argparse, json, shutil, subprocess, tempfile
from pathlib import Path

def run(input_video, output_video):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg and ffprobe are required")
    input_video=Path(input_video)
    output_video=Path(output_video)
    output_video.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cozo_post_") as folder:
        d=Path(folder)
        captions=d/"captions.ass"
        captions.write_text(
            "[Script Info]\nScriptType: v4.00+\nPlayResX: 360\nPlayResY: 640\n"
            "[V4+ Styles]\n"
            "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
            "Style: Default,DejaVu Sans,22,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,2,22,22,82,1\n"
            "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
            "Dialogue: 0,0:00:00.20,0:00:02.90,Default,,0,0,0,,Manager: Why do you want\\Nto work here?\n"
            "Dialogue: 0,0:00:03.20,0:00:06.30,Default,,0,0,0,,COZO: I don't.\n"
            "Dialogue: 0,0:00:14.40,0:00:15.00,Default,,0,0,0,,CELVANI  /  001\n",
            encoding="utf-8")
        cmd=["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(input_video)]
        voices=[]
        if shutil.which("espeak"):
            for i,(at,line,speed) in enumerate([(0.3,"Why do you want to work here?",155),(3.3,"I don't.",118)]):
                wav=d/("voice%d.wav"%i)
                subprocess.run(["espeak","-v","en-us","-s",str(speed),"-w",str(wav),line],check=True,timeout=20)
                cmd+=["-i",str(wav)]
                voices.append((i+1,int(at*1000)))
        if voices:
            filters=[f"[{i}:a]adelay={delay}:all=1[v{i}]" for i,delay in voices]
            filters.append("".join(f"[v{i}]" for i,_ in voices)+f"amix=inputs={len(voices)}:duration=longest:normalize=0,atrim=0:15[a]")
            cmd+=["-filter_complex",";".join(filters),"-map","0:v","-map","[a]","-c:a","aac","-b:a","128k"]
        else:
            cmd+=["-map","0:v","-an"]
        # Filter uses a temporary path with no quote characters; subtitle file is local.
        cmd+=["-vf","drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:enable=gte(t\\,14.5),ass="+str(captions),"-c:v","libx264","-profile:v","baseline",
              "-level:v","3.1","-pix_fmt","yuv420p","-movflags","+faststart",
              "-t","15",str(output_video)]
        subprocess.run(cmd,check=True,timeout=180)
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height","-of","json",str(output_video)],timeout=20))
    duration=float(probe["format"]["duration"])
    if not 14.9<=duration<=15.1:
        raise RuntimeError("Unexpected output duration: "+str(duration))
    return {"file":str(output_video),"duration":duration,"subtitles":"burned-in","voice":"espeak" if voices else "unavailable","mode":"postproduced_blockout"}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("input");p.add_argument("output")
    a=p.parse_args()
    print(json.dumps(run(a.input,a.output)))
