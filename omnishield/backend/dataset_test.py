from nudenet import NudeDetector
from pathlib import Path
from PIL import Image
import time

detector = NudeDetector()

dataset_path = Path("dataset")

unsafe_labels = [
    "FEMALE_BREAST_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "ANUS_EXPOSED"
]

threshold = 0.30

def fix_image_if_needed(image_path):
    fixed_path = image_path.with_name(image_path.stem + "_fixed.png")

    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        img.save(fixed_path)
        return fixed_path
    except:
        return image_path


def predict_image(image_path):
    try:
        image_path = fix_image_if_needed(image_path)

        results = detector.detect(str(image_path))

        for item in results:
            label = item.get("class")
            score = item.get("score", 0)

            if label in unsafe_labels and score >= threshold:
                return "unsafe", results

        return "safe", results

    except Exception as e:
        print("Error scanning:", image_path)
        print("Reason:", e)
        return "error", []


total = 0
correct = 0
false_positive = 0
missed_detection = 0

start = time.time()

for actual_label in ["safe", "unsafe"]:
    folder = dataset_path / actual_label

    if not folder.exists():
        print("Folder not found:", folder)
        continue

    for image_file in folder.iterdir():
        if image_file.suffix.lower() not in [".jpg", ".jpeg", ".png", ".webp"]:
            continue

        total += 1

        predicted_label, results = predict_image(image_file)

        print("\nImage:", image_file)
        print("Actual:", actual_label)
        print("Predicted:", predicted_label)

        if predicted_label == actual_label:
            correct += 1
            print("Result: Correct")
        else:
            print("Result: Wrong")

            if actual_label == "safe" and predicted_label == "unsafe":
                false_positive += 1

            if actual_label == "unsafe" and predicted_label == "safe":
                missed_detection += 1

end = time.time()

print("\nDataset Test Summary")
print("--------------------")
print("Total images:", total)
print("Correct detections:", correct)
print("False positives:", false_positive)
print("Missed detections:", missed_detection)

if total > 0:
    accuracy = (correct / total) * 100
    print(f"Accuracy: {accuracy:.2f}%")

print(f"Total time: {end - start:.2f} seconds")