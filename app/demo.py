from __future__ import annotations

import time


def build_demo_session() -> dict:
    now = int(time.time() * 1000)
    actions = []
    grades = ["GOOD", "PERFECT", "GOOD", "NORMAL", "GOOD", "GOOD"]
    roms = [74.0, 80.0, 78.0, 72.0, 75.0, 73.0]
    for index, (grade, rom) in enumerate(zip(grades, roms), start=1):
        start = now + index * 2_500
        duration = 1_100 + index * 35
        actions.append(
            {
                "action_id": str(index),
                "action_type": "ATTACK",
                "direction": "FORWARD",
                "started_at_ms": start,
                "ended_at_ms": start + duration,
                "result": True,
                "grade": grade,
                "rom_deg": rom,
                "peak_angular_velocity_dps": 118 + index * 4,
                "hold_time_ms": 180,
                "samples": [
                    {"timestamp_ms": start, "angle_deg": 0, "angular_velocity_dps": 0},
                    {"timestamp_ms": start + 300, "angle_deg": rom * 0.35, "angular_velocity_dps": 88},
                    {"timestamp_ms": start + 650, "angle_deg": rom, "angular_velocity_dps": 126},
                    {"timestamp_ms": start + duration, "angle_deg": 5, "angular_velocity_dps": 18},
                ],
            }
        )
    return {
        "schema_version": "1.0",
        "history_id": "demo-session-001",
        "user_id": "demo-user",
        "game_id": "ADVENTURE_FIGHT",
        "game_name": "ReFit 전투 재활",
        "game_version": "1.0.0",
        "primary_part": "SHOULDER",
        "side": "BOTH",
        "difficulty": 2,
        "started_at_ms": now,
        "ended_at_ms": now + 20_000,
        "action_count": len(actions),
        "success_count": len(actions),
        "fail_count": 0,
        "profile": {
            "age_group": "20_29",
            "height_cm": 175.5,
            "weight_kg": 72.3,
            "dominant_hand": "R",
            "diagnosis_tags": ["ROUND_SHOULDER"],
            "pain_baseline_0_10": 2,
        },
        "self_report": {
            "pain_before_0_10": 2,
            "pain_after_0_10": 3,
            "fatigue_after_0_10": 4,
            "swelling": False,
        },
        "actions": actions,
    }
