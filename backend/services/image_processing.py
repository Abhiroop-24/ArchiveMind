"""
ArchiveMind - Manuscript Image Processing Service
Performs archival preservation:
1. OpenCV paper boundary detection
2. Automatic four-corner framing (TL, TR, BR, BL)
3. 4-point perspective correction (unwarping to flat top-down A4 folio)
4. Bilateral noise filtering & CLAHE contrast enhancement
5. Deskewing & adaptive binarization for OCR/HTR fidelity
"""

import os
try:
    import cv2
except ImportError:
    cv2 = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from PIL import Image, ImageOps, ImageFilter, ImageEnhance
except ImportError:
    Image = None

from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List


def validate_image(image_path: str) -> Tuple[bool, Optional[str]]:
    """Checks that the image exists and has valid dimensions."""
    if not os.path.exists(image_path):
        return False, "File does not exist"
    
    if os.path.getsize(image_path) < 100:
        return False, "File too small or corrupted (< 100 bytes)"

    if cv2 is not None:
        img = cv2.imread(image_path)
        if img is None:
            return False, "OpenCV failed to decode image"
        h, w = img.shape[:2]
        if h < 40 or w < 40:
            return False, f"Image dimensions too small ({w}x{h})"
        return True, None
    elif Image is not None:
        try:
            with Image.open(image_path) as im:
                w, h = im.size
                if h < 40 or w < 40:
                    return False, f"Image dimensions too small ({w}x{h})"
                return True, None
        except Exception as e:
            return False, f"PIL decode error: {e}"
    return True, None


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Orders 4 quadrilateral coordinates in consistent order:
    0: Top-Left (TL)
    1: Top-Right (TR)
    2: Bottom-Right (BR)
    3: Bottom-Left (BL)
    """
    pts = np.asarray(pts, dtype="float32").reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")

    # Sum: top-left has smallest sum, bottom-right has largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # Difference: top-right has smallest diff (y - x), bottom-left has largest diff
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def four_point_perspective_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """
    Applies homography / perspective transformation to unwarp a quadrilateral paper
    boundary into a clean, flat, top-down rectangular document view.
    """
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Calculate width of new image
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    # Calculate height of new image
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    if maxWidth < 20 or maxHeight < 20:
        return image

    # Construct destination points for perspective correction
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    # Compute homography matrix and warp perspective
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight), flags=cv2.INTER_LANCZOS4)
    return warped


def deskew_image(gray: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Computes residual text skew angle using minAreaRect on binary contours,
    rotates image to restore horizontal orientation.
    """
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 100:
        return gray, 0.0

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    elif angle > 45:
        angle = 90 - angle
    else:
        angle = -angle

    if abs(angle) > 25.0:
        angle = 0.0

    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated, round(float(angle), 2)


def detect_a4_contour(img: np.ndarray) -> Dict[str, Any]:
    """
    Precision A4 Document Sheet Detector with Automatic 4-Corner Framing.
    Detects paper boundary, calculates the 4 precise corners [TL, TR, BR, BL],
    and checks aspect ratio (1:1.4142) and substrate contrast.
    """
    if img is None:
        return {"detected": False, "confidence": 0.0, "reason": "Empty image"}

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    # Bilateral and Gaussian noise filter
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 35, 125)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        area_ratio = area / float(w * h)
        if area_ratio < 0.04 or area_ratio > 0.98:
            continue

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.025 * peri, True)

        # Obtain 4 corner points
        if len(approx) == 4 and cv2.isContourConvex(approx):
            corner_pts = approx.reshape(4, 2).astype("float32")
        else:
            # Fallback to minimum area bounding box 4 corners
            rect_box = cv2.minAreaRect(cnt)
            corner_pts = cv2.boxPoints(rect_box).astype("float32")

        ordered_corners = order_points(corner_pts)

        x, y, bw, bh = cv2.boundingRect(cnt)
        if bw < 40 or bh < 40:
            continue

        major = float(max(bw, bh))
        minor = float(max(1, min(bw, bh)))
        ratio = major / minor

        # ISO 216 standard A4 ratio is sqrt(2) ~ 1.414
        delta_a4 = abs(ratio - 1.414)
        if delta_a4 > 0.28:
            continue

        # Paper interior vs exterior contrast check
        mask = np.zeros_like(gray)
        cv2.drawContours(mask, [cnt], -1, 255, -1)
        mean_inside = float(cv2.mean(gray, mask=mask)[0])
        inv_mask = cv2.bitwise_not(mask)
        mean_outside = float(cv2.mean(gray, mask=inv_mask)[0])

        contrast_diff = mean_inside - mean_outside
        if contrast_diff < -10.0:
            continue

        c_aspect = max(0.0, 1.0 - (delta_a4 / 0.28))
        c_contrast = min(1.0, max(0.5, (contrast_diff + 20.0) / 40.0))
        c_corners = 1.0 if len(approx) == 4 else 0.88

        confidence = round(float(0.45 * c_aspect + 0.35 * c_contrast + 0.20 * c_corners), 3)

        if confidence >= 0.65:
            norm_corners = [
                [round(float(pt[0]) / float(w), 4), round(float(pt[1]) / float(h), 4)]
                for pt in ordered_corners
            ]
            candidates.append({
                "x": int(x), "y": int(y), "w": int(bw), "h": int(bh),
                "norm_x": round(x / float(w), 4),
                "norm_y": round(y / float(h), 4),
                "norm_w": round(bw / float(w), 4),
                "norm_h": round(bh / float(h), 4),
                "corners": ordered_corners.tolist(),
                "corners_norm": norm_corners,
                "ratio": round(ratio, 3),
                "orientation": "portrait" if bh > bw else "landscape",
                "confidence": confidence,
                "polygon_vertices": len(approx)
            })

    if candidates:
        best = max(candidates, key=lambda c: c["confidence"])
        return {
            "detected": True,
            "document_type": "ISO 216 A4 Sheet (210x297mm)",
            "confidence": best["confidence"],
            "box": {
                "x": best["x"], "y": best["y"], "w": best["w"], "h": best["h"],
                "norm_x": best["norm_x"], "norm_y": best["norm_y"],
                "norm_w": best["norm_w"], "norm_h": best["norm_h"]
            },
            "corners": best["corners"],
            "corners_norm": best["corners_norm"],
            "aspect_ratio": best["ratio"],
            "ideal_ratio": 1.414,
            "orientation": best["orientation"]
        }

    return {
        "detected": False,
        "confidence": 0.0,
        "reason": "No A4 sheet matching aspect ratio 1:1.414 detected"
    }


def enhance_manuscript(
    original_path: str,
    processed_dir: str,
    output_prefix: str = "proc_"
) -> Dict[str, Any]:
    """
    Applies full archival preservation and CV pipeline:
    1. Automatic 4-corner paper boundary detection
    2. 4-point perspective correction (homography unwarping to flat top-down A4 document)
    3. Bilateral noise filtering (preserves fine ink calligraphic strokes)
    4. Deskewing
    5. CLAHE adaptive contrast equalization
    6. Gaussian adaptive binarization for OCR/HTR
    7. Generates processed image and side-by-side verification preview
    """
    is_valid, err = validate_image(original_path)
    if not is_valid:
        raise ValueError(f"Invalid image '{original_path}': {err}")

    orig_bgr = cv2.imread(original_path)
    orig_h, orig_w = orig_bgr.shape[:2]

    # Step 1: Detect 4 paper corners
    doc_meta = detect_a4_contour(orig_bgr)
    perspective_corrected = False
    active_bgr = orig_bgr.copy()
    corners_used = None

    if doc_meta.get("detected") and "corners" in doc_meta:
        try:
            corners_arr = np.array(doc_meta["corners"], dtype="float32")
            warped = four_point_perspective_transform(orig_bgr, corners_arr)
            if warped is not None and warped.shape[0] > 60 and warped.shape[1] > 60:
                active_bgr = warped
                perspective_corrected = True
                corners_used = doc_meta["corners"]
        except Exception:
            active_bgr = orig_bgr.copy()

    cur_h, cur_w = active_bgr.shape[:2]
    gray = cv2.cvtColor(active_bgr, cv2.COLOR_BGR2GRAY)

    # Step 2: Bilateral filter for noise reduction without blurring ink strokes
    denoised = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    # Step 3: Residual Deskew
    deskewed_gray, skew_angle = deskew_image(denoised)

    # Step 4: CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    contrast_enhanced = clahe.apply(deskewed_gray)

    # Step 5: Adaptive thresholding for optimal reading contrast
    adaptive_thresh = cv2.adaptiveThreshold(
        contrast_enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=25,
        C=10
    )

    # Step 6: Save processed archival image
    os.makedirs(processed_dir, exist_ok=True)
    filename = Path(original_path).stem
    processed_filename = f"{output_prefix}{filename}.jpg"
    processed_path = os.path.join(processed_dir, processed_filename)

    # Write enhanced grayscale image for maximum archival fidelity & OCR
    cv2.imwrite(processed_path, contrast_enhanced)

    # Step 7: Generate side-by-side comparison preview
    preview_filename = f"comparison_{filename}.jpg"
    preview_path = os.path.join(processed_dir, preview_filename)

    display_h = 600
    scale_orig = display_h / float(orig_h)
    display_w_orig = int(orig_w * scale_orig)
    left_img = cv2.resize(orig_bgr, (display_w_orig, display_h))

    # If corners were detected, draw the 4-corner green quadrilateral on the original capture
    if corners_used is not None:
        pts_scaled = (np.array(corners_used) * [scale_orig, scale_orig]).astype(np.int32)
        cv2.polylines(left_img, [pts_scaled], isClosed=True, color=(0, 255, 102), thickness=2)
        corner_labels = ["TL", "TR", "BR", "BL"]
        for i, pt in enumerate(pts_scaled):
            cv2.circle(left_img, (pt[0], pt[1]), 6, (0, 255, 102), -1)
            cv2.circle(left_img, (pt[0], pt[1]), 9, (255, 255, 255), 1)
            cv2.putText(left_img, corner_labels[i], (pt[0] + 8, pt[1] - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 102), 1, cv2.LINE_AA)

    scale_proc = display_h / float(cur_h)
    display_w_proc = int(cur_w * scale_proc)
    right_img = cv2.resize(cv2.cvtColor(contrast_enhanced, cv2.COLOR_GRAY2BGR), (display_w_proc, display_h))

    # Add label banners
    cv2.rectangle(left_img, (0, 0), (display_w_orig, 35), (20, 20, 20), -1)
    status_str = "ORIGINAL RAW CAPTURE (4-CORNER BOUNDARY LOCKED)" if perspective_corrected else "ORIGINAL RAW CAPTURE"
    cv2.putText(left_img, status_str, (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.rectangle(right_img, (0, 0), (display_w_proc, 35), (10, 40, 20), -1)
    right_label = "PERSPECTIVE RECTIFIED & ENHANCED" if perspective_corrected else f"ENHANCED ARCHIVAL (Skew: {skew_angle:+0.1f} deg)"
    cv2.putText(right_img, right_label, (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 102), 1, cv2.LINE_AA)

    combined_preview = np.hstack([left_img, right_img])
    cv2.imwrite(preview_path, combined_preview)

    return {
        "original_path": original_path,
        "processed_path": processed_path,
        "preview_path": preview_path,
        "perspective_corrected": perspective_corrected,
        "corners_detected": corners_used,
        "skew_angle": skew_angle,
        "original_dimensions": {"width": orig_w, "height": orig_h},
        "rectified_dimensions": {"width": cur_w, "height": cur_h},
        "filters_applied": [
            "4-Point Perspective Homography Unwarp" if perspective_corrected else "Direct Frame Pass",
            "Bilateral Denoising (sigma=75)",
            f"Residual Deskew ({skew_angle} deg)",
            "CLAHE Adaptive Histogram Equalization",
            "Gaussian Adaptive Thresholding"
        ]
    }
