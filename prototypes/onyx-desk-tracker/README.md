# ONYX DESK TRACKER — Stage 1

Local webcam marker-detection experiment for XREAL Air 2 companion hardware. **Does not detect a desk plane, estimate metric pose, track the wearer, render to glasses, or provide 6DoF anchoring.**

## Setup

Requires Python 3.10+, webcam and permission to access it.

```sh
cd prototypes/onyx-desk-tracker
python -m venv .venv
# Activate the virtual environment for your OS
pip install -r requirements.txt
python tracker.py --make-markers
python tracker.py --camera 0 --json
```

Print the four generated markers, place them flat at different desk corners, and aim the camera at the desk. The preview should outline recognized markers. Press Q to quit. JSON output is local only; nothing is uploaded.

For actual 3D pose estimation, calibrate camera intrinsics and distortion and use measured marker dimensions with OpenCV `solvePnP`; use a multi-marker board when possible. To align a headset-rendered model with the desk, also estimate the **headset's six-degree-of-freedom pose relative to the desk**, calibrate the camera-to-headset transform, and verify rendering latency. A stationary webcam that merely detects desk markers is insufficient.

Source: https://docs.opencv.org/4.10.0/d5/dae/tutorial_aruco_detection.html

No new paid services; this experiment does not touch production.
