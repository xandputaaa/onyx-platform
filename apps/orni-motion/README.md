# ORNI Motion — independent storyboard renderer

This module reproduces the approved COZO Episode 001 **motion-storyboard** method: split a six-panel 2-column × 3-row storyboard, add subtle camera push-ins and fades, optionally synthesize offline dialogue, and export a **15-second 720×1280 (9:16) MP4**.

It is **not** a full 3D animator or a Higgsfield/Kling replacement. It uses no paid API.

Requirements: Python 3, Pillow, numpy, opencv-python, ffmpeg; optional espeak.

```bash
python apps/orni-motion/motion_storyboard.py storyboard.jpg cozo.mp4 --dialogue-json dialogue.json
```

Example dialogue.json:

```json
[
 {"text":"Why do you want to work here?","at":0.55,"voice":"en-us+m3","speed":142},
 {"text":"I don't.","at":5.4,"voice":"en-us+m1","speed":115}
]
```

## Next phases

- Build and validate COZO as a reusable Blender rig with approved clothing, textures and animation cycles.
- Generate scenes, animation and lip sync through existing ORNI Blender worker.
- Integrate script, shot list, job queue, preview and export into ONYX.
- Add optional GPU-based ComfyUI backends only when hardware and model licensing permit.

Creative direction: original low-poly PS2-style cutscenes, recurring characters, deadpan comedy, fashion-forward settings. Reference creator imagery is stylistic inspiration, not animation source code.
