"""Authoritative STEP/BREP extraction with an OCCT-backed kernel.

Topology claims come only from the CAD kernel. When the direct OCP imports are
unavailable, CadQuery's bundled OCCT integration is used. Point parsing is
never used as a substitute for topology.
"""
from __future__ import annotations

from pathlib import Path

OCC_AVAILABLE = False
_BACKEND = "unavailable"

try:
    from OCP.STEPControl import STEPControl_Reader
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.TopAbs import TopAbs_SOLID, TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX
    from OCP.TopExp import TopExp_Explorer
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import brepgprop_VolumeProperties
    OCC_AVAILABLE = True
    _BACKEND = "OCP"
except Exception:
    try:
        import cadquery as cq
        OCC_AVAILABLE = True
        _BACKEND = "CadQuery/OCCT"
    except Exception:
        cq = None


def _cadquery_extract(path: Path) -> dict:
    shape = cq.importers.importStep(str(path))
    solids = shape.solids().vals() if hasattr(shape, "solids") else []
    valid = all(s.isValid() for s in solids) if solids else False
    if not solids:
        return {"status": "error", "reason": "STEP contained no valid solid topology"}
    bb = shape.val().BoundingBox()
    return {
        "status": "validated",
        "format": "step",
        "brep": {
            "solids": len(solids),
            "faces": sum(len(s.Faces()) for s in solids),
            "edges": sum(len(s.Edges()) for s in solids),
            "vertices": sum(len(s.Vertices()) for s in solids),
            "volume_native_units": float(sum(s.Volume() for s in solids)),
        },
        "bounding_box": {
            "size": [float(bb.xlen), float(bb.ylen), float(bb.zlen)],
            "units": "STEP model units; not guessed",
        },
        "provenance": {"source": _BACKEND, "topology": "kernel-derived", "units": "STEP model units; not guessed"},
    }


def extract_step(path: str) -> dict:
    if not OCC_AVAILABLE:
        return {"status": "unsupported", "reason": "No OCCT-backed CAD runtime is available"}
    p = Path(path)
    if not p.is_file() or p.stat().st_size == 0:
        return {"status": "error", "reason": "STEP file is missing or empty"}
    try:
        if _BACKEND == "CadQuery/OCCT":
            return _cadquery_extract(p)

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
        try:
            from OCP.Bnd import Bnd_Box
            from OCP.BRepBndLib import brepbndlib_Add
            box = Bnd_Box()
            brepbndlib_Add(shape, box)
            xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
            bbox = {"size": [float(xmax-xmin), float(ymax-ymin), float(zmax-zmin)], "units": "STEP model units; not guessed"}
        except Exception:
            bbox = None
        return {"status":"validated","format":"step","brep":{"solids":count(TopAbs_SOLID),"faces":count(TopAbs_FACE),"edges":count(TopAbs_EDGE),"vertices":count(TopAbs_VERTEX),"volume_native_units":float(props.Mass())},"bounding_box":bbox,"provenance":{"source":"OCP","topology":"kernel-derived","units":"STEP model units; not guessed"}}
    except Exception as exc:
        return {"status": "error", "reason": f"CAD kernel STEP extraction failed: {exc}", "provenance": {"source": _BACKEND}}
