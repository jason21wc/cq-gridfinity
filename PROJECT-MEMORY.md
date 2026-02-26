# Project Memory

## Decisions Log

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2026-02-22 | Fork cq-gridfinity, don't rewrite | 60-70% coverage already done, MIT license, tedious base geometry already implemented | Final |
| 2026-02-22 | CadQuery over OpenSCAD | Native B-Rep STEP output, exact analytic geometry vs polygon mesh | Final |
| 2026-02-22 | GPL isolation for ostat code | Use as spec reference only, write independent code | Final |
| 2026-02-22 | Phase 1 library-first approach | Geometry must be correct before wrapping in UI | Final |

## Constraints
- **Licensing:** MIT for our code; GPL-isolated from ostat's codebase
- **Dependencies:** CadQuery 2.0+, cq-kit, Python 3.11+
- **OpenCASCADE:** Heavy dependency (~500MB+), affects Docker image size in Phase 3
- **Performance:** Complex models may take 30-60s to generate

## Key Upstream References
- **cq-gridfinity:** github.com/michaelgale/cq-gridfinity (v0.5.7, Nov 2024)
- **kennetek:** github.com/kennetek/gridfinity-rebuilt-openscad (MIT) — primary spec
- **ostat:** github.com/ostat/gridfinity_extended_openscad (GPL) — spec reference only
- **Perplexing Labs:** gridfinity.perplexinglabs.com — feature reference for what users expect

## Phase Gates

### Phase 1: Library + CLI
- [ ] Fork set up and building
- [ ] Dev environment working (CadQuery generates STEP)
- [ ] Tier 1: Advanced baseplates complete
- [ ] Tier 1: Extended bin features complete
- [ ] Tier 2: Item holders, trays, drawers
- [ ] Tier 2: Lids and covers
- [ ] Tier 3: Wall-mount systems
- [ ] All tests passing, CLI entry points working

### Phase 2: Local Web UI
- [ ] FastAPI backend wrapping library
- [ ] Three.js 3D preview in browser
- [ ] Parameter forms per component type
- [ ] Local deployment working

### Phase 3: Deploy
- [ ] Dockerized
- [ ] Job queue for render requests
- [ ] Caching layer
- [ ] Deployed to VPS/Railway/Fly.io
