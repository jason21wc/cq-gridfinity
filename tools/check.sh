#!/usr/bin/env bash
#
# Local regression gate. Runs entirely on this machine -- no cloud, no credits.
#
#   tools/check.sh          fast: test suite + audit a representative model set
#   tools/check.sh --full   full: test suite + the entire ship set + audit
#
# Wired to run automatically before `git push` via .githooks/pre-push
# (install with `make hooks-install`). Bypass a single push with
# `git push --no-verify` when you know what you are doing.
#
# Exit non-zero if anything fails, so it can gate a push or a CI job.

set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

CONDA_ENV="${GRIDFINITY_CONDA_ENV:-gridfinity}"
RUN="conda run --no-capture-output -n ${CONDA_ENV}"
MODE="fast"
[ "${1:-}" = "--full" ] && MODE="full"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

fail=0
step() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }

step "1/3  Test suite"
if ! $RUN python -m pytest -q; then
    echo "FAIL: tests"
    fail=1
fi

step "2/3  Generate models (${MODE})"
if [ "$MODE" = "full" ]; then
    $RUN python examples/scripts/generate_shipset.py --out "$WORK" || fail=1
else
    # A deliberately DIVERSE subset, not a numerous one: each model exercises a
    # distinct failure mode, so one defect cannot invalidate the whole batch.
    #   bin+features  -> scoop/label/fillet interaction, and the corrected
    #                    stacking lip (spec conformance covers the numbers)
    #   divided bin   -> divider intersections, where fillet kernels fail
    #   baseplate     -> repeated cylindrical features
    #   lid           -> the short-height boundary family
    #   rugged lid    -> the ShapeFix repair path
    $RUN python - "$WORK" <<'PY' || fail=1
import sys
from pathlib import Path
from cqgridfinity import (GridfinityBaseplate, GridfinityBox,
                          GridfinityRuggedBox, GridfinitySolidBox)

out = Path(sys.argv[1])
models = [
    ("bin_scoop_label", lambda: GridfinityBox(2, 2, 6, scoops=True, labels=True)),
    ("bin_divided",     lambda: GridfinityBox(2, 3, 6, length_div=1, width_div=1)),
    ("baseplate_magnet", lambda: GridfinityBaseplate(3, 3, magnet_holes=True)),
    ("lid",             lambda: GridfinitySolidBox.as_lid(2, 3)),
]
rc = 0
for name, build in models:
    obj = build()
    r = obj.render()
    if not r.val().isValid():
        print(f"  INVALID: {name}"); rc = 1
    obj.save_step_file(str(out / f"{name}.step"))
    print(f"  ok {name}")

# Rugged box lid exercises repair_if_invalid(); the full box is too slow here.
rb = GridfinityRuggedBox(4, 3, 6)
r = rb.render_lid()
if not r.val().isValid():
    print("  INVALID: ruggedbox_lid"); rc = 1
rb.save_step_file(str(out / "ruggedbox_lid.step"))
print("  ok ruggedbox_lid")
sys.exit(rc)
PY
fi

step "3/3  STEP B-Rep audit"
if ! $RUN python tools/step_audit.py "$WORK"; then
    echo "FAIL: audit flagged one or more models"
    fail=1
fi

echo
if [ "$fail" -eq 0 ]; then
    printf '\033[32mAll checks passed (%s).\033[0m\n' "$MODE"
else
    printf '\033[31mChecks FAILED.\033[0m Fix before pushing, or `git push --no-verify` to override.\n'
fi
exit "$fail"
