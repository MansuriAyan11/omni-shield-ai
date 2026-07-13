from nudenet import NudeDetector
from pathlib import Path
import time

print("Speed test started...")

detector = NudeDetector()

# Apni working image ka path
image_path = Path("images") / "breast.jpg"

print("Checking image:", image_path)

if not image_path.exists():
    print("ERROR: Image not found:", image_path)
    print("Available files in images folder:")

    images_folder = Path("images")
    if images_folder.exists():
        for file in images_folder.iterdir():
            print("-", file.name)
    else:
        print("images folder not found")

    exit()

start_time = time.time()

results = detector.detect(str(image_path))

end_time = time.time()

scan_time = end_time - start_time

print("\nDetection Results:")
for item in results:
    print(item)

print("\nSpeed Result")
print("------------")
print(f"One image scan time: {scan_time:.4f} seconds")