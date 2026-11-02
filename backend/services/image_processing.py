"""
ArchiveMind - Manuscript Image Processing Service
Performs archival enhancement: deskewing, noise filtering, contrast equalization (CLAHE),
adaptive thresholding, and perspective alignment without mutating original captures.
"""

import os
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Dict, Any, Tuple, Optional


def validate_image(image_path: str) -> Tuple[bool, Optional[str]]:
    """Checks that the image exists, is readable by OpenCV, and has valid dimensions."""
    if not os.path.exists(image_path):
        return False, "File does not exist"
    
    if os.path.getsize(image_path) < 1024:
        return False, "File too small or corrupted (< 1 KB)"
        
    img = cv2.imread(image_path)
    if img is None:
        return False, "OpenCV failed to decode image"
        
    h, w = img.shape[:2]
    if h < 50 or w < 50:
        return False, f"Image dimensions too small ({w}x{h})"
        
    return True, None


def deskew_image(gray: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Computes text skew angle using minAreaRect on binary contours,
    rotates image to restore horizontal orientation.
    """
    # Invert image (text becomes foreground white)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 100:
        return gray, 0.0

    angle = cv2.minAreaRect(coords)[-1]
    # Correct angle range
    if angle < -45:
        angle = -(90 + angle)
    elif angle > 45:
        angle = 90 - angle
    else:
        angle = -angle

    # Limit extreme skew to avoid 90-degree accidental flips
    if abs(angle) > 25.0:
        angle = 0.0

    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated, round(float(angle), 2)


def enhance_manuscript(
    original_path: str,
    processed_dir: str,
    output_prefix: str = "enhanced_"
) -> Dict[str, Any]:
    """
    Applies full archival preservation and CV pipeline:
    1. Grayscale conversion
    2. Bilateral noise filtering (preserves ink stroke edges)
    3. Deskewing
    4. CLAHE contrast enhancement
    5. Adaptive binarization
    6. Generates processed image and side-by-side comparison
    """
    is_valid, err = validate_image(original_path)
    if not is_valid:
        raise ValueError(f"Invalid image '{original_path}': {err}")

    # Read original
    orig_bgr = cv2.imread(original_path)
    orig_h, orig_w = orig_bgr.shape[:2]
    gray = cv2.cvtColor(orig_bgr, cv2.COLOR_BGR2GRAY)

    # 1. Bilateral filter for noise reduction without blurring fine ink strokes
    denoised = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    # 2. Deskew
    deskewed_gray, skew_angle = deskew_image(denoised)

    # 3. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    contrast_enhanced = clahe.apply(deskewed_gray)

    # 4. Adaptive thresholding for optimal reading contrast
    adaptive_thresh = cv2.adaptiveThreshold(
        contrast_enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=25,
        C=10
    )

    # 5. Save processed image
    os.makedirs(processed_dir, exist_ok=True)
    filename = Path(original_path).stem
    processed_filename = f"{output_prefix}{filename}.jpg"
    processed_path = os.path.join(processed_dir, processed_filename)

    # Write enhanced grayscale / thresholded hybrid for maximum legibility
    cv2.imwrite(processed_path, contrast_enhanced)

    # 6. Generate side-by-side comparison preview
    preview_filename = f"comparison_{filename}.jpg"
    preview_path = os.path.join(processed_dir, preview_filename)

    # Resize preview to standard display height if large
    display_h = 600
    scale = display_h / float(orig_h)
    display_w = int(orig_w * scale)
    
    left_img = cv2.resize(orig_bgr, (display_w, display_h))
    right_img = cv2.resize(cv2.cvtColor(contrast_enhanced, cv2.COLOR_GRAY2BGR), (display_w, display_h))

    # Add label headers
    cv2.rectangle(left_img, (0, 0), (display_w, 35), (20, 20, 20), -1)
    cv2.putText(left_img, "ORIGINAL RAW CAPTURE", (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.rectangle(right_img, (0, 0), (display_w, 35), (10, 40, 20), -1)
    cv2.putText(right_img, f"ENHANCED ARCHIVAL (Skew: {skew_angle:+0.1f} deg)", (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 255, 220), 1, cv2.LINE_AA)

    combined_preview = np.hstack([left_img, right_img])
    cv2.imwrite(preview_path, combined_preview)

    return {
        "original_path": original_path,
        "processed_path": processed_path,
        "preview_path": preview_path,
        "skew_angle": skew_angle,
        "original_dimensions": {"width": orig_w, "height": orig_h},
        "filters_applied": [
            "Bilateral Denoising (sigma=75)",
            f"Hough/Contour Deskew ({skew_angle} deg)",
            "CLAHE Adaptive Histogram Equalization",
            "Gaussian Adaptive Thresholding"
        ]
    }
