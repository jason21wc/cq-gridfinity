#! /usr/bin/env python3
#
# Item dimension presets for Gridfinity holders
#
# Dimensions are nominal item sizes in mm.
# Clearance is added separately by the cutout profile.

BATTERY_PRESETS = {
    "AAA": {"diameter": 10.5, "height": 44.5},
    "AA": {"diameter": 14.5, "height": 50.5},
    "C": {"diameter": 26.2, "height": 50.0},
    "D": {"diameter": 34.2, "height": 61.5},
    "9V": {"width": 17.5, "depth": 26.5, "height": 48.5},
    "CR123A": {"diameter": 17.0, "height": 34.5},
    "18650": {"diameter": 18.6, "height": 65.2},
    "21700": {"diameter": 21.7, "height": 70.2},
    "CR2032": {"diameter": 20.0, "height": 3.2},
    "CR2025": {"diameter": 20.0, "height": 2.5},
}

CARD_PRESETS = {
    "SD": {"width": 24.0, "depth": 2.1, "height": 32.0},
    "microSD": {"width": 11.0, "depth": 1.0, "height": 15.0},
    "CF": {"width": 36.4, "depth": 3.3, "height": 42.8},
    "USB-A": {"width": 12.0, "depth": 4.5, "height": 14.0},
    "USB-C": {"width": 8.4, "depth": 2.6, "height": 10.0},
}

BIT_PRESETS = {
    "hex_quarter": {"diameter": 6.35, "height": 25.0},
    "hex_4mm": {"diameter": 4.0, "height": 25.0},
    "hex_5mm": {"diameter": 5.0, "height": 25.0},
    "hex_6mm": {"diameter": 6.0, "height": 25.0},
    "screwdriver_small": {"diameter": 5.0, "height": 30.0},
    "screwdriver_medium": {"diameter": 7.0, "height": 30.0},
    "drill_3mm": {"diameter": 3.5, "height": 35.0},
    "drill_5mm": {"diameter": 5.5, "height": 40.0},
    "drill_8mm": {"diameter": 8.5, "height": 50.0},
}

ALL_PRESETS = {**BATTERY_PRESETS, **CARD_PRESETS, **BIT_PRESETS}
