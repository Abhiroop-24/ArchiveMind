"""
ArchiveMind - Handwriting Style & Visual Forensics Service
Extracts visual handwriting descriptors (stroke thickness, slant angle, Hu moments, contour compactness).
Computes visual forensic distance across manuscript samples.
Clearly labeled as experimental paleographic analysis.
"""

import os
import cv2
import numpy as np
from typing import Dict, Any, List, Optional


def extract_visual_style_features(image_path: str) -> Dict[str, Any]:
    """
    Extracts geometric stroke and contour descriptors from manuscript ink strokes.
    Computes a 128-dimensional dense visual style fingerprint.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to read image at {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Compute Hu Moments (scale/rotation invariant shape moments)
    moments = cv2.moments(thresh)
    hu_moments = cv2.HuMoments(moments).flatten()
    # Log transform to make values comparable
    log_hu = [-np.sign(h) * np.log10(abs(h) + 1e-12) for h in hu_moments]

    # Find stroke contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_areas = [cv2.contourArea(c) for c in contours if cv2.contourArea(c) > 10]

    mean_stroke_area = float(np.mean(contour_areas)) if contour_areas else 0.0
    stroke_count = len(contour_areas)

    # Estimate dominant stroke slant angle using orientation of major contours
    slant_angles = []
    for c in contours:
        if len(c) >= 5:
            ellipse = cv2.fitEllipse(c)
            slant_angles.append(ellipse[2])

    median_slant = float(np.median(slant_angles)) if slant_angles else 0.0

    # Build 128-d dense feature vector from moments and spatial grid
    # Downsample thresholded image to 16x8 grid (128 cells)
    resized_grid = cv2.resize(thresh, (16, 8)).flatten().astype(np.float32) / 255.0
    # Normalize vector to unit length
    norm = np.linalg.norm(resized_grid)
    if norm > 0:
        normalized_vector = (resized_grid / norm).tolist()
    else:
        normalized_vector = resized_grid.tolist()

    return {
        "method": "OpenCV-ContourMoments-Grid128",
        "stroke_count": stroke_count,
        "mean_stroke_area": round(mean_stroke_area, 2),
        "dominant_slant_deg": round(median_slant, 1),
        "hu_moments_log": [round(float(h), 4) for h in log_hu[:7]],
        "feature_vector_128d": normalized_vector,
        "disclaimer": "Experimental visual feature extractor. Not certified for legal or historical forensic authentication."
    }
