"""Real OpenCascade STEP/BREP extraction.

No text parsing fallback is used for topology. If the OCC runtime is missing,
Fabrient reports unsupported instead of fabricating geometry claims.
"""
from __future__ import annotations
from pathlib import Path

try:
    from OCP.STEPControl import STEPControl_Reader
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.TopAbs import TopAbs_SOLID, TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX
    from OCP.TopExp import TopExp_Explorer
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import brepgprop_VolumeProperties
    OCC_AVAILABLE = True
except Exception:
    OCC_AVAILABLE = False


def extract_step(path: str) -> dict:
    if not OCC_AVAILABLE:
        return {"status": "unsupported", "reason": "OpenCascade runtime is unavailable"}
    p = Path(path)
    if not p.is_file() or p.stat().st_size == 0:
        return {"status": "error", "reason": "STEP file is missing or empty"}

    reader = STEPControl_Reader()
    status = reader.ReadFile(str(p))
    if status != IFSelect_RetDone:
        return {"status": "error", "reason": "OpenCascade could not read the STEP file"}
    if reader.TransferRoots() <= 0:
        return {"status": "error", "reason": "STEP contained no transferable roots"}

    shape = reader.OneShape()

    def count(kind):
        explorer = TopExp_Explorer(shape, kind)
        total = 0
        while explorer.More():
            total += 1
            explorer.Next()
        return total

    props = GProp_GProps()
    brepgprop_VolumeProperties(shape, props)

    return {
        "status": "validated",
        "format": "step",
        "brep": {
            "solids": count(TopAbs_SOLID),
            "faces": count(TopAbs_FACE),
            "edges": count(TopAbs_EDGE),
            "vertices": count(TopAbs_VERTEX),
            "volume_native_units": float(props.Mass()),
        },
        "provenance": {
            "source": "OpenCascade",
            "topology": "kernel-derived",
            "units": "STEP reader/model units; not guessed",
        },
    }
