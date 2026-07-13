from nudenet import NudeDetector
from pathlib import Path
from PIL import Image
import cv2
import numpy as np

detector = NudeDetector()

# Original image path
image_path = Path("images") / "test.jpg"

# Auto converted image path
fixed_image_path = Path("images") / "test_fixed.png"

print("Checking image path:", image_path)

# Step 1: File exists check
if not image_path.exists():
    print("ERROR: Image file not found.")
    print("Available files inside images folder:")

    images_folder = Path("images")
    if images_folder.exists():
        for file in images_folder.iterdir():
            print("-", file.name)

    exit()

# Step 2: First try OpenCV read
test_img = cv2.imread(str(image_path))

# Step 3: If OpenCV fails, use PIL to convert image
if test_img is None:
    print("OpenCV image read failed.")
    print("Trying auto-convert using Pillow...")

    try:
        pil_img = Image.open(image_path)
        pil_img = pil_img.convert("RGB")
        pil_img.save(fixed_image_path)

        print("Image auto-converted successfully:", fixed_image_path)

        image_path = fixed_image_path
        test_img = cv2.imread(str(image_path))

        if test_img is None:
            print("ERROR: Converted image bhi OpenCV read nahi kar pa raha.")
            exit()

    except Exception as e:
        print("ERROR: Pillow bhi image open nahi kar pa raha.")
        print("Reason:", e)
        exit()

print("Image loaded successfully.")
print("Final image used:", image_path)
print("Image shape:", test_img.shape)

# Step 4: NudeNet detection
results = detector.detect(str(image_path))

print("\nDetection Results:")
for item in results:
    print(item)

unsafe_labels = [
    "FEMALE_BREAST_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "ANUS_EXPOSED"
]

is_unsafe = False

for item in results:
    label = item.get("class")
    score = item.get("score", 0)

    print(f"Detected: {label} | Score: {score}")

    threshold = 0.45

    if label in unsafe_labels and score >= threshold:
        is_unsafe = True
        print(f"Unsafe detected: {label} | Score: {score}")

if is_unsafe:
    print("\nFinal Result: NSFW / Unsafe Image")
else:
    print("\nFinal Result: Safe Image")