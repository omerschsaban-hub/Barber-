"""Small compatibility boundary for the existing STEP geometry route."""
from __future__ import annotations

from pathlib import Path


def extract_step(path: str) -> dict:
    try:
        import cadquery as cq
        result = cq.importers.importStep(str(Path(path)))
        shape = result.val() if hasattr(result, "val") else result
        bb = shape.BoundingBox()
        return {
            "status": "ok",
            "bounding_box": {
                "xmin": float(bb.xmin), "xmax": float(bb.xmax),
                "ymin": float(bb.ymin), "ymax": float(bb.ymax),
                "zmin": float(bb.zmin), "zmax": float(bb.zmax),
            },
            "size_mm": {
                "x": float(bb.xlen), "y": float(bb.ylen), "z": float(bb.zlen)
            },
        }
    except Exception as exc:
        return {"status": "error", "reason": str(exc)[:500]}
