"""ORNI Motion: six-panel storyboard to 9:16 MP4. Requires cv2, Pillow, numpy, ffmpeg; espeak optional."""
import argparse, json, shutil, subprocess, tempfile
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

def render(storyboard, output, dialogue=None, fps=15):
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is required")
    src=Image.open(storyboard).convert("RGB")
    w,h=src.size
    panels=[np.asarray(src.crop((c*w//2,r*h//3,(c+1)*w//2,(r+1)*h//3))) for r in range(3) for c in range(2)]
    sizes=[45,60,60,45,8,7]  # exactly 225 frames / 15 seconds
    width,height=720,1280
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        tmp=Path(temp)
        raw=tmp/"silent.mp4"
        writer=cv2.VideoWriter(str(raw),cv2.VideoWriter_fourcc(*"mp4v"),fps,(width,height))
        if not writer.isOpened():
            raise RuntimeError("Could not open video writer")
        idx=0
        try:
            for panel,count in zip(panels,sizes):
                ph,pw=panel.shape[:2]
                for frame in range(count):
                    t=frame/max(1,count-1)
                    zoom=1.04+0.06*t
                    cw,ch=int(pw/zoom),int(ph/zoom)
                    x=(pw-cw)//2
                    y=(ph-ch)//2
                    cut=panel[y:y+ch,x:x+cw]
                    scale=min(width/cw,height/ch)
                    rw,rh=int(cw*scale),int(ch*scale)
                    foreground=cv2.resize(cut,(rw,rh))
                    background=cv2.resize(cut,(width,height))
                    background=(cv2.GaussianBlur(background,(0,0),40)*0.45).astype("uint8")
                    left,top=(width-rw)//2,(height-rh)//2
                    background[top:top+rh,left:left+rw]=foreground
                    fade=max(0,min(1,idx/5,(224-idx)/5))
                    writer.write(cv2.cvtColor((background*fade).astype("uint8"),cv2.COLOR_RGB2BGR))
                    idx+=1
        finally:
            writer.release()
        cmd=["ffmpeg","-y","-loglevel","error","-i",str(raw)]
        voices=[]
        if dialogue and shutil.which("espeak"):
            for i,line in enumerate(dialogue):
                wav=tmp/f"voice{i}.wav"
                subprocess.run(["espeak","-v",line.get("voice","en-us"),"-s",str(line.get("speed",140)),"-w",str(wav),line["text"]],check=True)
                cmd.extend(["-i",str(wav)])
                voices.append((i+1,int(float(line.get("at",0))*1000)))
        if voices:
            filters=[f"[{i}:a]adelay={delay}:all=1[v{i}]" for i,delay in voices]
            filters.append("".join(f"[v{i}]" for i,_ in voices)+f"amix=inputs={len(voices)}:duration=longest:normalize=0,atrim=0:15[a]")
            cmd+=["-filter_complex",";".join(filters),"-map","0:v","-map","[a]","-c:a","aac"]
        else:
            cmd+=["-map","0:v","-an"]
        cmd+=["-c:v","libx264","-pix_fmt","yuv420p","-t","15","-movflags","+faststart",str(output)]
        subprocess.run(cmd,check=True)
    return {"file":str(output),"width":720,"height":1280,"duration":15,"mode":"motion_storyboard"}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("storyboard")
    p.add_argument("output")
    p.add_argument("--dialogue-json")
    args=p.parse_args()
    lines=json.loads(Path(args.dialogue_json).read_text()) if args.dialogue_json else None
    print(json.dumps(render(args.storyboard,args.output,lines)))
