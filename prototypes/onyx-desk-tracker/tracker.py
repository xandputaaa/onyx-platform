"""Local webcam ArUco desk-marker proof of concept. No cloud or glasses connection."""
import argparse
import json
import time
import cv2
import numpy as np

DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

def marker_image(marker_id, size=400):
    if not 0 <= marker_id < 50:
        raise ValueError("Marker id must be 0..49")
    return cv2.aruco.generateImageMarker(DICT, marker_id, size)

def detect(frame):
    corners, ids, _ = cv2.aruco.ArucoDetector(DICT).detectMarkers(frame)
    found = []
    if ids is not None:
        for marker_id, corner in zip(ids.flatten(), corners):
            pts = corner.reshape(4, 2)
            found.append({"id": int(marker_id), "center_px": [round(float(x), 1) for x in pts.mean(axis=0)], "corners_px": pts.round(1).tolist()})
    return corners, ids, found

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--make-markers", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print detections locally as JSON lines")
    args = parser.parse_args()
    if args.make_markers:
        for i in range(4):
            cv2.imwrite(f"onyx-marker-{i}.png", marker_image(i))
        print("Created onyx-marker-0.png through onyx-marker-3.png. Print at equal measured size.")
        return
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit("Camera unavailable. Check index/permissions.")
    try:
        last = 0.0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            corners, ids, found = detect(frame)
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            cv2.putText(frame, f"ONYX DESK TRACKER | {len(found)} markers | NO 6DoF", (14, 30), cv2.FONT_HERSHEY_SIMPLEX, .65, (160, 230, 255), 2)
            cv2.imshow("ONYX desk tracker (Q to quit)", frame)
            now = time.monotonic()
            if args.json and now - last >= .25:
                print(json.dumps({"timestamp_monotonic": round(now, 3), "markers": found, "pose_valid": False, "desk_anchored": False}), flush=True)
                last = now
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
