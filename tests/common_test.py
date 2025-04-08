import os

EXPORT_STEP_FILE_PATH = "./tests/testfiles"

env = dict(os.environ)
SKIP_TEST_BOX = "SKIP_TEST_BOX" in env
SKIP_TEST_RBOX = "SKIP_TEST_RBOX" in env
SKIP_TEST_SPACER = "SKIP_TEST_SPACER" in env
SKIP_TEST_BASEPLATE = "SKIP_TEST_BASEPLATE" in env


def INCHES(x):
    return x * 25.4


def _faces_match(obj, face, n):
    nf = len(obj.faces(face).vals())
    return nf == n


def _edges_match(obj, face, n):
    nf = len(obj.faces(face).edges().vals())
    return abs(nf - n) < 3


def _almost_same(x, y, tol=1e-3):
    if isinstance(x, (list, tuple)):
        return all((abs(xe - ye) < tol for xe, ye in zip(x, y)))
    return abs(x - y) < tol


def _export_files(spec="all"):
    if "EXPORT_STEP_FILES" in env:
        exp_var = env["EXPORT_STEP_FILES"].lower()
        if exp_var == "all":
            return True
        elif exp_var == spec.lower():
            return True
        return False
    return False
