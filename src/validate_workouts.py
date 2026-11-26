import glob
import os
import re
import sys
import yaml

VALID_SPORTS = {
    "running",
    "cycling",
    "walking",
    "swimming",
    "training",
    "strength",
    "hiking",
    "rowing",
    "generic",
}

VALID_SUB_SPORTS = {
    "trail",
    "treadmill",
    "track",
    "road",
    "mountain",
    "indoor_cycling",
    "gravel",
    "strength",
}

VALID_INTENSITIES = {"warmup", "active", "rest", "recovery", "cooldown"}
DURATION_RE = re.compile(r"^(\d+(?:\.\d+)?)(s|m|meters|km|mi)$")


def validate_step(step: dict, path: str, label: str, errors: list[str]) -> None:
    if not isinstance(step, dict):
        errors.append(f"{path} ({label}): step must be a mapping")
        return

    step_type = step.get("type")
    if not isinstance(step_type, str) or step_type.strip().lower() not in VALID_INTENSITIES:
        errors.append(
            f"{path} ({label}): invalid or missing 'type' ({step_type!r}); "
            f"expected one of {sorted(VALID_INTENSITIES)}"
        )

    raw_dur = step.get("duration")
    if raw_dur is None:
        errors.append(f"{path} ({label}): missing required 'duration'")
    else:
        dur = str(raw_dur).strip().lower()
        if dur != "open" and not DURATION_RE.match(dur):
            errors.append(
                f"{path} ({label}): invalid duration {raw_dur!r} "
                "(use Ns, Nm, Nmeters, Nkm, Nmi, or 'open')"
            )

    if "name" in step and not isinstance(step["name"], str):
        errors.append(f"{path} ({label}): 'name' must be a string")


def validate_file(yaml_path: str) -> list[str]:
    errors: list[str] = []
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        return [f"{yaml_path}: YAML syntax error: {exc}"]

    if not isinstance(data, dict):
        return [f"{yaml_path}: root document must be a YAML mapping"]

    if not isinstance(data.get("name"), str) or not data["name"].strip():
        errors.append(f"{yaml_path}: missing or empty 'name'")

    folder_sport = os.path.basename(os.path.dirname(yaml_path)).lower()
    declared_sport = str(data.get("sport", "")).strip().lower()

    if folder_sport not in VALID_SPORTS:
        errors.append(
            f"{yaml_path}: directory '{folder_sport}' is not a supported sport "
            f"({sorted(VALID_SPORTS)})"
        )
    if not declared_sport:
        errors.append(f"{yaml_path}: missing required 'sport' field")
    elif declared_sport != folder_sport:
        errors.append(
            f"{yaml_path}: declared sport '{declared_sport}' does not match "
            f"parent directory '{folder_sport}'"
        )

    if "sub_sport" in data:
        sub = str(data["sub_sport"]).strip().lower()
        if sub not in VALID_SUB_SPORTS:
            errors.append(
                f"{yaml_path}: unsupported sub_sport {data['sub_sport']!r}; "
                f"expected one of {sorted(VALID_SUB_SPORTS)}"
            )

    steps = data.get("steps")
    if not isinstance(steps, list) or len(steps) == 0:
        errors.append(f"{yaml_path}: 'steps' must be a non-empty list")
        return errors

    for i, item in enumerate(steps, start=1):
        if not isinstance(item, dict):
            errors.append(f"{yaml_path} (step {i}): entry must be a mapping")
            continue

        if "repeat" in item:
            rep = item["repeat"]
            if not isinstance(rep, int) or isinstance(rep, bool) or rep < 1:
                errors.append(f"{yaml_path} (step {i}): 'repeat' must be an integer >= 1")
            sub_steps = item.get("steps")
            if not isinstance(sub_steps, list) or len(sub_steps) == 0:
                errors.append(f"{yaml_path} (step {i}): repeat block requires a non-empty 'steps' list")
            else:
                for j, sub in enumerate(sub_steps, start=1):
                    validate_step(sub, yaml_path, f"step {i}.{j}", errors)
        else:
            validate_step(item, yaml_path, f"step {i}", errors)

    return errors


if __name__ == "__main__":
    files = sorted(glob.glob("workouts/*/*.yaml"))
    if not files:
        print("No workout YAML files found under workouts/*/*.yaml")
        sys.exit(1)

    all_errors: list[str] = []
    for path in files:
        all_errors.extend(validate_file(path))

    if all_errors:
        print("Workout YAML validation failed:\n", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    print(f"Validated {len(files)} workout YAML file(s) successfully.")
