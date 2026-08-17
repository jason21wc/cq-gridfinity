# Component Licenses

This project contains components derived from multiple upstream projects with different licenses. The root `LICENSE` file (MIT) covers all original code in this repository. Individual modules may carry additional attribution requirements as detailed below.

---

## MIT Licensed Components (No Additional Restrictions)

These components are MIT licensed. You may use, modify, and redistribute freely with attribution.

| Module | Source | Authors |
|--------|--------|---------|
| `cqgridfinity/gf_obj.py` | cq-gridfinity upstream | Michael Gale |
| `cqgridfinity/gf_box.py` | cq-gridfinity upstream + kennetek spec | Michael Gale, Jason Collier |
| `cqgridfinity/gf_baseplate.py` | cq-gridfinity upstream + kennetek spec | Michael Gale, Jason Collier |
| `cqgridfinity/gf_drawer.py` | cq-gridfinity upstream | Michael Gale |
| `cqgridfinity/gf_helpers.py` | cq-gridfinity upstream | Michael Gale |
| `cqgridfinity/gf_holes.py` | Independent implementation (kennetek spec ref) | Jason Collier |
| `cqgridfinity/gf_divider.py` | Independent implementation | Jason Collier |
| `cqgridfinity/gf_holegrid.py` | Independent implementation | Jason Collier |
| `cqgridfinity/gf_vase.py` | Independent implementation (kennetek spec ref) | Jason Collier |
| `tools/step_audit.py` | Independent implementation | Jason Collier |
| `examples/scripts/` | Independent implementation | Jason Collier |
| `cqgridfinity/constants.py` | cq-gridfinity upstream + kennetek spec | Michael Gale, Jason Collier |
| `cqgridfinity/gridflock/` *(planned)* | Independent implementation (yawkat spec ref, MIT + CC-BY 4.0) | Jason Collier |
| `cqgridfinity/labels/cullenect_label.py` *(planned)* | Independent implementation (CullenJWebb spec ref, MIT) | Jason Collier |
| `cqgridfinity/patterns/` *(planned)* | Independent implementation | Jason Collier |
| `cqgridfinity/lids/` *(planned)* | Independent implementation | Jason Collier |
| `cqgridfinity/holders/` *(planned)* | Independent implementation | Jason Collier |
| `cqgridfinity/drawers/` *(planned)* | Independent implementation | Jason Collier |

### Source References (MIT)

- **cq-gridfinity** by Michael Gale — [github.com/michaelgale/cq-gridfinity](https://github.com/michaelgale/cq-gridfinity) (MIT)
- **gridfinity-rebuilt-openscad** by kennetek — [github.com/kennetek/gridfinity-rebuilt-openscad](https://github.com/kennetek/gridfinity-rebuilt-openscad) (MIT)
- **GridFlock** by yawkat — [github.com/yawkat/gridflock](https://github.com/yawkat/gridflock) (MIT, models CC-BY 4.0)
- **Cullenect Labels** by CullenJWebb — [github.com/CullenJWebb/Cullenect-Labels](https://github.com/CullenJWebb/Cullenect-Labels) (MIT)

---

## CC BY-NC-SA 4.0 Licensed Components

The following module is based on Pred's Gridfinity Rugged Box design, which is licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International.

| Module | Source | Original Author |
|--------|--------|----------------|
| `cqgridfinity/gf_ruggedbox.py` | cq-gridfinity upstream (Pred's design) | Pred (design), Michael Gale (CadQuery implementation) |

**License terms:** You may share and adapt this component under the following terms:
- **Attribution** — Credit Pred as the original designer and Michael Gale for the CadQuery implementation
- **NonCommercial** — You may not use this component for commercial purposes
- **ShareAlike** — Derivative works must use the same license

Full license: [creativecommons.org/licenses/by-nc-sa/4.0/](https://creativecommons.org/licenses/by-nc-sa/4.0/)

---

## CC BY-SA 4.0 Licensed Components

| Module | Source | Original Author |
|--------|--------|----------------|
| `cqgridfinity/gf_ruggedbox_smkent.py` | Independent implementation (smkent design) | smkent (design), Jason Collier (CadQuery implementation) |

> **Why this is a separate module from `gf_ruggedbox.py`:** Pred's rugged box is
> CC BY-**NC**-SA. A derivative of a NonCommercial work stays NonCommercial, so
> extending it would produce a better box that is still commercially blocked.
> The two implementations are deliberately independent and **no code crosses
> between them**. smkent's design is read directly (CC BY-SA permits adaptation
> with attribution and share-alike), unlike the GPL references below.

**License terms:** You may share and adapt under the following terms:
- **Attribution** — Credit smkent as the original designer
- **ShareAlike** — Derivative works must use the same license

Full license: [creativecommons.org/licenses/by-sa/4.0/](https://creativecommons.org/licenses/by-sa/4.0/)

---

## GPL-Isolated References (Spec Reference Only)

The following project is used as a **specification reference only**. No code has been ported, translated, or derived from this codebase. All implementations are independent CadQuery code written from dimensional specifications and feature descriptions.

- **gridfinity_extended_openscad** by ostat — [github.com/ostat/gridfinity_extended_openscad](https://github.com/ostat/gridfinity_extended_openscad) (GPL)

---

## License Pending Confirmation

| Module | Source | Status |
|--------|--------|--------|
| `cqgridfinity/lids/anylid.py` | Independent implementation (rngcntr spec ref) | **BLOCKED** — No GitHub repo (MakerWorld only), license unclear. Implementation cannot begin until license is resolved. |
| `cqgridfinity/gf_labels.py` | **MIT** | Cullenect swappable labels — design by Cullen J Webb ([Cullenect-Labels](https://github.com/CullenJWebb/Cullenect-Labels)), Copyright (c) 2024, MIT. Translated from readable source rather than reconstructed from dimensions |
