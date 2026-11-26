# yaml-to-fit

Lightweight YAML-to-`.fit` workout compiler built for GPS watches that support structured `.fit` workout files (such as UNA Watch, Garmin, and COROS) without a native workout builder.

## Features

- **Declarative YAML Schema:** Define warm-ups, intervals, repeat blocks, and cool-downs in plain text without proprietary platforms.
- **Multi-Sport Organization:** Group workouts into sport-specific folders (`running`, `cycling`, `walking`, etc.) with automatic cross-checking between folder names and YAML declarations.
- **Open-Target Execution:** Compiles every step with open effort targets so your watch alerts you cleanly on interval transitions without nagging you with live pace alarms.
- **Automated GitHub Releases:** Every push to `main` compiles updated workouts into `.fit` binaries and publishes them under a deterministic CalVer + content-hash release tag (`vYYYY.MM.DD-<hash>`).

## Repository Structure

```text
├── .github/
│   └── workflows/
│       └── build-workouts.yml   # CI pipeline for compiling & publishing GitHub Releases
├── src/
│   └── compile_fit.py           # Python compiler using fit-tool and PyYAML
├── workouts/
│   ├── running/
│   │   └── 2on-2off.yaml
│   ├── cycling/
│   │   └── 2on-2off.yaml
│   └── walking/
│       └── 30m-brisk.yaml
├── .gitignore
├── README.md
└── requirements.txt
```

## Getting Started

### 1. Define a Workout

Create a `.yaml` file inside a sport subdirectory under `workouts/` (for example, `workouts/running/2on-2off.yaml`):

```yaml
name: "2min On 2min Off"
sport: running
sub_sport: track # optional (trail, treadmill, track, road, mountain, gravel, etc.)
steps:
  - type: warmup
    duration: 10m
  - repeat: 7
    steps:
      - type: active
        name: "2:00 On"
        duration: 2m
      - type: rest
        name: "2:00 Off"
        duration: 2m
  - type: cooldown
    duration: 5m
```

> **Sport Validation Rule:** Every YAML file must explicitly include a `sport:` field matching its parent folder name (`running`, `cycling`, `walking`, etc.). If the declared `sport:` does not match the directory name, the file is skipped and flagged in the build summary.

### 2. Compile via GitHub Actions (Recommended)

1. Commit and push your YAML file to the `main` branch (or trigger **Build FIT Workouts** manually from the **Actions** tab).
2. Open the **Releases** page in this repository to view the compiled sport breakdown and download the generated `<sport>-<filename>.fit` assets.
3. Transfer the `.fit` file(s) to your watch's `Workouts` directory via USB or your watch's companion app.

### 3. Compile Locally

Requires Python 3.9 or newer.

```bash
pip install -r requirements.txt
python src/compile_fit.py
```

Compiled `.fit` files are written to `dist/` alongside a summary in `release_notes.md`.

## YAML Schema Reference

### Top-Level Fields

| Field | Required | Description |
| :--- | :--- | :--- |
| `name` | Yes | Workout title displayed on the watch. |
| `sport` | Yes | Must match the parent folder name (`running`, `cycling`, `walking`, `swimming`, `training`, `strength`, `hiking`, `rowing`, `generic`). |
| `sub_sport` | No | Optional sub-sport tag (`trail`, `treadmill`, `track`, `road`, `mountain`, `indoor_cycling`, `gravel`, `strength`). |
| `steps` | Yes | Ordered list of workout steps or `repeat` blocks. |

### Step Fields

| Field | Required | Description |
| :--- | :--- | :--- |
| `type` | Yes | Intensity classification: `warmup`, `active`, `rest`, `recovery`, or `cooldown`. |
| `duration` | Yes | Step length (see supported formats below). |
| `name` | No | Custom step label shown on the watch (defaults to capitalized `type`). |

### Supported Duration Formats

- **Seconds:** `30s`, `90s`
- **Minutes:** `2m`, `10m`
- **Meters:** `400meters`
- **Kilometers:** `0.4km`, `1km`, `5km`
- **Miles:** `1mi`, `3.1mi`
- **Open (Manual Lap Button):** `open`

### Repeat Blocks

Wrap sequential steps inside a `repeat` object to loop them a fixed number of times:

```yaml
- repeat: 5
  steps:
    - type: active
      name: "400m Fast"
      duration: 400meters
    - type: rest
      name: "200m Jog"
      duration: 200meters
```
