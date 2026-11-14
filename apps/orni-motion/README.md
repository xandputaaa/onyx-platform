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


## Blender Episode 001 blockout

The Blender worker now exposes two authenticated queued jobs:

- `POST /api/scene/cozo-rig` — editable COZO procedural character rig
- `POST /api/scene/cozo-episode` — editable boutique scene with COZO, manager placeholder, five camera positions, and a 180-frame animation timeline

Poll `GET /job-status` with `Authorization: Bearer <ORNI_BLENDER_TOKEN>`; download `/outputs/cozo_episode_001_blockout.blend` using the same token once complete. These endpoints run on the worker's internal control API (port 8765), not the public noVNC port.

For a local headless smoke render, with Blender installed:

```bash
blender -b --python apps/orni-blender/test_cozo_scene.py
```

**Known limitations:** No verified rendered episode yet; no final rigged COZO mesh, facial animation, clothing simulation, full character walk cycle or synchronized dialogue in Blender. The scene uses simple primitives and stand-ins. Do not present the blockout as a finished production.
