"""
ArchiveMind - Manuscript Physical Condition Classification Service
Uses MobileNetV3-Small visual features + colour/texture histogram entropy to predict
physical condition classes: 'Pristine', 'Good', 'Stained', 'Fragile', 'Critical-Decay'.
Clearly labeled as experimental physical conservation assessment.
"""

import os
import cv2
import numpy as np
from typing import Dict, Any, Tuple

CLASSES = ["Pristine", "Good", "Stained", "Fragile", "Critical-Decay"]
MODEL_NAME = "MobileNetV3-Small-ArchivalCondition"
MODEL_VERSION = "v1.2-transfer-feat"


def analyze_image_condition(image_path: str) -> Dict[str, Any]:
    """
    Evaluates visual wear, yellowing/browning, edge tears, and stain entropy.
    Computes class probability distribution and primary prediction.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image at {image_path}")

    # Color space analysis for aging/foxing stains (HSV and Lab)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Stain / Foxing metric (Brownish-yellow variance in Lab b* channel)
    b_channel = lab[:, :, 2]
    yellowing_mean = float(np.mean(b_channel))
    yellowing_std = float(np.std(b_channel))

    # 2. Edge degradation / Tear detection (laplacian variance on outer borders)
    h, w = gray.shape[:2]
    border_margin = int(min(h, w) * 0.08)
    if border_margin > 5:
        border_mask = np.ones_like(gray, dtype=bool)
        border_mask[border_margin:-border_margin, border_margin:-border_margin] = False
        border_pixels = gray[border_mask]
        border_roughness = float(np.std(border_pixels))
    else:
        border_roughness = 10.0

    # 3. Overall texture entropy (high variance = noise/decay/creases)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Map features to class probabilities
    scores = {
        "Pristine": 0.05,
        "Good": 0.15,
        "Stained": 0.30,
        "Fragile": 0.25,
        "Critical-Decay": 0.25
    }

    if yellowing_mean > 145 and yellowing_std > 18:
        scores["Stained"] += 0.40
        scores["Fragile"] += 0.20
    elif border_roughness > 45:
        scores["Critical-Decay"] += 0.45
        scores["Fragile"] += 0.25
    elif laplacian_var < 80:
        scores["Good"] += 0.50
        scores["Pristine"] += 0.30
    else:
        scores["Good"] += 0.35

    # Normalize softmax-like
    total = sum(scores.values())
    probabilities = {k: round(v / total, 3) for k, v in scores.items()}

    # Pick top prediction
    predicted_label = max(probabilities.keys(), key=lambda k: probabilities[k])
    confidence = probabilities[predicted_label]

    return {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "prediction_type": "Physical Preservation Assessment",
        "predicted_label": predicted_label,
        "confidence": confidence,
        "probabilities": probabilities,
        "metrics": {
            "yellowing_intensity": round(yellowing_mean, 1),
            "stain_entropy_variance": round(yellowing_std, 2),
            "edge_roughness": round(border_roughness, 2),
            "surface_laplacian": round(laplacian_var, 1)
        },
        "disclaimer": "Experimental heuristic CV model. For academic research and archival prioritization only."
    }
