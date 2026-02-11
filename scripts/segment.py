import cv2
import numpy as np
import os
from pathlib import Path

# Area selection: can be set via env `AREA` or first CLI argument
area = os.environ.get("AREA")
import sys
if not area and len(sys.argv) > 1:
    area = sys.argv[1]
if not area:
    area = "Periyar"

# Create Output folder if it doesn't exist
if not os.path.exists("Output"):
    os.makedirs("Output")

# Get all images in Data/<area> folder
image_dir = Path(f"Data/{area}")
image_files = sorted(image_dir.glob("*.png")) + sorted(image_dir.glob("*.jpg")) + sorted(image_dir.glob("*.jpeg"))

if not image_files:
    print(f"No images found in Data/{area}/")
    exit()

print(f"Found {len(image_files)} images in Data/{area}/")

# Initialize aggregate statistics
total_free_pixels = 0
total_pixels = 0
total_green_pixels = 0
total_green_pixels_in_free = 0
results = []


# Process each image
for img_path in image_files:
    print(f"\nProcessing: {img_path.name}")
    
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"  Error: Cannot read {img_path.name}")
        continue
    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Reshape for clustering
    pixels = img.reshape((-1, 3))
    pixels = np.float32(pixels)

    # Apply K-Means
    K = 4
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(
        pixels, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
    )

    # Rebuild segmented image
    centers = np.uint8(centers)
    segmented = centers[labels.flatten()]
    segmented = segmented.reshape(img.shape)

    # Save segmented image
    base_name = img_path.stem
    segmented_bgr = cv2.cvtColor(segmented, cv2.COLOR_RGB2BGR)
    cv2.imwrite(f"Output/{base_name}_segmented.png", segmented_bgr)

    # Auto-select free-land cluster by color distance to a soil prototype
    soil_proto = np.array([136, 117, 105], dtype=np.float32)
    centers_f = centers.astype(np.float32)
    dists = np.linalg.norm(centers_f - soil_proto, axis=1)
    free_cluster = int(np.argmin(dists))

    # Create mask for free land cluster
    mask = (labels.flatten() == free_cluster)
    mask = mask.reshape(img.shape[0], img.shape[1])

    # Save mask
    mask_uint8 = (mask * 255).astype(np.uint8)
    cv2.imwrite(f"Output/{base_name}_free_mask.png", mask_uint8)

    # Calculate statistics
    free_pixels = np.sum(mask)
    img_total_pixels = mask.size
    percentage = (free_pixels / img_total_pixels) * 100

    # Estimate trees (count green pixels)
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    lower_green = np.array([25, 25, 25])
    upper_green = np.array([100, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green) > 0
    green_pixels = int(np.sum(green_mask))
    # green pixels inside free land
    green_in_free = int(np.sum(green_mask.reshape(img.shape[0], img.shape[1]) & mask))
    avg_tree_pixels = 500
    estimated_trees_total = int(green_pixels / avg_tree_pixels) if avg_tree_pixels > 0 else 0
    estimated_trees_in_free = int(green_in_free / avg_tree_pixels) if avg_tree_pixels > 0 else 0

    # Store results
    results.append({
        "image": img_path.name,
        "free_land_pct": percentage,
        "free_pixels": int(free_pixels),
        "total_pixels": img_total_pixels,
        "estimated_trees_total": estimated_trees_total,
        "estimated_trees_in_free": estimated_trees_in_free
    })

    # Accumulate for aggregate stats
    total_free_pixels += free_pixels
    total_pixels += img_total_pixels
    total_green_pixels += green_pixels
    total_green_pixels_in_free += green_in_free

    print(f"  Free land: {percentage:.2f}% | Trees (total): {estimated_trees_total}, in free: {estimated_trees_in_free}")

# Calculate aggregate statistics
aggregate_percentage = (total_free_pixels / total_pixels) * 100 if total_pixels > 0 else 0
aggregate_trees = int(total_green_pixels / avg_tree_pixels) if avg_tree_pixels > 0 else 0
aggregate_trees_in_free = int(total_green_pixels_in_free / avg_tree_pixels) if avg_tree_pixels > 0 else 0

# Save individual reports
for result in results:
    report_path = f"Output/{result['image'].split('.')[0]}_report.txt"
    with open(report_path, "w") as f:
        f.write(f"Image: {result['image']}\n")
        f.write(f"Free land percentage = {result['free_land_pct']:.2f}%\n")
        f.write(f"Free land pixels = {result['free_pixels']}\n")
        f.write(f"Total pixels = {result['total_pixels']}\n")
        f.write(f"Estimated trees (all green) = {result['estimated_trees_total']}\n")
        f.write(f"Estimated trees (inside free land) = {result['estimated_trees_in_free']}\n")

# Save aggregate report
summary_path = f"Output/{area.upper()}_SUMMARY.txt"
with open(summary_path, "w") as f:
    f.write(f"PERIYAR AGGREGATE ANALYSIS\n")
    f.write(f"{'='*50}\n")
    f.write(f"Total images processed: {len(results)}\n")
    f.write(f"Total free land percentage = {aggregate_percentage:.2f}%\n")
    f.write(f"Total free land pixels = {int(total_free_pixels)}\n")
    f.write(f"Total pixels = {total_pixels}\n")
    f.write(f"Total estimated trees = {aggregate_trees}\n")
    f.write(f"Total estimated trees (inside free land) = {aggregate_trees_in_free}\n")
    f.write(f"\n{'='*50}\n")
    f.write(f"Individual image results:\n")
    f.write(f"{'='*50}\n")
    for i, result in enumerate(results, 1):
        f.write(f"\n{i}. {result['image']}\n")
        f.write(f"   Free land: {result['free_land_pct']:.2f}%\n")
        f.write(f"   Trees (total): {result['estimated_trees_total']}\n")
        f.write(f"   Trees (in free land): {result['estimated_trees_in_free']}\n")

print(f"\n{'='*50}")
print(f"PERIYAR AGGREGATE RESULTS:")
print(f"{'='*50}")
print(f"Images processed: {len(results)}")
print(f"Total free land percentage: {aggregate_percentage:.2f}%")
print(f"Total estimated trees: {aggregate_trees}")
print(f"Total estimated trees (inside free land): {aggregate_trees_in_free}")
print(f"\nAll outputs saved to Output/ folder")
