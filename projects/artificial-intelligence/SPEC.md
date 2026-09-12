# Multi-Object Tracking and Directional Counting System for Fixed-Camera Video Analytics

## 1. Project Overview

**Title:** Multi-Object Tracking and Directional Counting System for Fixed-Camera Video Analytics

**Objective:** Build a complete, reproducible, production-oriented video analytics pipeline that:

- Detects objects of interest (primarily `person` and `car`, extensible to any COCO class) in a recorded video from a fixed camera using a pretrained YOLO model.
- Assigns persistent Track IDs via multi-object tracking (primary tracker: ByteTrack).
- Detects crossings of one or more user-defined virtual counting lines.
- Determines direction (IN / OUT) for each crossing.
- Counts objects per class and direction while preventing duplicate counting.
- Logs every crossing event with rich metadata.
- Produces an annotated output video and structured evaluation-ready outputs.

The system is designed as a clean, modular research codebase suitable for an academic magazine article and a public GitHub repository. Code quality, documentation, configuration management, reproducibility, and evaluation rigor must meet global university / research-lab standards.

**Input**

- Single recorded video file from a fixed (non-moving) camera.
- Configuration file controlling video path, classes, confidence, counting line geometry (one or more lines), tracker parameters, etc.
- For production batch runs: one or more clips plus `configs/production.yaml` (see §17).

**Primary Outputs**

1. Annotated video (bounding boxes + class + Track ID + counting line(s) + live IN/OUT counters).
2. Event log (CSV) containing every validated crossing.
3. Final count summary (per-class, per-line IN / OUT totals printed after `run()` and stored in `PipelineController.stats`).
4. Evaluation report materials when ground truth is available (`evaluation_summary.csv`, `evaluation_matches.csv`).
5. Optional production manifest JSON for multi-clip runs (`outputs/production/production_manifest_*.json`).

**Non-Goals (Explicit Scope Boundaries)**

- No training or fine-tuning of the detector.
- No online / live camera streaming in the core pipeline (recorded video only).
- No multi-camera fusion or 3D tracking.
- No guaranteed re-identification across track ID switches — this is treated as a known, documented limitation (see §7.4 and §13), not a solved problem.
- Re-identification (ReID) and advanced trajectory analytics remain optional stretch goals only.
- No hard real-time performance guarantee: the pipeline processes recorded video offline, so throughput (FPS) is reported as a metric, not enforced as a constraint.

### 1.1 Implementation Status (As-Built)

The v1 core pipeline is implemented under the Python package `mot-counting` (`src/mot_counting/`). Locked design decisions in this document remain in force; the following describes what the code actually does today.

**Implemented**

- YAML + Pydantic v2 configuration (`AppConfig` in `config.py`).
- Manual composition root (`build_pipeline`) wiring YOLO26, ByteTrack, CrossingLogic, CSV repository, OpenCV visualizer, frame source, Observer `Subject`.
- `PipelineController` loop, line-geometry fail-fast, `RunStats`, annotated `cv2.VideoWriter` (`mp4v`).
- Custom crossing state machine keyed by `(track_id, line_id)`.
- Evaluation matcher and CLI (`src/mot_counting/evaluation.py`, `scripts/evaluate.py`).
- Ground-truth annotator (`scripts/annotate_ground_truth.py`).
- Production multi-clip runner (`scripts/run_production.py`).
- Docker CPU and GPU Compose files; YOLO weights baked at image build time.
- Unit tests under `tests/unit/`, integration test `tests/integration/test_full_pipeline.py`, annotator tests at `tests/test_annotate_ground_truth.py`.
- CI documented for this project: live workflow is `.github/workflows/ai-ci.yml` at the **magazine-03 repository root** (this package lives in `projects/artificial-intelligence/`).

**Not implemented / remaining gaps vs original design**

- BoT-SORT: `tracker.type: botsort` is accepted by the Pydantic schema and `TrackerFactory`, then raises `NotImplementedError`.
- Trajectory trails: `visualization.draw_trails` exists in YAML but `OpenCvVisualizer` does not draw trails.
- `CrossingEvent.video_name` is never populated by `CrossingLogic` (always `None` in pipeline CSVs). The GT annotator *does* write `video_name`.
- Logging level is not a YAML field; `composition_root.build_pipeline` calls `logging.basicConfig(level=INFO)`.
- No `utils/metrics.py` — evaluation lives in `evaluation.py`.
- No issue template under this project's `.github/ISSUE_TEMPLATE/`.
- GitHub Actions YAML is not stored inside this subdirectory; see `.github/workflows/README.md` in this folder.

---

## 2. Project Roles & Responsibilities

| Role | Name | Primary Responsibilities |
|---|---|---|
| **Project Lead / Core Implementer** | **Mostafa** | Core pipeline architecture and implementation, Detection–Tracking integration, Crossing Logic implementation, configuration system, module integration, code quality, technical coordination of implementation, and repository structure |
| **AI Section Lead / Evaluation & Quality Lead** | **Armila** | Project scope and technical requirements definition, evaluation framework design and implementation, event matching and metrics implementation, results and failure analysis, final system validation, technical review of major design decisions, and PR review and merge approval |
| **Developer** | **Farzad** | Implementation and testing of assigned project modules |
| **Developer** | **Amirmohammad** | Implementation and testing of assigned project modules |

**Deadline:** the project must be complete by **September 1, 2026** (~10 days from project kickoff).

---

## 3. Core Technical Stack (Locked Decisions)

| Component | Choice | Notes |
|---|---|---|
| Package | **`mot-counting` 0.1.0** | setuptools, `src/` layout (`[tool.setuptools.packages.find] where = ["src"]`). |
| Object Detector | **YOLO26 (Ultralytics), `yolo26m` variant** | Default for development, evaluation, and `configs/production.yaml`. `yolo26n` is used by `configs/ci.yaml`. Supported variant strings: `yolo26n`, `yolo26s`, `yolo26m`, `yolo26l`, `yolo26x`. YOLO11 remains a late, optional, non-blocking comparison. |
| Tracker (Primary) | ByteTrack via `ultralytics.trackers.byte_tracker.BYTETracker` | Default path. Config hyperparameters: `track_thresh=0.5`, `match_thresh=0.8`, `track_buffer=30`. Wrapper also sets `track_high_thresh=track_thresh`, `track_low_thresh=0.1`, `new_track_thresh=track_thresh+0.1`, `fuse_score=True` (not YAML-exposed). |
| Tracker (Optional) | BoT-SORT | Stretch goal. Config may set `tracker.type: botsort`; factory raises `NotImplementedError`. |
| Video I/O & Drawing | OpenCV (`opencv-python`) | `OpenCvFrameSource`, `OpenCvVisualizer`, `cv2.VideoWriter` fourcc `mp4v`. |
| Configuration | **YAML + Pydantic v2** | `load_config(path)` → `AppConfig`. Relative config paths resolve from the **current working directory**, not automatically from the package root. |
| Event Storage | CSV (UTF-8, header row) | `CsvEventRepository`; `InMemoryEventRepository` for tests. |
| Crossing Logic | Custom `CrossingLogic` | Do not use Supervision `LineZone` as the production path. |
| Language / Runtime | Python 3.10+ | Native install recommends 3.12. CPU Docker image: `python:3.12-slim`. GPU Docker image: Ubuntu 22.04 Python 3.10 on `nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04`. |
| Packaging | `pyproject.toml` + pip editable install | Dependencies **exactly pinned** (`==`) in `[project].dependencies`. Docker installs the same pins. |
| Type checker | **mypy** | `[tool.mypy]` in `pyproject.toml`; CI runs `mypy src/mot_counting`. Not pyright. |
| Containerization | Docker + Compose CPU/GPU | See §11. GPU Compose does **not** reserve an NVIDIA device by default (fails on Docker Desktop macOS/Windows). Pass `--gpus all` on Linux with nvidia-container-toolkit. |
| License | **MIT** (project code) | See §3.1 for Ultralytics AGPL-3.0. |
| Primary Dev Tooling | Cursor (AI-assisted IDE) | |
| Linting / Formatting | **Ruff** (`ruff check` + `ruff format`) | Line length 100, target `py310`. Pre-commit pin `ruff-pre-commit` `v0.16.4`. |
| Logging | stdlib `logging` | Configured once in the composition root. |
| Testing | `pytest` | Marker `integration` for tests that need real weights and `data/ci_sample_clip.mp4`. |
| CLI | stdlib `argparse` | `run_pipeline.py`, `evaluate.py`, `annotate_ground_truth.py`, `run_production.py`. |

### 3.1 Third-Party Licensing Note (Locked)

The project's own source code is licensed under **MIT**. The `ultralytics` package (used to load and run YOLO26) is separately licensed under **AGPL-3.0** by Ultralytics.

- Because this entire project — code, configs, training-free inference pipeline, and all outputs — is published publicly and completely as an open-source academic repository, using `ultralytics` under AGPL-3.0 terms is fully permitted at no cost. No Ultralytics Enterprise License is required for this use case.
- An Enterprise License would only become necessary if any part of the project (or a downstream product built on it) were kept closed-source or deployed commercially without publishing the corresponding source code — which is explicitly out of scope for this academic project.
- The repository's `LICENSE` file contains the MIT license text for the project's own code. A short, clearly worded note is added to `README.md` stating: the project code is MIT-licensed; it depends on `ultralytics`, which is separately licensed under AGPL-3.0 by Ultralytics; users who wish to reuse the `ultralytics` dependency itself must comply with AGPL-3.0 (or obtain their own Ultralytics Enterprise License) independently of this project's MIT license.
- No `THIRD_PARTY_LICENSES.md` or repo-wide AGPL relicensing is needed — the project's own code stays MIT, and the dependency's license is disclosed transparently in the README.

### 3.2 Exact-Pinned Runtime and Dev Dependencies (As-Built)

From `pyproject.toml`:

**Runtime:** `ultralytics==8.4.128`, `opencv-python==4.11.0.86`, `numpy==1.26.4`, `pydantic==2.13.4`, `pyyaml==6.0.3`, `lap==0.5.13`.

**Dev extra:** `pytest==9.1.1`, `ruff==0.16.4`, `pre-commit==4.6.2`, `mypy==1.19.1`, `types-PyYAML==6.0.12.20250915`.

**Torch:** not listed in `pyproject.toml`. Native installs typically pull torch as an Ultralytics dependency. Docker installs torch/torchvision first from `TORCH_INDEX_URL` (`https://download.pytorch.org/whl/cpu` or `.../cu124`) so the CPU image does not pull CUDA wheels.

---

## 4. Software Architecture & Design Patterns (Mandatory)

The system must follow a clean, layered architecture with explicit design patterns so that junior developers can work on isolated modules with minimal risk of interference. The following patterns are required, with their implementation style locked below.

### 4.1 Factory Pattern
- `DetectorFactory` wraps an **already-loaded** Ultralytics YOLO object into `Yolo26Detector`. It never loads weights. Supported `model_variant` values are the five `yolo26*` strings; anything else is `ValueError`.
- `TrackerFactory` constructs `ByteTrackWrapper` for `bytetrack`. Unlike the detector factory, ByteTrack has no separate weight file: the factory **instantiates the wrapper itself** and ignores the `loaded_tracker` argument (passed as `None` from the composition root). `botsort` raises `NotImplementedError`.
- **Model loading boundary:** YOLO weights are loaded in `composition_root._load_detector_model`. Candidate paths, first match wins: `{variant}.pt` in CWD, `/app/{variant}.pt` (Docker), then `{project_root}/{variant}.pt` (two parents above `composition_root.py`). Failures raise `RuntimeError`. No runtime download is required if the `.pt` file is present (Docker copies `yolo26n.pt` and `yolo26m.pt` into `/app` at build time).
- **Class-list validation boundary:** `_validate_classes_against_model` runs immediately after load. Unknown names raise `ValueError` listing `sorted(model.names.values())`. Missing/unusable `.names` raises `TypeError`.

### 4.2 Interface / Abstraction Layer + Dependency Injection
- All major components communicate exclusively through interfaces implemented as **`abc.ABC`** abstract base classes (locked choice — not `typing.Protocol`).
- The central Controller must never import or depend directly on concrete YOLO or ByteTrack classes. (`PipelineController` types against `IDetector` / `ITracker` only.)
- Concrete implementations are injected at construction time via **pure constructor injection**, wired in `composition_root.py`. No DI container.
- Required interfaces:
  - `IDetector`
  - `ITracker`
  - `ICrossingLogic`
  - `IEventRepository`
  - `IVisualizer` (subclass of `Observer`; see §6)
  - `IFrameSource`

### 4.3 Observer Pattern (Scope Locked)
- Implemented **explicitly** in `observers/base.py`: `Observer.update(...)` and `Subject.subscribe` / `Subject.notify`.
- The core sequence `read → detect → track → update crossing state` is a **plain synchronous method sequence inside `PipelineController`**, not observers.
- Side-effect consumers: `LoggerObserver` and `OpenCvVisualizer` subscribe to one `Subject`. The controller calls `visualizer.set_frame(frame)` then `subject.notify(frame_idx, tracks, events, counters)`.
- **Notify policy:** observers are called in subscription order. The **first exception propagates** and remaining observers are **not** notified. Duplicate `subscribe()` of the same instance is allowed (notified once per subscription).
- The controller **must not** call `visualizer.draw()` in the loop (that would double-render). Annotated frames are taken from `visualizer.last_annotated_frame`.

### 4.4 Controller Pattern
- `PipelineController` owns orchestration. Constructor-injected: `AppConfig`, `IFrameSource`, `IDetector`, `ITracker`, `ICrossingLogic`, `IEventRepository`, `IVisualizer`, `Subject`, optional `cv2.VideoWriter`.
- Lifecycle: `run()` (geometry validation, loop, always `cleanup()` in `finally`), `stop()` (graceful after current frame), `cleanup()` (release capture, flush/close CSV, release writer; best-effort, logs exceptions).
- `RunStats`: `frames_processed`, `frames_skipped`, `elapsed_seconds`, `average_fps` (`processed / elapsed`, else `0.0`), `final_counters` snapshot from `get_counters()`.
- Line geometry: `LineGeometryError` if any `point_a` / `point_b` is outside `[0, width) × [0, height)`.
- Timestamp: `frame_idx / fps` when `fps > 0`, else `0.0`.
- Mid-stream decode failure: warning, increment `frames_skipped`, continue. `(False, None)` with no frame is treated as **EOF**.

### 4.5 Repository Pattern
- `CsvEventRepository` is the only production writer of the event CSV. Header is derived from `dataclasses.fields(CrossingEvent)`.
- `bbox` is serialized as one comma-separated string `"x1,y1,x2,y2"` (csv quoting handles commas). Empty string if `None`.
- `InMemoryEventRepository` appends to `self.events`; `flush`/`close` are no-ops.

### 4.6 Composition Root & CLI
- `build_pipeline(config_path)` sequence:
  1. `load_config`
  2. `logging.basicConfig(level=INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")`
  3. Load YOLO; validate `detection.classes`
  4. `OpenCvFrameSource(config.video.path)`; read FPS
  5. `DetectorFactory.create`, `TrackerFactory.create` (`frame_rate=max(1, round(fps))`)
  6. `CrossingLogic(lines, crossing_logic, fps)`, `CsvEventRepository`, `OpenCvVisualizer(lines=config.lines)`
  7. `Subject`; subscribe `LoggerObserver` then visualizer; `log_run_start`
  8. Create `VideoWriter` (creates parent dirs; fail `RuntimeError` if not opened)
  9. Return `PipelineController`
- `scripts/run_pipeline.py`: `--config` required; `--video` optional. If `--video` is set, YAML is patched into a tempfile (`video.path`) before `build_pipeline`. After `run()`, prints `=== Final Counters ===` (`class_name`, `line_id`, direction).
- `scripts/evaluate.py`: `--predictions`, `--ground-truth`; optional `--tolerance-seconds` (else `evaluation.matching_tolerance_seconds` from `configs/default.yaml`); optional `--output-dir` (else prediction CSV directory). Writes artifacts in §7.8. Exit `1` on CSV load errors.
- `scripts/annotate_ground_truth.py` and `scripts/run_production.py`: §13 and §17.

Direct script execution prepends `src/` onto `sys.path` so `pip install -e .` is not strictly required for those CLIs.

---

## 5. Core Data Types (Locked Signatures)

Implemented in `src/mot_counting/types.py` (frozen dataclasses; `Direction` is `str, Enum`).

```python
from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Detection:
    xyxy: tuple[float, float, float, float]  # x1, y1, x2, y2 in pixel coords
    confidence: float
    class_id: int
    class_name: str


@dataclass(frozen=True)
class Track:
    track_id: int
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2 in pixel coords
    class_id: int
    class_name: str
    score: float


class Direction(str, Enum):
    IN = "IN"
    OUT = "OUT"


@dataclass(frozen=True)
class CrossingEvent:
    frame_idx: int
    timestamp_seconds: float
    track_id: int
    class_id: int
    class_name: str
    direction: Direction
    line_id: str
    confidence: float | None = None
    bbox: tuple[float, float, float, float] | None = None
    video_name: str | None = None
```

Pipeline-emitted events set `confidence` from `Track.score` and `bbox` from `Track.bbox` on the confirmation frame. `video_name` remains `None` unless a future caller sets it.

---

## 6. Interfaces (Locked Signatures)

```python
from abc import ABC, abstractmethod
import numpy as np


class IDetector(ABC):
    @abstractmethod
    def predict(self, frame: np.ndarray) -> list[Detection]: ...


class ITracker(ABC):
    @abstractmethod
    def update(
        self, detections: list[Detection], frame_idx: int, frame: np.ndarray
    ) -> list[Track]: ...


class ICrossingLogic(ABC):
    @abstractmethod
    def process(
        self, tracks: list[Track], frame_idx: int, timestamp_seconds: float
    ) -> list[CrossingEvent]: ...

    @abstractmethod
    def get_counters(self) -> dict:
        """Returns current running totals, keyed by (class_name, line_id, direction)."""
        ...


class IEventRepository(ABC):
    @abstractmethod
    def save(self, event: CrossingEvent) -> None: ...

    @abstractmethod
    def flush(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...


class IVisualizer(Observer):  # not a standalone ABC; inherits Observer
    def set_frame(self, frame: np.ndarray) -> None:
        """Bind the current BGR frame before Subject.notify()."""
        ...

    @abstractmethod
    def draw(
        self,
        frame: np.ndarray,
        tracks: list[Track],
        lines: list,
        counters: dict,
    ) -> np.ndarray: ...


class IFrameSource(ABC):
    @abstractmethod
    def read(self) -> tuple[bool, np.ndarray | None]: ...

    @abstractmethod
    def get_fps(self) -> float: ...

    @abstractmethod
    def get_frame_size(self) -> tuple[int, int]: ...  # (width, height)

    @abstractmethod
    def release(self) -> None: ...
```

`IDetector` implementations receive an already-loaded model object at construction time (see §4.1) — the model itself is never loaded inside `predict()`. Frame argument to `predict` is BGR `uint8` `(H, W, 3)`.

`ITracker.update()` accepts the raw current `frame` in addition to `detections` and `frame_idx`. `ByteTrackWrapper` does not use `frame` (motion-only). The parameter stays for a future BoT-SORT implementation.

`Observer.update(frame_idx, tracks, events, counters)` is defined in `observers/base.py`. `IVisualizer` extends `Observer` so `draw()` stays a pure render primitive while `update()` is the pipeline callback. `draw()` must copy the frame (not mutate in place).

`IFrameSource.read()` contract (as implemented by `OpenCvFrameSource`):

- `(True, frame)` — successful decode.
- `(False, None)` — natural end-of-video.
- `(False, sentinel)` — skippable decode/grab failure (`sentinel` is a non-`None` empty `uint8` array). The controller treats any unsuccessful read with a non-`None` frame as skip-and-continue.

---

## 7. Functional Requirements (Must-Have)

### 7.1 Detection
- Frame-by-frame inference with YOLO26 (`yolo26m` default). Frames are processed **one at a time** (`batch_size=1`) in v1.
- Inference image size (`imgsz`) is configurable, **default 640**. Must be a positive integer (Pydantic).
- Filter by configurable class list and a single **global confidence threshold** in `(0, 1]`, default `0.4`. Ultralytics `conf=` is set to that threshold; the wrapper also drops boxes with `conf < threshold`.
- **Class scope for v1:** `person` and `car` only in shipped YAML. The class list is config-driven.
- **Class-name fail-fast validation:** composition root vs `model.names` (§4.1).
- YOLO26 uses a native end-to-end, NMS-free detection head; the wrapper applies **no extra NMS/IoU**.
- Concrete class: `Yolo26Detector` (`detectors/yolo26_detector.py`). Call: `model(frame, imgsz=..., conf=..., verbose=False)[0]`.

### 7.2 Tracking
- `ByteTrackWrapper` (`trackers/bytetrack_tracker.py`) assigns persistent `track_id`s.
- Detections are packed into `UltralyticsResultsMock` (`xyxy`, `xywh`, `conf`, `cls` as float tensors). Empty frames use empty tensors. `BYTETracker.update(..., img=None)`.
- Output layout expected: `[x1, y1, x2, y2, track_id, score, class_id, ...]`. Rows shorter than 7 values are skipped with a warning.
- `class_name` is resolved from a cumulative `_class_names[class_id]` map filled from detections (ByteTrack does not return association indices).
- `reset()` exists for tests (clears tracker + class map).
- Position relative to counting lines is owned by Crossing Logic, not the tracker.

### 7.3 Counting Line(s)
- Each line: `line_id` (unique string), `point_a` / `point_b` as `[x, y]` **absolute pixels**, `positive_direction` `A_to_B` or `B_to_A` (default `A_to_B`).
- Schema requires **at least one** line; duplicate `line_id`s fail Pydantic validation.
- Normalized (0–1) coordinates are **not** supported in v1.
- Runtime geometry: endpoints must lie in `[0, width) × [0, height)` (`PipelineController._validate_line_geometry`).
- Example multi-line file: `configs/examples/multi_line.yaml` (`entrance` / `exit`).
- `configs/production.yaml` does **not** override line geometry per clip; lines must be correct for the target resolution before `run_production.py`.

### 7.4 Crossing Logic (Critical Custom Component)

Implemented in `crossing/crossing_logic.py`. Behavior below is locked for evaluation compatibility.

**Reference point:** default `bottom_center` (`get_bottom_center`: `((x1+x2)/2, y2)`). Configurable `box_center` (`get_bbox_center`).

**Side / direction formula:**

```
signed_distance = (B.x - A.x) * (P.y - A.y) - (B.y - A.y) * (P.x - A.x)
```

`get_side`: `> 0` → `+1` (left of directed A→B), `< 0` → `-1`, `== 0` → `0`. Degenerate A==B: `signed_distance` returns `0.0` (no exception).

**On-line (side 0):** the pair is marked `last_seen` but the window is **not** updated and **no** event is emitted.

**IN vs OUT:** `positive_direction == "A_to_B"`: moving to side `+1` is IN, to `-1` is OUT. `"B_to_A"` inverts this.

**State model — keyed by `(track_id, line_id)`.** Per pair (`_PairState`):

- Sliding window of `(side, class_name, class_id)`, maxlen `history_length` (default 8, ≥ 1).
- `confirmed_side` (`None` until first observation).
- `cooldown_frames_remaining` (from `round(cooldown_seconds * fps)`, fps floored at 1.0).
- `last_seen_frame_idx` for stale cleanup (`round(stale_track_timeout_seconds * fps)`, at least 1 frame).
- `last_event_ref_point` / `last_event_frame_idx` for optional safeguards.

**Sustained-change confirmation:**
1. Append current raw side (if not 0); drop oldest past `history_length`. Decrement cooldown if `> 0`.
2. Majority side over the window; decisive if `majority_count / len(window) >= confirmation_majority_threshold` (must be in `(0.5, 1.0]`, default `0.7`).
3. If `confirmed_side is None`, set it to the current majority and **do not emit**.
4. Crossing only when the majority is decisive **and opposite** `confirmed_side`.
5. If still in cooldown: **no event and `confirmed_side` does not flip**. After cooldown, optional displacement/velocity checks; then emit, flip `confirmed_side`, start cooldown.

**Class attribution:** majority `(class_name, class_id)` over the same window.

**Cooldown:** seconds in config; per `(track_id, line_id)` only.

**Safeguards (disabled when `null`):**
- `min_displacement_px`: Euclidean distance of reference point vs last event.
- `min_velocity_px_per_s`: `|Δ(signed_distance / line_length)| / Δt` using FPS.

**Stale cleanup:** entries with `(frame_idx - last_seen_frame_idx) > stale_timeout_frames` are deleted at the start of `process()`.

Counters increment on emit: `(majority_class_name, line_id, direction)`.

**Known limitation — track ID switches:** a new ID starts with empty state and can duplicate or miss a count. Not solved via ReID in v1.

### 7.5 Event Logging
Every validated crossing produces one `CrossingEvent` written via the repository:

- `frame_idx`, `timestamp_seconds`, `track_id`
- Majority-vote `class_name` / `class_id`
- `direction`, `line_id`
- `confidence` and `bbox` from the confirmation-frame `Track`
- `video_name`: not set by the pipeline

CSV columns (header order): `frame_idx, timestamp_seconds, track_id, class_id, class_name, direction, line_id, confidence, bbox, video_name`.

### 7.6 Visualization
`OpenCvVisualizer` draws:

- Counting lines in cyan by default, labeled with `line_id` near the midpoint.
- Boxes colored by class (`person` green, `car` blue; bicycle/motorcycle/bus/truck palette; else `class_id % palette`).
- Label `ID:{track_id} {class_name} {score:.2f}` on a filled background.
- Live overlay top-left: `[line_id]` then `Class IN: n OUT: m` (handles tuple keys `(class_name, line_id, Direction)`).

`draw_trails` is unused. Observer `update` no-ops if `set_frame` was not called.

### 7.7 Configuration
Everything user-tunable lives in YAML validated by `AppConfig`. Shipped files:

| File | Role |
|---|---|
| `configs/default.yaml` | Evaluation/default: `yolo26m`, `data/ci_sample_clip.mp4` |
| `configs/ci.yaml` | CI/integration: `yolo26n`, same clip |
| `configs/production.yaml` | Production detector `yolo26m`; video/output paths placeholders overridden by `run_production.py` |
| `configs/examples/multi_line.yaml` | Two independent lines |

**Reference `configs/default.yaml`:**

```yaml
video:
  path: "data/ci_sample_clip.mp4"
  output_dir: "outputs/"

detection:
  model_variant: "yolo26m"   # yolo26n | yolo26s | yolo26m | yolo26l | yolo26x
  imgsz: 640
  confidence_threshold: 0.4
  classes: ["person", "car"]

tracker:
  type: "bytetrack"          # bytetrack | botsort (botsort not wired)
  track_thresh: 0.5
  match_thresh: 0.8
  track_buffer: 30

lines:
  - line_id: "main_line"
    point_a: [100, 400]
    point_b: [800, 400]
    positive_direction: "A_to_B"

crossing_logic:
  reference_point: "bottom_center"   # bottom_center | box_center
  history_length: 8
  confirmation_majority_threshold: 0.7
  cooldown_seconds: 1.5
  stale_track_timeout_seconds: 2.0
  min_displacement_px: null
  min_velocity_px_per_s: null

events:
  output_csv: "outputs/events.csv"

evaluation:
  matching_tolerance_seconds: 1.0

visualization:
  output_video: "outputs/annotated.mp4"
  draw_trails: false
```

Published magazine numbers must use `default.yaml` (`yolo26m`), never `ci.yaml`.

### 7.8 Evaluation Support

Canonical protocol: `docs/evaluation-protocol.md`. Implementation: `src/mot_counting/evaluation.py`.

**CSV load:** required columns `timestamp_seconds`, `class_name`, `direction`, `line_id`. Optional: `frame_idx`, `track_id`, `class_id`. Whitespace stripped; `class_name` lowercased; `direction` uppercased to `Direction`. Missing required fields → `ValueError`. Missing file → `FileNotFoundError`.

**Grouping:** independent strata `(line_id, class_name, direction)` — **not** class+direction alone.

**Eligibility:** same class, direction, **and** `line_id`, and

```text
abs(prediction.timestamp_seconds - ground_truth.timestamp_seconds) <= tolerance_seconds
```

Inclusive. Tolerance is applied in **seconds**, not converted to frames.

**Assignment:** sort each group by `(timestamp_seconds, source_index)`. Exact DP: (1) maximize number of eligible matches; (2) minimize total absolute timestamp error. Tie-break recurrence order: skip prediction, then skip GT, then match. One-to-one: extra eligible predictions are FP.

**Metrics** (overall and per group):

- Precision = `TP / (TP + FP)` — `None` / `N/A` if no predictions
- Recall = `TP / (TP + FN)` — `N/A` if no GT
- F1 = harmonic mean when both defined; `0.0` if both are `0.0`
- Absolute counting error = `|predicted_count − gt_count|`
- Relative counting error = abs error / `gt_count` — `N/A` if `gt_count == 0`
- Percentage counting error = relative × 100

**Artifacts:** `evaluation_summary.csv` (overall row then groups), `evaluation_matches.csv` (TP/FP/FN). TP `time_delta_seconds` = `prediction_timestamp − gt_timestamp` (signed; matching uses absolute error).

Pipeline FPS / runtime remain informational (`RunStats`), not part of the event matcher.

---

## 8. High-Level Architecture

```
Configuration (YAML, validated via Pydantic v2 AppConfig)
        ↓
Composition Root (build_pipeline: load YOLO from local .pt,
                   validate classes vs model.names,
                   open OpenCvFrameSource, Factories,
                   CrossingLogic, CsvEventRepository,
                   OpenCvVisualizer, LoggerObserver, VideoWriter)
        ↓
PipelineController  ←── injects ──→  IDetector (Yolo26Detector)
        │                              ITracker  (ByteTrackWrapper)
        │                              ICrossingLogic
        │                              IEventRepository
        │                              IVisualizer (also Observer)
        │                              IFrameSource
        │                              Subject
        ↓
synchronous loop: read → detect → track → process crossings → save events
        ↓
set_frame + Subject.notify ──→ LoggerObserver, OpenCvVisualizer
        ↓
VideoWriter ← last_annotated_frame     CSV ← CsvEventRepository
```

All components communicate through `abc.ABC` interfaces. The Controller never imports concrete detector or tracker classes.

---

## 9. Repository Structure (As-Built)

This project is `projects/artificial-intelligence/` inside the magazine-03 git repository.

```
artificial-intelligence/
├── README.md
├── README.fa.md
├── LICENSE                          # MIT (project code)
├── SPEC.md
├── pyproject.toml
├── .pre-commit-config.yaml
├── Dockerfile
├── docker-compose.cpu.yml
├── docker-compose.gpu.yml
├── .dockerignore
├── configs/
│   ├── default.yaml
│   ├── ci.yaml
│   ├── production.yaml
│   └── examples/
│       └── multi_line.yaml
├── src/mot_counting/
│   ├── config.py
│   ├── composition_root.py
│   ├── types.py
│   ├── evaluation.py                # matcher + metrics (not utils/metrics.py)
│   ├── interfaces/
│   │   ├── detector.py
│   │   ├── tracker.py
│   │   ├── crossing.py
│   │   ├── repository.py
│   │   ├── visualizer.py
│   │   └── frame_source.py
│   ├── factories/
│   │   ├── detector_factory.py
│   │   └── tracker_factory.py
│   ├── detectors/
│   │   └── yolo26_detector.py
│   ├── trackers/
│   │   └── bytetrack_tracker.py
│   ├── crossing/
│   │   └── crossing_logic.py
│   ├── repositories/
│   │   ├── csv_event_repository.py
│   │   └── in_memory_event_repository.py
│   ├── visualizers/
│   │   └── opencv_visualizer.py
│   ├── controllers/
│   │   └── pipeline_controller.py
│   ├── observers/
│   │   ├── base.py
│   │   └── logger_observer.py
│   └── utils/
│       ├── geometry.py
│       └── video_io.py              # OpenCvFrameSource
├── scripts/
│   ├── run_pipeline.py
│   ├── evaluate.py
│   ├── annotate_ground_truth.py
│   └── run_production.py
├── tests/
│   ├── unit/                        # see §12.3
│   ├── integration/
│   │   └── test_full_pipeline.py
│   └── test_annotate_ground_truth.py
├── data/
│   └── ci_sample_clip.mp4           # synthetic / CC0 — docs/ci-sample-clip.md
├── outputs/                         # gitignored runtime artifacts
├── docs/
│   ├── evaluation-protocol.md
│   ├── ci-sample-clip.md
│   └── branch-protection-ai-develop.md
└── .github/
    └── workflows/
        └── README.md                # points to magazine-03 root ai-ci.yml
```

YOLO weight files `yolo26n.pt` / `yolo26m.pt` are expected in the project (or Docker build) context; they are not committed as source.

---

## 10. Detailed Module Specifications

### 10.1 Configuration (`config.py`)
- Submodels: `VideoConfig`, `DetectionConfig`, `TrackerConfig`, `LineConfig`, `CrossingLogicConfig`, `EventsConfig`, `EvaluationConfig`, `VisualizationConfig`, root `AppConfig`.
- YAML must be a mapping; parse errors → `ValueError`. Missing file → `FileNotFoundError`.
- Line-vs-frame validation is **not** in Pydantic (unknown until video open).
- Class-vs-model validation is **not** in Pydantic (unknown until YOLO load).

### 10.2 Interfaces & Dependency Injection
- See §6. Concrete classes are created only in factories or the composition root (plus tests).

### 10.3 Detector (`detectors/` + Factory)
- `Yolo26Detector(model, imgsz, confidence_threshold, allowed_classes)`.
- Factory forwards `confidence_threshold`, `classes`, `imgsz` from config.

### 10.4 Tracker (`trackers/` + Factory)
- `ByteTrackWrapper(frame_rate, track_thresh, match_thresh, track_buffer, fuse_score=True)`.
- Factory `frame_rate` comes from video FPS.

### 10.5 Crossing Logic (`crossing/`)
- Implements §7.4. FPS used to convert cooldown and stale timeout once at construction.

### 10.6 Event Repository
- `CsvEventRepository(output_path)` creates parent directories, opens `"w"` UTF-8, writes header immediately, keeps the handle open. Controller must `close()` even on errors.

### 10.7 Visualizer
- Construction-time `lines` from config. `last_annotated_frame` is the write source for `VideoWriter`.

### 10.8 Logger (Observer)
- `LoggerObserver`: `log_run_start`, `log_run_stop`, `log_frame_warning`, `update`.
- Per-frame: DEBUG dump of tracks/events/counters; INFO if any crossings this frame.
- Decode-skip warnings currently come from `PipelineController`'s module logger, not `log_frame_warning`.

### 10.9 Pipeline Controller
- See §4.4.

### 10.10 Geometry (`utils/geometry.py`)
- `signed_distance`, `get_side`, `get_bottom_center`, `get_bbox_center`.

### 10.11 Frame source (`utils/video_io.py`)
- Missing file → `FileNotFoundError`; OpenCV cannot open → `RuntimeError`.
- `get_fps()`: container FPS, else fallback **`DEFAULT_FPS = 30.0`** if non-finite or `<= 0`.
- `get_frame_size()`: invalid width/height → `RuntimeError`.
- `read()` uses `grab`/`retrieve` and advances past failed grabs when `CAP_PROP_FRAME_COUNT` still indicates remaining frames.

### 10.12 Evaluation (`evaluation.py`)
- Types: `EvaluationEvent`, `GroupKey`, `MatchPair`, `GroupMatchResult`, `GroupMetrics`, `EvaluationResult`.
- Public helpers: `load_prediction_events`, `load_ground_truth_events`, `event_from_crossing_fields`, `evaluate_events`, `compute_group_metrics`.

---

## 11. Docker & Reproducibility (Mandatory)

- Single `Dockerfile` with `ARG BASE_IMAGE` (default `python:3.12-slim`) and `ARG TORCH_INDEX_URL`.
- System packages: `libglib2.0-0`, `libsm6`, `libxext6`, `libxrender1`, `libgomp1`, `libgl1`.
- Weights: `COPY yolo26n.pt yolo26m.pt /app/` — files **must exist in the build context**. Download once: `python -c "from ultralytics import YOLO; YOLO('yolo26n.pt'); YOLO('yolo26m.pt')"`.
- `ENV ULTRALYTICS_CONFIG_DIR=/app/.ultralytics`, `PYTHONPATH=/app/src`.
- **ENTRYPOINT:** `["python", "scripts/run_pipeline.py"]` **CMD:** `["--config", "configs/ci.yaml"]`. Extra `docker run` tokens append to the entrypoint. To run `run_production.py`, pass `--entrypoint python` (see script docstring).
- Compose mounts: `configs/` and `data/` read-only, `outputs/` read-write.
- `tests` service: `pytest tests/unit/`.
- GPU file: `platform: linux/amd64`, `pull_policy: never`; optional `--gpus all`.

There is no real-time processing requirement. FPS is informational.

---

## 12. Engineering Practices

### 12.1 Error Handling (Locked Policy)
- **Startup errors** (video missing/unopenable, model load failure, invalid config, unknown class names, line geometry, VideoWriter fail) → **fail fast**.
- **Per-frame decode errors** → log warning, skip, continue.
- Observer exceptions abort remaining observers for that frame and propagate unless the caller catches them (controller does not catch notify errors).

### 12.2 Logging
- stdlib `logging`, default **INFO** at composition-root startup (not YAML).
- `WARNING` for skippable frames; `DEBUG` for crossing tracing.

### 12.3 Testing
- Framework: `pytest`; `testpaths = ["tests"]`.
- `tests/unit/`: `test_config`, `test_types`, `test_geometry`, `test_crossing_logic`, `test_factories`, `test_yolo26_detector`, `test_bytetrack_tracker`, `test_repositories`, `test_observers`, `test_logger_observer`, `test_visualizer`, `test_video_io`, `test_pipeline_controller`, `test_composition_root`, `test_evaluate`, `test_interfaces`, `test_run_production_docker`.
- `tests/integration/test_full_pipeline.py`: end-to-end with real weights + CI clip (pytest marker `integration`).
- `tests/test_annotate_ground_truth.py`: annotator helpers (not under `unit/`).
- Docker CI (magazine-03 root workflow): Ruff check + format `--check`, mypy, `pytest tests/unit/`, CPU image run of `configs/ci.yaml` requiring non-empty `outputs/annotated.mp4` and `outputs/events.csv`. GPU is not in CI.

### 12.4 Pre-commit Hook (Locked)
- Ruff only: `ruff` with `--fix`, then `ruff-format`. Rev `v0.16.4`.

### 12.5 Documentation & Code Standards
- Type hints; Google-style docstrings on public APIs in most modules.
- README (English) + optional `README.fa.md`.
- CI clip is synthetic / CC0 — `docs/ci-sample-clip.md`.
- No hard-coded credentials.

---

## 13. Evaluation Protocol (Armila-Owned Final Assessment)

**Test Set:** 4–6 short clips covering normal flow, higher density, partial occlusion, bi-directional movement.

**Ground Truth creation:** `scripts/annotate_ground_truth.py` (OpenCV only; no detector/tracker). Independent of the pipeline.

```text
python scripts/annotate_ground_truth.py --video data/clip.mp4 --output data/gt.csv
```

Controls: **Space** pause/resume, **Left/Right** step (pauses), **M** mark crossing, **U** undo last, **Q** or **Esc** save and quit. Marking pauses playback, prompts in the terminal for `class_name`, `direction` (`IN`/`OUT`), `line_id`, then auto-saves the CSV. Empty class or line, or invalid direction, cancels that mark.

GT CSV columns: `frame_idx, timestamp_seconds, class_name, direction, line_id, video_name` (no `track_id`). Timestamp `round(frame_idx / fps, 6)`. Invalid container FPS falls back to **25.0** (annotator-only; pipeline frame source uses **30.0**).

**Matching and metrics:** §7.8. Default tolerance placeholder `1.0` s until finalized on real clips.

**Qualitative failure cases:** missed detection, class confusion, track fragmentation / ID switches, false crossing, occlusion — from manual review of annotated video vs GT. No automated class-confusion matcher in v1.

---

## 14. Stretch Goals (Only If Core Pipeline Is Solid and Schedule Allows)

1. Side-by-side comparison of ByteTrack vs BoT-SORT on the same videos and GT (`BoTSortWrapper` + factory wiring).
2. Optional ROI occupancy / time-in-area analytics.
3. Short trajectory visualization (`draw_trails: true`).
4. Limited ReID experiment (track ID switch limitation from §7.4).
5. Evaluation on a subset of MOT17 (tracker quality only).
6. YOLO11 vs YOLO26 detection quality / speed comparison (late, non-blocking).
7. Frame-batching for detection throughput.
8. Populate `CrossingEvent.video_name` from `config.video.path` in crossing logic or the controller.
9. Configurable log level in YAML.

Given the 10-day timeline (deadline September 1, 2026), stretch goals are explicitly lower priority than a fully stable core pipeline and evaluation.

---

## 15. Development Workflow, Git Strategy & Task Allocation

### 15.1 Branch Strategy (Locked)
- `main` is the protected, stable branch.
- `ai-develop` is the team's integration branch, created off `main`. All feature work for this project happens off `ai-develop`, not off `main` directly.
- Feature branches: `feature/<short-task-name>` from `ai-develop`.
- PRs target `ai-develop`. No direct pushes to `ai-develop` or `main`.
- CI runs on every PR into `ai-develop`. See `docs/branch-protection-ai-develop.md`.

### 15.2 Task Ticket Format (Locked)
- Tasks are GitHub Issues. The originally planned template path `.github/ISSUE_TEMPLATE/implementation_task.md` is **not present in this project folder**; if reintroduced, required sections remain: Context, Interface to implement, Acceptance criteria, Test cases.

### 15.3 Code Review & Merge Policy
- Every PR into `ai-develop` requires Mostafa's review and approval.
- CI must be green (Ruff, mypy, unit tests, Docker CPU integration) before merge.

### 15.4 Sequencing
1. Skeleton: config, interfaces, factories, composition root, controller, Observer, Crossing Logic.
2. Docker (CPU/GPU, baked weights) and pre-commit early.
3. Independent interface-backed modules (detector, visualizer, CSV repo, GT annotator, evaluation).
4. CI at magazine-03 root: `.github/workflows/ai-ci.yml` — working directory `projects/artificial-intelligence`. This subdirectory only documents that workflow.
5. Armila's official evaluation after the event format is frozen (CSV schema + matcher in §7.8).

---

## 16. Deliverables for the Magazine Article (Section 3 – Implementation)

The code repository itself is the primary artifact. The magazine text (≈ 4 pages) will:

- Clearly state the problem and input assumptions.
- Describe the overall architecture, explicitly mentioning Factory, Observer (side-effect consumers only), Controller, Repository, and manual composition-root DI (`abc.ABC`, Pydantic v2).
- Walk through Detection → Tracking → Crossing Logic (bottom-center, signed-distance, confirmed-side + history window, cooldown, majority-class attribution, on-line side-0 skip).
- Explain per-class, per-line counting and CSV logging via the Repository.
- Present the evaluation protocol (group key includes `line_id`; DP matching on timestamps), metrics, and real failure cases — including track ID switches.
- Conclude with strengths, limitations, and extensions (§14).

The repository README, `docs/evaluation-protocol.md`, and this document together serve as the complete technical specification.

---

## 17. Production Multi-Clip Runner (As-Built)

`scripts/run_production.py` runs `build_pipeline` once per clip with patched paths.

```text
python scripts/run_production.py \
    --config configs/production.yaml \
    --clips data/clip_a.mp4 data/clip_b.mp4 \
    --output-root outputs/production
```

Per clip under `{output-root}/{stem}/`: `{stem}_events.csv`, `{stem}_annotated.mp4`. Missing clips are recorded as errors and skipped. After each success, `load_prediction_events` verifies T18/evaluator compatibility.

Manifest `{output-root}/production_manifest_{UTC}.json` includes execution context (Python, platform, torch CPU/GPU/MPS if importable, detector variant), per-clip stats/counters (`class|line|DIR` keys), and summary counts. Exit **1** if any clip failed; exit **2** if any CSV failed the evaluator parse.

Docker: replace ENTRYPOINT:

```text
docker run --rm --entrypoint python \
    -v "$(pwd)/configs:/app/configs:ro" \
    -v "$(pwd)/data:/app/data:ro" \
    -v "$(pwd)/outputs:/app/outputs" \
    mot-counting:cpu \
    scripts/run_production.py --config configs/production.yaml \
        --clips data/clip_a.mp4 --output-root outputs/production
```

`run_production.py` does **not** override `lines`; set geometry for the clip resolution in YAML first.

---

## 18. CLI Quick Reference

All commands are run from `projects/artificial-intelligence/` (the directory with `pyproject.toml`).

```text
# Single-clip pipeline
python scripts/run_pipeline.py --config configs/ci.yaml
python scripts/run_pipeline.py --config configs/default.yaml --video data/clip.mp4

# Evaluate predictions vs ground truth
python scripts/evaluate.py --predictions outputs/events.csv --ground-truth data/gt.csv
python scripts/evaluate.py --predictions outputs/events.csv --ground-truth data/gt.csv \
    --tolerance-seconds 1.0 --output-dir outputs/eval

# Manual GT
python scripts/annotate_ground_truth.py --video data/clip.mp4 --output data/gt.csv

# Multi-clip production + manifest
python scripts/run_production.py --config configs/production.yaml \
    --clips data/a.mp4 --output-root outputs/production

# Docker CPU pipeline
docker compose -f docker-compose.cpu.yml run --rm pipeline --config configs/ci.yaml
```

The repository README and this document together are the complete technical specification so that any competent developer can run, evaluate, or extend the system without further clarification.
