from collections import defaultdict
import datetime
import glob
import os
import re
from typing import Optional
import zipfile
import yaml
from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.workout_message import WorkoutMessage
from fit_tool.profile.messages.workout_step_message import WorkoutStepMessage
from fit_tool.profile.profile_type import (
    FileType,
    Manufacturer,
    Sport,
    SubSport,
    WorkoutStepDuration,
    WorkoutStepTarget,
    Intensity,
)

SPORT_MAP = {
    "running": Sport.RUNNING,
    "cycling": Sport.CYCLING,
    "walking": Sport.WALKING,
    "swimming": Sport.SWIMMING,
    "training": Sport.TRAINING,
    "strength": Sport.TRAINING,
    "hiking": Sport.HIKING,
    "rowing": Sport.ROWING,
    "generic": Sport.GENERIC,
}

SUB_SPORT_MAP = {
    "trail": SubSport.TRAIL,
    "treadmill": SubSport.TREADMILL,
    "track": SubSport.TRACK,
    "road": SubSport.ROAD,
    "mountain": SubSport.MOUNTAIN,
    "indoor_cycling": SubSport.INDOOR_CYCLING,
    "gravel": SubSport.GRAVEL_CYCLING,
    "strength": SubSport.STRENGTH_TRAINING,
}

INTENSITY_MAP = {
    "warmup": Intensity.WARMUP,
    "active": Intensity.ACTIVE,
    "rest": Intensity.REST,
    "recovery": Intensity.RECOVERY,
    "cooldown": Intensity.RECOVERY,
}


def parse_duration(raw: str):
    raw = str(raw).strip().lower()
    if raw == "open":
        return WorkoutStepDuration.OPEN, None
    match = re.match(r"^(\d+(?:\.\d+)?)(s|m|meters|km|mi)$", raw)
    if not match:
        raise ValueError(f"Unsupported duration format: {raw}")
    val, unit = float(match.group(1)), match.group(2)
    if unit == "s":
        return WorkoutStepDuration.TIME, val
    if unit == "m":
        return WorkoutStepDuration.TIME, val * 60.0
    if unit == "meters":
        return WorkoutStepDuration.DISTANCE, val
    if unit == "km":
        return WorkoutStepDuration.DISTANCE, val * 1000.0
    if unit == "mi":
        return WorkoutStepDuration.DISTANCE, val * 1609.34


def make_step(index: int, cfg: dict) -> WorkoutStepMessage:
    step = WorkoutStepMessage()
    step.message_index = index
    step.workout_step_name = cfg.get("name", cfg["type"].capitalize())
    dur_type, dur_val = parse_duration(cfg["duration"])
    step.duration_type = dur_type
    if dur_val is not None:
        if dur_type == WorkoutStepDuration.TIME:
            step.duration_time = dur_val
        else:
            step.duration_distance = dur_val
    step.target_type = WorkoutStepTarget.OPEN
    step.intensity = INTENSITY_MAP.get(cfg["type"].lower(), Intensity.ACTIVE)
    return step


def compile_yaml(yaml_path: str, out_dir: str) -> Optional[str]:
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    folder_sport = os.path.basename(os.path.dirname(yaml_path)).lower()
    declared_sport = str(data.get("sport", "")).strip().lower()

    if not declared_sport or declared_sport != folder_sport:
        print(
            f"SKIPPED {yaml_path}: declared sport '{declared_sport or 'missing'}' "
            f"does not match directory '{folder_sport}'"
        )
        return None

    steps = []
    idx = 0
    for item in data["steps"]:
        if "repeat" in item:
            start_idx = idx
            for sub in item["steps"]:
                steps.append(make_step(idx, sub))
                idx += 1
            rep = WorkoutStepMessage()
            rep.message_index = idx
            rep.duration_type = WorkoutStepDuration.REPEAT_UNTIL_STEPS_CMPLT
            rep.duration_step = start_idx
            rep.target_type = WorkoutStepTarget.OPEN
            rep.target_value = int(item["repeat"])
            steps.append(rep)
            idx += 1
        else:
            steps.append(make_step(idx, item))
            idx += 1

    builder = FitFileBuilder(auto_define=True, min_string_size=50)

    file_id = FileIdMessage()
    file_id.type = FileType.WORKOUT
    file_id.manufacturer = Manufacturer.GARMIN.value
    file_id.product = 0
    file_id.time_created = round(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    file_id.serial_number = 1001
    builder.add(file_id)

    workout = WorkoutMessage()
    workout.workout_name = data["name"]
    workout.sport = SPORT
