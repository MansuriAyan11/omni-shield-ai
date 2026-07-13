from nudenet import NudeDetector
from pathlib import Path
from PIL import Image
import cv2
import os

detector = NudeDetector()

# Your video path
video_path = Path("videos") / "test.mp4"

# Temporary frame image
temp_frame_path = Path("temp_frame.jpg")

print("Checking video path:", video_path)

# Check video exists
if not video_path.exists():
    print("ERROR: Video file not found.")
    print("Available files inside videos folder:")

    videos_folder = Path("videos")
    if videos_folder.exists():
        for file in videos_folder.iterdir():
            print("-", file.name)
    else:
        print("videos folder not found.")

    exit()

# Open video
cap = cv2.VideoCapture(str(video_path))

if not cap.isOpened():
    print("ERROR: Video open nahi ho raha.")
    print("Possible reasons:")
    print("1. Video corrupt hai")
    print("2. Path wrong hai")
    print("3. Video format unsupported hai")
    print("4. File actual video nahi hai")
    exit()

unsafe_labels = [
    "FEMALE_BREAST_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "ANUS_EXPOSED"
]

# NudeNet threshold
threshold = 0.45

frame_count = 0
checked_frame_count = 0
unsafe_frame_count = 0

print("\nVideo scanning started...")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    frame_count += 1

    # Har 30th frame check karega
    # 30 means approx 1 second if video is 30 FPS
    if frame_count % 30 == 0:
        checked_frame_count += 1

        # Save current frame as image
        cv2.imwrite(str(temp_frame_path), frame)

        # OpenCV saved image check
        test_img = cv2.imread(str(temp_frame_path))

        if test_img is None:
            print(f"Frame {frame_count} read failed, skipping...")
            continue

        # NudeNet detection on frame
        results = detector.detect(str(temp_frame_path))

        frame_is_unsafe = False

        for item in results:
            label = item.get("class")
            score = item.get("score", 0)

            print(f"Frame {frame_count}: {label} | Score: {score}")

            if label in unsafe_labels and score >= threshold:
                frame_is_unsafe = True
                break

        if frame_is_unsafe:
            unsafe_frame_count += 1
            print(f"Unsafe detected at frame: {frame_count}")

cap.release()

# Remove temp frame
if temp_frame_path.exists():
    os.remove(temp_frame_path)

print("\nVideo Scan Summary")
print("------------------")
print("Total frames:", frame_count)
print("Checked frames:", checked_frame_count)
print("Unsafe frames:", unsafe_frame_count)

if unsafe_frame_count > 0:
    print("\nFinal Result: NSFW / Unsafe Video")
else:
    print("\nFinal Result: Safe Video")