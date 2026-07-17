ANALYSIS_VERSION = "rules-1.0.0"

# These are product-level starting thresholds, not medical diagnoses.
# They must be calibrated with real sessions and a rehabilitation specialist.
ROM_TARGET_DEG = {
    "SHOULDER": 90.0,
    "WAIST": 45.0,
    "WRIST": 60.0,
    "LEG": 90.0,
    "UNKNOWN": 90.0,
}

PEAK_SPEED_CAUTION_DPS = {
    "SHOULDER": 240.0,
    "WAIST": 180.0,
    "WRIST": 300.0,
    "LEG": 220.0,
    "UNKNOWN": 240.0,
}

GRADE_SCORE = {
    "PERFECT": 100.0,
    "GOOD": 85.0,
    "NORMAL": 70.0,
    "BAD": 40.0,
    "MISS": 0.0,
}

MIN_ACTIONS_FOR_TREND = 4
MIN_COMPLETENESS_FOR_UP = 0.55
