from __future__ import annotations

import os
import tempfile
from pathlib import Path


def extract_step(raw: bytes) -> dict:
    """Extract real STEP topology through CadQuery/OpenCascade.

    No unit conversion is guessed. The STEP file's declared units are retained
    as reported by the kernel where available; callers must not label values mm
    unless the source declares mm.
    """
    try:
        import cadquery as cq
    except Exception as exc:
        raise ImportError("CadQuery/OpenCascade is unavailable") from exc

    fd, path = tempfile.mkstemp(suffix=".step")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
        assembly = cq.importers.importStep(path)
        solids = assembly.solids().vals()
        if not solids:
            raise ValueError("STEP contains no solid bodies")

        boxes = [s.BoundingBox() for s in solids]
        xmin = min(b.xmin for b in boxes); ymin = min(b.ymin for b in boxes); zmin = min(b.zmin for b in boxes)
        xmax = max(b.xmax for b in boxes); ymax = max(b.ymax for b in boxes); zmax = max(b.zmax for b in boxes)
        faces = sum(len(s.Faces()) for s in solids)
        edges = sum(len(s.Edges()) for s in solids)
        vertices = sum(len(s.Vertices()) for s in solids)
        volume = sum(float(s.Volume()) for s in solids)

        return {
            "status": "extracted",
            "kernel": "OpenCascade via CadQuery",
            "units": "source STEP units; no conversion guessed",
            "solid_count": len(solids),
            "topology": {"faces": faces, "edges": edges, "vertices": vertices},
            "volume_source_units3": volume,
            "bounding_box": {
                "min": [xmin, ymin, zmin],
                "max": [xmax, ymax, zmax],
                "size": [xmax-xmin, ymax-ymin, zmax-zmin],
            },
            "feature_extraction": {
                "status": "kernel_topology",
                "features": [
                    {"type": "solid", "count": len(solids)},
                    {"type": "face", "count": faces},
                    {"type": "edge", "count": edges},
                    {"type": "vertex", "count": vertices},
                ],
            },
            "provenance": {"source": "user_uploaded_STEP", "method": "OpenCascade/CadQuery", "synthetic": False},
        }
    finally:
        Path(path).unlink(missing_ok=True)
