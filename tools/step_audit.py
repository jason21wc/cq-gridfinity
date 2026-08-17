#!/usr/bin/env python
"""STEP B-Rep quality audit (ROADMAP.md DoD-4).

The project's entire value proposition is *native B-Rep* STEP output rather than
a triangle mesh wearing a .step extension. That claim is machine-checkable, and
the decisive test is the **surface-type census**:

    Genuine B-Rep  : a magnet hole is ONE cylindrical face.
    Tessellation   : a magnet hole is HUNDREDS of tiny planar facets.

The distinction is unambiguous and needs no human eye. This tool reports, per
model: solid/face/edge counts, validity, the surface-type histogram, bounding
box, and file size -- then flags anything that smells tessellated.

What this tool CANNOT tell you: whether Shapr3D or Fusion 360 imports the file
without complaint, and whether the resulting body is pleasant to edit. That is
DoD-3 and needs a human.

Usage:
    python tools/step_audit.py FILE_OR_DIR [FILE_OR_DIR ...]
    python tools/step_audit.py examples/output --json audit.json
    python tools/step_audit.py ~/Downloads/gridfinity-shipset --quiet

Exit status is non-zero if any model fails validity or is flagged as a
tessellation suspect, so this can gate CI.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepCheck import BRepCheck_Analyzer

# Surface kinds that carry real CAD intent. A model built from these is
# editable downstream; a model built only from planes probably is not.
ANALYTIC = ("Plane", "Cylinder", "Cone", "Sphere", "Torus")

# A model with this many faces that is almost entirely planar is very likely
# tessellated geometry rather than B-Rep. Gridfinity parts always contain
# cylinders (holes) or curved fillets, so ~100% planar at high face count is
# not a legitimate outcome for this project.
TESSELLATION_FACE_FLOOR = 400
TESSELLATION_PLANAR_FRAC = 0.98


def _surface_kind(face) -> str:
    """Return the OpenCASCADE surface type of a face as a short string."""
    # GeomAbs_Cylinder -> "Cylinder"
    return str(BRepAdaptor_Surface(face.wrapped).GetType()).rsplit("_", 1)[-1]


def audit_shape(shape, label: str = "<shape>") -> dict:
    """Audit a CadQuery Shape or Workplane. Returns a result dict."""
    if isinstance(shape, cq.Workplane):
        shape = shape.val()

    faces = shape.Faces()
    histogram: dict[str, int] = {}
    for f in faces:
        kind = _surface_kind(f)
        histogram[kind] = histogram.get(kind, 0) + 1

    n_faces = len(faces)
    n_planar = histogram.get("Plane", 0)
    planar_frac = (n_planar / n_faces) if n_faces else 0.0
    n_analytic = sum(v for k, v in histogram.items() if k in ANALYTIC)

    try:
        bb = shape.BoundingBox()
        bbox = [round(bb.xlen, 3), round(bb.ylen, 3), round(bb.zlen, 3)]
    except Exception:
        bbox = None

    valid = BRepCheck_Analyzer(shape.wrapped).IsValid()

    flags = []
    notes = []
    if not valid:
        flags.append("INVALID")
    if n_faces >= TESSELLATION_FACE_FLOOR and planar_frac >= TESSELLATION_PLANAR_FRAC:
        flags.append("TESSELLATION_SUSPECT")
    if n_faces and n_analytic / n_faces < 0.5:
        # Majority free-form surfaces is legitimate for a lofted shape, and
        # for ENGRAVED TEXT -- glyph outlines are genuinely curves. It is a
        # NOTE rather than a failure: this tool's real job is catching a
        # planar facet explosion (triangles wearing a .step extension), and a
        # B-spline surface is the opposite of that. Failing CI on legitimate
        # text would just train people to ignore the tool.
        notes.append("MOSTLY_FREEFORM")
    if not n_faces:
        flags.append("EMPTY")

    return {
        "label": label,
        "valid": valid,
        "solids": len(shape.Solids()),
        "shells": len(shape.Shells()),
        "faces": n_faces,
        "edges": len(shape.Edges()),
        "vertices": len(shape.Vertices()),
        "planar_fraction": round(planar_frac, 4),
        "analytic_fraction": round(n_analytic / n_faces, 4) if n_faces else 0.0,
        "surface_types": dict(sorted(histogram.items(), key=lambda kv: -kv[1])),
        "bbox_mm": bbox,
        "flags": flags,
        "notes": notes,
    }


def audit_file(path: Path) -> dict:
    """Import a STEP file and audit it."""
    try:
        wp = cq.importers.importStep(str(path))
    except Exception as exc:  # noqa: BLE001 - report, don't crash the batch
        return {
            "label": path.name,
            "path": str(path),
            "valid": False,
            "flags": ["IMPORT_FAILED"],
            "notes": [],
            "error": f"{type(exc).__name__}: {exc}",
        }

    result = audit_shape(wp, label=path.name)
    result["path"] = str(path)
    size = path.stat().st_size
    result["file_bytes"] = size
    result["file_kb"] = round(size / 1024, 1)
    if result["faces"]:
        result["bytes_per_face"] = round(size / result["faces"])
    return result


def _collect(targets: list[str]) -> list[Path]:
    files: list[Path] = []
    for t in targets:
        p = Path(t).expanduser()
        if p.is_dir():
            files.extend(sorted(p.rglob("*.step")))
            files.extend(sorted(p.rglob("*.stp")))
        elif p.is_file():
            files.append(p)
        else:
            print(f"warning: no such path: {p}", file=sys.stderr)
    return files


def _fmt_types(types: dict, limit: int = 4) -> str:
    items = list(types.items())[:limit]
    s = " ".join(f"{k[:4]}:{v}" for k, v in items)
    if len(types) > limit:
        s += " ..."
    return s


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("targets", nargs="+", help="STEP file(s) or directory(ies)")
    ap.add_argument("--json", dest="json_out", help="write full results to JSON")
    ap.add_argument("--quiet", action="store_true", help="only print flagged models")
    args = ap.parse_args(argv)

    files = _collect(args.targets)
    if not files:
        print("No STEP files found.", file=sys.stderr)
        return 2

    results = [audit_file(f) for f in files]

    hdr = f"{'model':<44} {'faces':>6} {'plan%':>6} {'kB':>7}  surfaces / flags"
    print(hdr)
    print("-" * len(hdr))

    failed = 0
    for r in results:
        flagged = bool(r.get("flags"))  # notes do not fail the gate
        if flagged:
            failed += 1
        if args.quiet and not flagged:
            continue
        if "IMPORT_FAILED" in r.get("flags", []):
            print(f"{r['label'][:44]:<44} {'—':>6} {'—':>6} {'—':>7}  {r['error']}")
            continue
        tail = _fmt_types(r["surface_types"])
        if flagged:
            tail += "  [" + ",".join(r["flags"]) + "]"
        if r.get("notes"):
            tail += "  (" + ",".join(r["notes"]) + ")"
        print(
            f"{r['label'][:44]:<44} {r['faces']:>6} "
            f"{r['planar_fraction'] * 100:>5.1f}% {r['file_kb']:>7.1f}  {tail}"
        )

    print("-" * len(hdr))
    ok = len(results) - failed
    print(f"{len(results)} model(s): {ok} clean, {failed} flagged")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(results, indent=2))
        print(f"wrote {args.json_out}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
