from __future__ import annotations

import base64
import binascii
import hashlib
import math

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .real_cv_sim2real import _line, _px, REAL_CV_VERSION

router = APIRouter(prefix="/v1/cv", tags=["cv-json"])
CV_JSON_VERSION = "real-cv-json-2.1"


class RealCVJsonRequest(BaseModel):
    image_base64: str = Field(min_length=1)
    reference_length_mm: float = Field(gt=0)
    reference_line: str
    target_line: str
    reference_uncertainty_mm: float = Field(default=0.0, ge=0)
    min_image_side_px: int = Field(default=320, ge=64, le=10000)
    min_contrast: float = Field(default=8.0, ge=0, le=128)
    min_sharpness: float = Field(default=20.0, ge=0, le=100000)


def _decode_image(value: str) -> bytes:
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(422, "image_base64 must be valid base64") from exc
    if len(raw) > 10_000_000:
        raise HTTPException(413, "Image exceeds 10 MB")
    return raw


def _image_quality(image: np.ndarray) -> dict:
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    contrast = float(np.std(gray))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return {
        "contrast_std": contrast,
        "sharpness_laplacian_variance": sharpness,
        "width_px": int(gray.shape[1]),
        "height_px": int(gray.shape[0]),
    }


def _validate_quality(image: np.ndarray, x: RealCVJsonRequest) -> dict:
    quality = _image_quality(image)
    if min(quality["width_px"], quality["height_px"]) < x.min_image_side_px:
        raise HTTPException(422, f"Image is too small for reliable measurement; minimum side is {x.min_image_side_px}px")
    if quality["contrast_std"] < x.min_contrast:
        raise HTTPException(422, "Image contrast is too low for reliable CV measurement")
    if quality["sharpness_laplacian_variance"] < x.min_sharpness:
        raise HTTPException(422, "Image sharpness is too low for reliable CV measurement")
    return quality


@router.post("/measure-real-json")
def measure_real_json(x: RealCVJsonRequest):
    raw = _decode_image(x.image_base64)
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise HTTPException(415, "Unsupported image format")
    quality = _validate_quality(image, x)
    ref, target = _line(x.reference_line, "reference_line"), _line(x.target_line, "target_line")
    ref_px, target_px = _px(ref), _px(target)
    if ref_px < 5 or target_px < 5:
        raise HTTPException(422, "Reference and target lines must be at least 5 pixels long")
    mm_per_px = x.reference_length_mm / ref_px
    px_sigma = math.sqrt(0.5**2 + 0.5**2)
    measurement_mm = target_px * mm_per_px
    relative_pixel_uncertainty = math.sqrt(
        (px_sigma / ref_px) ** 2 + (px_sigma / target_px) ** 2
    )
    sigma = math.sqrt(
        (measurement_mm * relative_pixel_uncertainty) ** 2
        + x.reference_uncertainty_mm**2
    )
    return {
        "status": "measured",
        "measurement_mm": measurement_mm,
        "uncertainty_1sigma_mm": sigma,
        "interval_95_mm": [measurement_mm - 1.96 * sigma, measurement_mm + 1.96 * sigma],
        "quality": quality,
        "quality_gate": "pass",
        "scale": {"reference_length_mm": x.reference_length_mm, "reference_pixels": ref_px, "mm_per_pixel": mm_per_px, "perspective_corrected": False},
        "image": {"width_px": int(image.shape[1]), "height_px": int(image.shape[0]), "sha256": hashlib.sha256(raw).hexdigest()},
        "provenance": {"source": "user_image", "algorithm": "explicit-reference-pixel-scale", "cv_version": REAL_CV_VERSION, "cv_json_version": CV_JSON_VERSION, "ground_truth_mm": False, "claim_boundary": "Physical reference establishes scale; CV measurement is evidence, not final physical acceptance."},
    }


@router.post("/detect-line-candidates-json")
def detect_line_candidates_json(payload: dict):
    raw = _decode_image(str(payload.get("image_base64", "")))
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise HTTPException(415, "Unsupported image format")
    quality = _image_quality(image)
    if min(quality["width_px"], quality["height_px"]) < 160:
        raise HTTPException(422, "Image is too small for line detection")
    edges = cv2.Canny(image, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50, minLineLength=max(20, image.shape[1] // 10), maxLineGap=8)
    candidates = []
    if lines is not None:
        for row in lines[:200]:
            p1, p2 = [int(row[0][0]), int(row[0][1])], [int(row[0][2]), int(row[0][3])]
            candidates.append({"p1": p1, "p2": p2, "length_px": float(math.dist(p1, p2))})
    candidates.sort(key=lambda item: item["length_px"], reverse=True)
    return {"status": "candidates", "candidates": candidates[:50], "requires_user_selection": True, "quality": quality, "provenance": {"algorithm": "opencv-canny-hough", "cv_version": REAL_CV_VERSION, "ground_truth_mm": False}}