from __future__ import annotations

import base64
import hashlib
import math

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .real_cv_sim2real import _line, _quad, _ordered_quad, _px, REAL_CV_VERSION

router = APIRouter(prefix="/v1", tags=["real-cv-mcp"])

class CVMeasureJSON(BaseModel):
    image_base64: str = Field(min_length=16)
    reference_length_mm: float = Field(gt=0)
    reference_line: str
    target_line: str
    reference_uncertainty_mm: float = Field(default=0.0, ge=0)
    reference_quad: str | None = None

class CVDetectJSON(BaseModel):
    image_base64: str = Field(min_length=16)


def _decode(value: str) -> tuple[bytes, np.ndarray]:
    try:
        raw = base64.b64decode(value, validate=True)
    except Exception as exc:
        raise HTTPException(422, "image_base64 must be valid base64") from exc
    if len(raw) > 10_000_000:
        raise HTTPException(413, "Image exceeds 10 MB")
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise HTTPException(415, "Unsupported image format")
    return raw, image

@router.post("/cv/measure-real-json")
def measure_real_json(x: CVMeasureJSON):
    raw, image = _decode(x.image_base64)
    ref, target = _line(x.reference_line, "reference_line"), _line(x.target_line, "target_line")
    ref_px, target_px = _px(ref), _px(target)
    if ref_px < 2 or target_px < 2:
        raise HTTPException(422, "Reference and target lines must be at least 2 pixels long")
    quad = _quad(x.reference_quad)
    if quad is not None:
        q = _ordered_quad(quad)
        dst = np.array([[0, 0], [x.reference_length_mm, 0], [x.reference_length_mm, x.reference_length_mm], [0, x.reference_length_mm]], dtype=np.float32)
        H = cv2.getPerspectiveTransform(q, dst)
        target_rect = cv2.perspectiveTransform(target.reshape(1, -1, 2).astype(np.float32), H)[0]
        measurement_mm = _px(target_rect)
        sigma = math.sqrt(0.5 + x.reference_uncertainty_mm**2)
        method = "explicit-reference-homography"
    else:
        mm_per_px = x.reference_length_mm / ref_px
        measurement_mm = target_px * mm_per_px
        px_sigma = math.sqrt(0.5**2 + 0.5**2)
        sigma = math.sqrt((measurement_mm * math.sqrt((px_sigma / ref_px) ** 2 + (px_sigma / target_px) ** 2)) ** 2 + x.reference_uncertainty_mm**2)
        method = "explicit-reference-pixel-scale"
    return {"status": "measured", "measurement_mm": measurement_mm, "uncertainty_1sigma_mm": sigma, "interval_95_mm": [measurement_mm - 1.96 * sigma, measurement_mm + 1.96 * sigma], "image": {"width_px": int(image.shape[1]), "height_px": int(image.shape[0]), "sha256": hashlib.sha256(raw).hexdigest()}, "provenance": {"source": "mcp_image_base64", "algorithm": method, "cv_version": REAL_CV_VERSION, "ground_truth_mm": False}}

@router.post("/cv/detect-line-candidates-json")
def detect_lines_json(x: CVDetectJSON):
    raw, image = _decode(x.image_base64)
    edges = cv2.Canny(image, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50, minLineLength=max(20, image.shape[1] // 10), maxLineGap=8)
    candidates = []
    if lines is not None:
        for row in lines[:200]:
            p1, p2 = [int(row[0][0]), int(row[0][1])], [int(row[0][2]), int(row[0][3])]
            candidates.append({"p1": p1, "p2": p2, "length_px": float(math.dist(p1, p2))})
    candidates.sort(key=lambda x: x["length_px"], reverse=True)
    return {"status": "candidates", "candidates": candidates[:50], "requires_user_selection": True, "image_sha256": hashlib.sha256(raw).hexdigest(), "provenance": {"algorithm": "opencv-canny-hough", "cv_version": REAL_CV_VERSION}}
