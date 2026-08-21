"""Authoritative STEP/BREP extraction with an OCCT-backed kernel.

Topology claims come only from the CAD kernel. CadQuery 2.6.0 is the
supported OCCT-backed runtime and is also used to produce a deterministic
triangle mesh for the browser viewer. No point-cloud approximation is used.
"""
from __future__ import annotations

from pathlib import Path

OCC_AVAILABLE = False
_BACKEND = "unavailable"
cq = None

try:
    import cadquery as cq
    OCC_AVAILABLE = True
    _BACKEND = "CadQuery/OCCT"
except Exception:
    pass


def _mesh_from_shape(shape) -> dict:
    """Return a bounded, deterministic triangle mesh from an OCCT shape."""
    vertices, triangles = shape.tessellate(0.15, 0.5)
    if not vertices or not triangles:
        return {"vertices": [], "triangles": [], "vertex_count": 0, "triangle_count": 0}
    if len(vertices) > 100_000 or len(triangles) > 200_000:
        raise ValueError("STEP tessellation exceeds visualization mesh limit")
    verts = [[float(v.x), float(v.y), float(v.z)] for v in vertices]
    tris = [[int(t[0]), int(t[1]), int(t[2])] for t in triangles]
    return {
        "vertices": verts,
        "triangles": tris,
        "vertex_count": len(verts),
        "triangle_count": len(tris),
        "tolerance": {"linear": 0.15, "angular": 0.5},
    }


def extract_step(path: str) -> dict:
    if not OCC_AVAILABLE:
        return {"status": "unsupported", "reason": "No OCCT-backed CAD runtime is available"}
    p = Path(path)
    if not p.is_file() or p.stat().st_size == 0:
        return {"status": "error", "reason": "STEP file is missing or empty"}
    try:
        shape = cq.importers.importStep(str(p))
        solids = shape.solids().vals() if hasattr(shape, "solids") else []
        valid = all(s.isValid() for s in solids) if solids else False
        if not solids or not valid:
            return {"status": "error", "reason": "STEP contained no valid solid topology"}

        model_shape = shape.val()
        bb = model_shape.BoundingBox()
        mesh = _mesh_from_shape(model_shape)
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
            "mesh": mesh,
            "provenance": {
                "source": _BACKEND,
                "topology": "kernel-derived",
                "topology_verified": True,
                "mesh": "kernel tessellation; deterministic parameters",
                "units": "STEP model units; not guessed",
            },
        }
    except Exception as exc:
        return {"status": "error", "reason": f"CAD kernel STEP extraction failed: {exc}", "provenance": {"source": _BACKEND}}
