# Evaluation Results

## 1. Evaluation Overview

This evaluation measures event-level and counting performance of the production directional line-crossing pipeline on a frozen set of five real video clips.

The evaluated pipeline is:

```text
YOLO26 detector
→ ByteTrack tracker
→ directional line-crossing logic
→ event CSV
→ event-level evaluation
```

The evaluation covers `person` and `car` crossing events using the configured `bottom_center` reference point.

Across the five clips, the Ground Truth contains 57 manually annotated crossing events. The production system emitted 54 crossing events. Event-level matching produced:

- **TP:** 54
- **FP:** 0
- **FN:** 3
- **Precision:** 1.0000
- **Recall:** 0.9474
- **F1:** 0.9730
- **Absolute counting error:** 3
- **Percentage counting error:** 5.26%

Four clips were matched without event-level errors. The remaining clip exposed three missed `car / IN` crossings and provides the main failure case examined in this report.

---

## 2. Evaluation Set

The final evaluation set contains five short fixed-camera clips covering pedestrian and vehicle scenes, different movement directions including bidirectional traffic, different target densities, partial occlusion, and closely spaced crossings.

| Clip | Primary class | Scenario | Frames | Duration |
| --- | --- | --- | ---: | ---: |
| `escalator_0_9s.mp4` | `person` | Moderate-density pedestrian flow with partial occlusion | 216 | 9.00 s |
| `BackVehcilesTraffic720p_14_28s.avi` | `car` | Vehicle traffic with both `IN` and `OUT` crossings | 350 | 14.00 s |
| `TwoWayTraffic720p_shift05s.mp4` | `car` | Bidirectional vehicle traffic | 477 | 19.08 s |
| `VIRAT_S_010204_05_000856_000890_trim4s.mp4` | `person` | Low-density pedestrian movement | 488 | 20.36 s |
| `BackVehcilesTraffic720p_61_79s.avi` | `car` | More demanding vehicle flow with closely spaced crossings | 450 | 18.00 s |

Total processed frames: **1,981**.

### Ground Truth event counts

| Clip | GT events |
| --- | ---: |
| Escalator | 8 |
| MND Back 14–28 s | 12 |
| TwoWay | 15 |
| VIRAT | 5 |
| MND 61–79 s | 17 |
| **Total** | **57** |

---

## 3. Methodology

### 3.1 Ground Truth process

Ground Truth was created manually using the project annotation workflow and the schema:

```text
frame_idx
timestamp_seconds
class_name
direction
line_id
video_name
```

Ground Truth was manually annotated by a single reviewer and subsequently rechecked frame-by-frame. For every final evaluation clip, Ground Truth was completed and reviewed from the video before the corresponding production predictions were inspected.

This ordering kept annotation decisions independent from production outcomes.

The crossing reference used during annotation matched production semantics:

```text
bottom_center
```

Each event was assigned to the frame where the object's `bottom_center` crossed the locked counting line. When the exact frame required closer inspection, adjacent frames were stepped through until the side transition was visually resolved.

For vehicle scenes, `car` Ground Truth was limited to visually unambiguous passenger cars. Other vehicle categories were not merged into `car` solely for evaluation.

The annotation interface displayed the locked counting-line geometry and direction as visual guidance. This display support did not alter the source video or Ground Truth event semantics.

### 3.2 Production configuration

All five clips were evaluated using the same production detector, tracker, and crossing-logic settings:

```yaml
detection:
  model_variant: "yolo26m"
  imgsz: 960
  confidence_threshold: 0.35
  classes: ["person", "car"]

tracker:
  type: "bytetrack"
  track_thresh: 0.5
  match_thresh: 0.8
  track_buffer: 30

crossing_logic:
  reference_point: "bottom_center"
  history_length: 8
  confirmation_majority_threshold: 0.7
  cooldown_seconds: 1.5
  stale_track_timeout_seconds: 2.0
```

Clip-specific configuration was limited to the counting-line geometry and line identifier.

No production settings were changed between final clips in response to evaluation results.

### 3.3 Matching protocol and frozen tolerance

Event-level scoring used the project evaluator in `scripts/evaluate.py`.

Predictions and Ground Truth events were matched only when they agreed on:

```text
line_id
class_name
direction
```

Matching was one-to-one and required the absolute timestamp difference to be within the frozen temporal tolerance.

The final tolerance was:

```text
matching_tolerance_seconds = 0.5
```

The same value was used for all five clips.

The tolerance was frozen before the primary evaluation scoring run and was not changed after results were produced.

The value was selected to accommodate plausible timestamp offsets between a manually identified geometric crossing and the production event timestamp. Production crossing logic uses an 8-frame history and majority confirmation, which can shift the emitted event time relative to the frame where the manually reviewed `bottom_center` crosses the line. Frame-to-frame variation in detector bounding-box geometry can also shift the measured `bottom_center` around the boundary.

Matching remains one-to-one within the exact `(line_id, class_name, direction)` group, so the 0.5 s tolerance defines the maximum temporal separation allowed for otherwise compatible events; it does not relax class, direction, or line identity.

---

## 4. Results

### 4.1 Per-clip results

| Clip | GT | Predicted | TP | FP | FN | Precision | Recall | F1 | Abs. count error | Count error % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Escalator | 8 | 8 | 8 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0 | 0.00% |
| MND Back 14–28 s | 12 | 12 | 12 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0 | 0.00% |
| TwoWay | 15 | 15 | 15 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0 | 0.00% |
| VIRAT | 5 | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0 | 0.00% |
| MND 61–79 s | 17 | 14 | 14 | 0 | 3 | 1.0000 | 0.8235 | 0.9032 | 3 | 17.65% |

### 4.2 Aggregate metrics

Across all five clips:

```text
GT events        = 57
Predicted events = 54

TP = 54
FP = 0
FN = 3
```

| Metric | Value |
| --- | ---: |
| Precision | 1.0000 |
| Recall | 0.9474 |
| F1 | 0.9730 |
| Absolute counting error | 3 |
| Percentage counting error | 5.26% |

No false-positive crossing events were observed in this evaluation set. All observed event-level errors were missed crossings.

### 4.3 Per-direction and per-group results

| Line / class / direction | GT | Predicted | TP | FP | FN | Precision | Recall | F1 | Count error % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `escalator_main / person / IN` | 8 | 8 | 8 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.00% |
| `mnd_back_main / car / IN` | 8 | 8 | 8 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.00% |
| `mnd_back_main / car / OUT` | 4 | 4 | 4 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.00% |
| `twoway_main / car / IN` | 5 | 5 | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.00% |
| `twoway_main / car / OUT` | 10 | 10 | 10 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.00% |
| `virat_main / person / IN` | 2 | 2 | 2 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.00% |
| `virat_main / person / OUT` | 3 | 3 | 3 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.00% |
| `mnd_61_79_main / car / IN` | 5 | 2 | 2 | 0 | 3 | 1.0000 | 0.4000 | 0.5714 | 60.00% |
| `mnd_61_79_main / car / OUT` | 12 | 12 | 12 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.00% |

The performance reduction is localized to the `car / IN` group in the MND 61–79 s clip. The corresponding `OUT` flow in the same clip was fully matched.

---

## 5. Runtime and Execution Environment

All final production runs were executed in CPU mode using the same detector model.

### Execution environment

```text
Platform: Windows 11
CPU: 13th Gen Intel(R) Core(TM) i5-13500H
Execution mode: CPU
Detector model: yolo26m
Python: 3.12.0
PyTorch: 2.13.0+cpu
Ultralytics: 8.4.128
OpenCV: 4.11.0
ByteTrack implementation: Ultralytics BYTETracker via project ByteTrackWrapper
Git commit: 7dd1059e97c6042116252f4501c98f6b3619aef1
```

An Intel Iris Xe graphics adapter was present on the machine, but GPU acceleration was not used for these runs.

### Per-clip runtime

| Clip | Frames | Processing time | Average FPS | Total wall time |
| --- | ---: | ---: | ---: | ---: |
| Escalator | 216 | 145.281 s | 1.49 | 147.280 s |
| MND Back 14–28 s | 350 | 392.563 s | 0.89 | 393.570 s |
| TwoWay | 477 | 405.766 s | 1.18 | 406.705 s |
| VIRAT | 488 | 225.156 s | 2.17 | 225.859 s |
| MND 61–79 s | 450 | 208.532 s | 2.16 | 209.187 s |

Across the five runs:

```text
Total frames processed = 1,981
Total processing time  = 1,377.298 s
Total wall time        = 1,382.601 s
Aggregate throughput   ≈ 1.44 FPS
```

These measurements characterize the CPU-based evaluation environment. Deployment throughput will depend on execution hardware and acceleration configuration.

---

## 6. Validation and Evaluation Reproducibility

### 6.1 Representative event validation

Representative true-positive events and all observed false-negative events were manually checked against the corresponding video frames.

Representative checks included:

- MND Back GT frame 82 matched prediction frame 85.
- Escalator GT frame 207 matched prediction frame 198, with a time difference of 0.375 s.

Both checks were confirmed to represent the same physical crossing event.

The largest observed absolute timestamp difference among matched events was 0.375 s, remaining inside the frozen 0.5 s tolerance.

No false-positive events were produced in the final evaluation set, so no FP event was available for representative manual inspection.

### 6.2 False-negative validation

The three false negatives in `mnd_61_79_main / car / IN` were manually reviewed:

```text
GT frame 167 → 6.68 s
GT frame 182 → 7.28 s
GT frame 352 → 14.08 s
```

Each was confirmed as a genuine line crossing.

The annotated production video was also inspected around each miss to determine the most likely failure region:

- At frame 167, the vehicle remained detected and retained a stable track ID across the counting line, but no corresponding `IN` event was emitted.
- At frame 182, the vehicle became occluded by a tree before reaching the line. Its bounding box disappeared during the occlusion; the vehicle was tracked as ID `19` before the occlusion and ID `22` after reappearing beyond the line.
- At frame 352, the vehicle again remained detected with a stable track ID across the boundary, but no corresponding `IN` event was emitted.

The events around GT frames 352 and 360 were reviewed more closely because they occurred only eight frames apart. Frame-by-frame inspection confirmed two distinct real crossings: one by a white vehicle and one by a dark vehicle. Production emitted only one `IN` event in this interval, at frame 357. Under the frozen one-to-one matching procedure, the evaluator associated that event with GT frame 360, leaving GT frame 352 unmatched. The available evidence establishes two separate physical crossings and one emitted production event; it does not, by itself, establish the physical identity represented by the frame-357 event.

### 6.3 Aggregate reconciliation

Aggregate counts were recomputed directly from the per-clip `overall` rows:

```text
TP = 54
FP = 0
FN = 3
Predicted = 54
GT = 57
```

The recomputed Precision, Recall, F1, and counting error matched the reported aggregate values.

### 6.4 Evaluation reproducibility check

The evaluation stage was executed a second time for all five clips using the same frozen Ground Truth files, production prediction CSVs, and 0.5 s matching tolerance.

For all five clips:

- `evaluation_summary.csv` from the repeated evaluation was identical to the original evaluation output.
- `evaluation_matches.csv` from the repeated evaluation was identical to the original evaluation output.

This confirms deterministic reproduction of the reported evaluation metrics and event matches from the frozen Ground Truth and prediction artifacts.

---

## 7. Failure Analysis and Stress Observations

### 7.1 Missed crossings with stable tracking

A genuine `car / IN` crossing at GT frame 167 (`6.68 s`) in the MND 61–79 s clip was not emitted as a production crossing event.

Manual review of the annotated production video confirmed that the vehicle remained detected, retained a stable track ID, and crossed the configured counting line without a visible tracking interruption.

Because detection and track continuity were present across the boundary, the most likely failure region is the **Crossing Logic**, specifically crossing confirmation or event generation.

Effect:

```text
1 false negative
1-event IN undercount
```

A second failure with the same observable pattern occurred at GT frame 352 (`14.08 s`). The vehicle remained detected and continuously tracked across the line, but no corresponding `IN` event was emitted.

The nearby GT event at frame 360 (`14.40 s`) was a separate physical crossing from the GT event at frame 352. Production emitted only one `IN` event in this interval, at frame 357, and the frozen evaluator matched that event to GT frame 360, leaving GT frame 352 unmatched. The available evidence does not require assigning a physical vehicle identity to the frame-357 production event.

For the frame-352 miss, the most likely subsystem is again the **Crossing Logic** because the GT frame-352 vehicle remained detected and continuously tracked across the boundary without a corresponding second `IN` event.

### 7.2 Occlusion-related track fragmentation

The GT crossing at frame 182 (`7.28 s`) showed a different failure mode.

Before reaching the counting line, the vehicle became occluded by a tree. During this interval the production annotation no longer contained a bounding box for the vehicle.

Before the occlusion the vehicle was tracked as:

```text
track_id = 19
```

After it reappeared beyond the counting line, it was assigned:

```text
track_id = 22
```

The crossing therefore occurred while continuous tracking information was unavailable.

This failure is most consistent with **Tracking**, triggered by occlusion-related detection loss and resulting track fragmentation / ID reassignment.

Effect:

```text
1 false negative
1-event IN undercount
```

### 7.3 Failure summary

| GT frame | Time | Failure pattern | Likely subsystem | Effect |
| ---: | ---: | --- | --- | --- |
| 167 | 6.68 s | Stable detection and track, but no `IN` event | Crossing Logic | 1 FN |
| 182 | 7.28 s | Occlusion, lost bbox, track `19 → 22` | Tracking | 1 FN |
| 352 | 14.08 s | Stable detection and track, but no `IN` event | Crossing Logic | 1 FN |

The three observed errors therefore represent two distinct failure modes: crossing-event generation despite stable tracking, and occlusion-related track fragmentation.

### 7.4 Stress observations across the set

The remaining four clips produced complete event matches despite differences in scene structure:

- moderate-density pedestrian movement and partial occlusion in the escalator scene,
- vehicle traffic with both `IN` and `OUT` crossings in MND Back,
- bidirectional vehicle movement in TwoWay,
- low-density pedestrian movement in VIRAT.

The observed errors were concentrated in the more demanding incoming-flow portion of the MND 61–79 s sequence rather than distributed broadly across the tested scenarios.

---

## 8. Limitations

This evaluation uses five short fixed-camera clips and should be interpreted as a focused real-video evaluation rather than a large-scale benchmark.

The scene set includes useful variation in movement direction, target type, density, and interaction near the counting line, but it does not cover the full range of camera viewpoints, lighting conditions, weather, target scales, or crowd and traffic densities that may occur in deployment.

Only the frozen production configuration using `yolo26m` reported here was evaluated. This evaluation is not a detector, tracker, image-size, or confidence-threshold ablation.

Runtime measurements were collected in CPU mode on a single machine and should not be generalized to GPU deployments or other hardware.

No false-positive crossing events occurred in this five-clip set, so false-positive behavior is less characterized than false-negative behavior.

The available artifacts support a likely subsystem attribution for the observed misses, but they do not prove a unique root cause at the internal algorithm-state level.

---

## 9. Conclusion

The frozen five-clip evaluation produced 54 true-positive crossing events, no false-positive events, and three false negatives from 57 Ground Truth events.

Overall event Precision was 1.0000, Recall was 0.9474, and F1 was 0.9730. The aggregate counting error was three events, corresponding to 5.26% of the Ground Truth count.

Four clips were matched without event-level errors across pedestrian, mixed-direction vehicle, bidirectional vehicle, and low-density scenarios. The observed errors were concentrated in one more demanding vehicle sequence, specifically the incoming direction, including a case with two vehicles crossing only 0.32 s apart.

The results show strong event-level performance within this focused five-clip fixed-camera evaluation while also identifying two concrete areas for future robustness work: preserving crossing-event generation when detection and tracking remain stable across the boundary, and maintaining track continuity through occlusion to avoid fragmentation and ID reassignment.

The frozen configuration, Ground Truth, event-matching outputs, manual validation evidence, runtime records, and the evaluation reproducibility check provide a traceable basis for these results.

---

## 10. Appendix

### 10.1 Final Ground Truth files

```text
data/ground_truth/escalator_gt.csv
data/ground_truth/mnd_back_gt.csv
data/ground_truth/twoway_gt.csv
data/ground_truth/virat_gt.csv
data/ground_truth/mnd_61_79_gt.csv
```

### 10.2 Final evaluation configs

```text
configs/eval_escalator.yaml
configs/eval_mnd_back.yaml
configs/eval_twoway.yaml
configs/eval_virat.yaml
configs/eval_mnd_61_79.yaml
```

### 10.3 Final production prediction artifacts

The per-clip prediction event CSVs are local runtime artifacts and are not committed to the
repository (`outputs/` is listed in `.gitignore`). They are produced by running
`scripts/run_production.py` with the evaluation configs listed in §10.2, as described in the
result-reproduction steps in `README.md §7`.

Each clip produces one events CSV under `outputs/final_<clip>/`:

```text
<clip_stem>_events.csv
```

### 10.4 Production manifests

Per-clip production manifests (`production_manifest_<UTC>.json`) are also local runtime artifacts
under `outputs/` and are not committed to the repository. They are generated automatically by
`scripts/run_production.py` alongside the prediction event CSVs.

### 10.5 Evaluation outputs

The `evaluation_summary.csv` and `evaluation_matches.csv` files for each clip are local runtime
artifacts under `outputs/` and are not committed to the repository. They are produced by running
`scripts/evaluate.py` with the frozen `--tolerance-seconds 0.5` against the ground truth files in
§10.1, as described in `README.md §7`.

The evaluation reproducibility check repeated this scoring for all five clips and confirmed that
both generated CSV files were identical to the primary evaluation outputs.

### 10.6 Validation evidence

Representative true-positive checks and the frame sequences used to verify the three false-negative
events were recorded during manual review of the annotated production videos. These frame-level
inspection records are local artifacts and are not committed to the repository.

### 10.7 Counting-line geometry

| Config | Line ID | Point A | Point B | Positive direction |
| --- | --- | --- | --- | --- |
| Escalator | `escalator_main` | `(760, 120)` | `(1120, 850)` | `A_to_B` |
| MND Back | `mnd_back_main` | `(0, 340)` | `(1279, 340)` | `A_to_B` |
| TwoWay | `twoway_main` | `(0, 430)` | `(1279, 430)` | `A_to_B` |
| VIRAT | `virat_main` | `(660, 530)` | `(935, 370)` | `A_to_B` |
| MND 61–79 | `mnd_61_79_main` | `(0, 430)` | `(1279, 430)` | `A_to_B` |

### 10.8 Source and licensing notes

The two MND vehicle clips and the TwoWay traffic clip originate from the Mendeley vehicle-traffic dataset used by the project and are recorded with CC BY 4.0 licensing.

The VIRAT clip originates from the VIRAT Video Dataset and is used under the applicable VIRAT dataset access and use terms.

The escalator clip follows the project’s recorded CrowdLensAI source chain, which attributes the underlying video to the original Vecteezy contributor.

Source videos are not redistributed as part of this report. Provenance and applicable licensing information should remain associated with any externally shared evaluation artifacts.

### 10.9 Evaluation reproducibility reference

Frozen evaluation scoring used:

```text
scripts/evaluate.py
```

with:

```text
matching_tolerance_seconds = 0.5
```

for every clip.

Representative invocation:

```bash
python ./scripts/evaluate.py \
  --predictions "<prediction_events.csv>" \
  --ground-truth "<ground_truth.csv>" \
  --tolerance-seconds 0.5 \
  --output-dir "<evaluation_output_directory>"
```

The evaluation reproducibility check repeated the scoring stage for all five clips into `outputs/evaluation_rerun/` and compared both generated CSV files against the primary evaluation outputs.
