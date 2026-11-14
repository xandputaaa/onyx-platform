"""Regression checks for ORNI Motion's aspect ratio, duration and optional audio."""
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

MODULE=Path(__file__).with_name("motion_storyboard.py")
spec=importlib.util.spec_from_file_location("orni_motion",MODULE)
motion=importlib.util.module_from_spec(spec)
spec.loader.exec_module(motion)

@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"ffmpeg/ffprobe required")
class MotionSmokeTest(unittest.TestCase):
    def test_storyboard_exports_vertical_fifteen_seconds(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            image=Image.new("RGB",(600,900),"#202020")
            draw=ImageDraw.Draw(image)
            for i in range(6):
                x=(i%2)*300
                y=(i//2)*300
                draw.rectangle((x+15,y+15,x+285,y+285),fill=(35+i*25,45,55))
                draw.text((x+35,y+35),f"SHOT {i+1}",fill="white")
            source=d/"storyboard.png"
            image.save(source)
            dest=d/"test.mp4"
            result=motion.render(source,dest)
            self.assertTrue(dest.is_file())
            self.assertEqual(result["mode"],"motion_storyboard")
            probe=json.loads(subprocess.check_output([
                "ffprobe","-v","error","-show_streams","-show_format","-of","json",str(dest)
            ]))
            video=next(s for s in probe["streams"] if s["codec_type"]=="video")
            self.assertEqual((video["width"],video["height"]),(720,1280))
            self.assertEqual(int(video["nb_frames"]),225)
            self.assertAlmostEqual(float(probe["format"]["duration"]),15,delta=0.15)

if __name__=="__main__":
    unittest.main()
