"""Interactive ground-truth annotation tool for video line crossings.

The tool is intentionally independent of detectors, trackers, crossing logic,
and T06. It uses OpenCV only for video playback and display.
"""

from __future__ import annotations

import argparse
import csv
import logging
import math
from dataclasses import dataclass
from pathlib import Path

import cv2

logger = logging.getLogger(__name__)

# Fallback FPS based on T06 policy
DEFAULT_FALLBACK_FPS = 25.0


# Named constants for platform-dependent key codes returned by cv2.waitKeyEx
KEY_LEFT_CODES = frozenset({2424832, 65361})
KEY_RIGHT_CODES = frozenset({2555904, 65363})


def normalize_key(key: int) -> str | int:
    """Normalize a waitKeyEx key code for portable cross-platform matching.

    Maps platform-specific arrow codes to semantic names ('left', 'right')
    and lowercases ASCII characters so 'm'/'M', 'u'/'U', 'q'/'Q' behave identically.
    """
    if key in KEY_LEFT_CODES:
        return "left"
    if key in KEY_RIGHT_CODES:
        return "right"
    if 0 <= key < 256:
        return chr(key).lower()
    return key


CSV_FIELDNAMES = [
    "frame_idx",
    "timestamp_seconds",
    "class_name",
    "direction",
    "line_id",
    "video_name",
]


@dataclass(frozen=True)
class AnnotationEvent:
    """A manually annotated line-crossing event."""

    frame_idx: int
    timestamp_seconds: float
    class_name: str
    direction: str
    line_id: str
    video_name: str


@dataclass(frozen=True)
class DisplayLine:
    """Display-only counting-line metadata for the annotation window."""

    point_a: tuple[int, int]
    point_b: tuple[int, int]
    positive_direction: str
    line_id: str


def is_invalid_fps(fps: float) -> bool:
    """Return True when *fps* cannot be used for timestamps or wait delays.

    Zero, negative, NaN, and ±infinity are all invalid.  ``NaN <= 0`` is
    False, so a ``fps <= 0`` check alone would let non-finite metadata
    through to ``round(1000 / fps)``.
    """
    return not math.isfinite(fps) or fps <= 0


def resolve_annotation_fps(raw_fps: float) -> float:
    """Return a usable playback FPS, falling back when container metadata is invalid."""
    if is_invalid_fps(raw_fps):
        return DEFAULT_FALLBACK_FPS
    return float(raw_fps)


def annotation_wait_delay_ms(fps: float, *, playing: bool) -> int:
    """Return the ``cv2.waitKeyEx`` delay used by the annotation playback loop.

    Callers must pass a resolved, valid FPS (see :func:`resolve_annotation_fps`).
    """
    if not playing:
        return 0
    return max(1, round(1000 / fps))


def calculate_timestamp(frame_idx: int, fps: float) -> float:
    """Calculate elapsed time from a zero-based frame index."""
    if is_invalid_fps(fps):
        return 0.0

    return round(frame_idx / fps, 6)


def save_events_to_csv(
    events: list[AnnotationEvent],
    output_path: str | Path,
) -> None:
    """Save annotation events using the official T13 CSV schema."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()

        for event in events:
            writer.writerow(
                {
                    "frame_idx": event.frame_idx,
                    "timestamp_seconds": event.timestamp_seconds,
                    "class_name": event.class_name,
                    "direction": event.direction,
                    "line_id": event.line_id,
                    "video_name": event.video_name,
                }
            )


def record_event(
    event: AnnotationEvent,
    events_list: list[AnnotationEvent],
    out_path: str | Path,
) -> None:
    """Append event and incrementally auto-save to prevent data loss on crash."""
    events_list.append(event)
    save_events_to_csv(events_list, out_path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments and document keyboard controls."""
    parser = argparse.ArgumentParser(
        description=(
            "Interactive Ground Truth Annotation Tool. "
            "Keyboard controls: SPACE=pause/resume, "
            "RIGHT=next frame, LEFT=previous frame, "
            "M=mark crossing, U=undo, Q or ESC=save and quit."
        )
    )
    parser.add_argument(
        "--video",
        required=True,
        type=Path,
        help="Path to the input video file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to the output Ground Truth CSV file.",
    )
    parser.add_argument(
        "--display-line-a",
        nargs=2,
        type=int,
        metavar=("X", "Y"),
        help="Display-only point A coordinates for the counting line.",
    )
    parser.add_argument(
        "--display-line-b",
        nargs=2,
        type=int,
        metavar=("X", "Y"),
        help="Display-only point B coordinates for the counting line.",
    )
    parser.add_argument(
        "--display-positive-direction",
        choices=("A_to_B", "B_to_A"),
        help="Display-only IN direction using the configured signed-side convention.",
    )
    parser.add_argument(
        "--display-line-id",
        help="Display-only counting-line identifier.",
    )

    args = parser.parse_args(argv)
    display_values = (
        args.display_line_a,
        args.display_line_b,
        args.display_positive_direction,
        args.display_line_id,
    )

    if any(value is not None for value in display_values) and not all(
        value is not None for value in display_values
    ):
        parser.error(
            "display-line mode requires --display-line-a, --display-line-b, "
            "--display-positive-direction, and --display-line-id"
        )

    args.display_line = None
    if args.display_line_a is not None:
        point_a = tuple(args.display_line_a)
        point_b = tuple(args.display_line_b)

        if point_a == point_b:
            parser.error("display-line points A and B must be distinct")
        if not args.display_line_id.strip():
            parser.error("--display-line-id must not be empty")

        args.display_line = DisplayLine(
            point_a=point_a,
            point_b=point_b,
            positive_direction=args.display_positive_direction,
            line_id=args.display_line_id,
        )

    return args


def ask_crossing_details() -> tuple[str, str, str] | None:
    """Read and validate class, direction, and line information."""
    print("\n[!] Check the terminal — waiting for input below.")
    class_name = input("class_name: ").strip()
    if not class_name:
        print("Annotation cancelled: class_name cannot be empty.")
        return None

    direction = input("direction [IN/OUT]: ").strip().upper()
    if direction not in {"IN", "OUT"}:
        print("Annotation cancelled: direction must be IN or OUT.")
        return None

    line_id = input("line_id: ").strip()
    if not line_id:
        print("Annotation cancelled: line_id cannot be empty.")
        return None

    return class_name, direction, line_id


def clip_infinite_line_to_frame(
    point_a: tuple[int, int],
    point_b: tuple[int, int],
    frame_width: int,
    frame_height: int,
) -> tuple[tuple[int, int], tuple[int, int]] | None:
    """Clip the infinite line through A and B to the visible frame rectangle."""
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError("frame dimensions must be positive")

    ax, ay = point_a
    bx, by = point_b
    dx = bx - ax
    dy = by - ay

    if dx == 0 and dy == 0:
        raise ValueError("line points A and B must be distinct")

    max_x = frame_width - 1
    max_y = frame_height - 1
    intersections: list[tuple[float, float, float]] = []

    def add_intersection(t: float, x: float, y: float) -> None:
        epsilon = 1e-9
        if not (-epsilon <= x <= max_x + epsilon and -epsilon <= y <= max_y + epsilon):
            return
        if any(
            abs(x - old_x) <= epsilon and abs(y - old_y) <= epsilon
            for _, old_x, old_y in intersections
        ):
            return
        intersections.append((t, min(max(x, 0.0), max_x), min(max(y, 0.0), max_y)))

    if dx != 0:
        for x in (0.0, float(max_x)):
            t = (x - ax) / dx
            add_intersection(t, x, ay + t * dy)

    if dy != 0:
        for y in (0.0, float(max_y)):
            t = (y - ay) / dy
            add_intersection(t, ax + t * dx, y)

    if len(intersections) < 2:
        return None

    intersections.sort(key=lambda item: item[0])
    _, start_x, start_y = intersections[0]
    _, end_x, end_y = intersections[-1]
    return (round(start_x), round(start_y)), (round(end_x), round(end_y))


def calculate_in_arrow(
    point_a: tuple[int, int],
    point_b: tuple[int, int],
    positive_direction: str,
    arrow_length: float = 70.0,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return an IN arrow crossing from the OUT side to the configured IN side."""
    ax, ay = point_a
    bx, by = point_b
    dx = bx - ax
    dy = by - ay
    line_length = math.hypot(dx, dy)

    if line_length == 0:
        raise ValueError("line points A and B must be distinct")
    if positive_direction not in {"A_to_B", "B_to_A"}:
        raise ValueError("positive_direction must be A_to_B or B_to_A")

    # (-dy, dx) points toward positive signed_distance for directed A→B.
    normal_x = -dy / line_length
    normal_y = dx / line_length
    if positive_direction == "B_to_A":
        normal_x = -normal_x
        normal_y = -normal_y

    center_x = (ax + bx) / 2
    center_y = (ay + by) / 2
    half_length = arrow_length / 2
    start = (
        round(center_x - normal_x * half_length),
        round(center_y - normal_y * half_length),
    )
    end = (
        round(center_x + normal_x * half_length),
        round(center_y + normal_y * half_length),
    )
    return start, end


def _draw_outlined_text(
    frame,
    text: str,
    origin: tuple[int, int],
    scale: float,
    color: tuple[int, int, int],
) -> None:
    """Draw compact overlay text that remains readable on varied video content."""
    cv2.putText(
        frame,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (0, 0, 0),
        4,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        2,
        cv2.LINE_AA,
    )


def draw_display_line(frame, display_line: DisplayLine) -> None:
    """Draw counting-line guidance in-place on an already copied display frame."""
    frame_height, frame_width = frame.shape[:2]
    visible_line = clip_infinite_line_to_frame(
        display_line.point_a,
        display_line.point_b,
        frame_width,
        frame_height,
    )

    if visible_line is not None:
        cv2.line(frame, visible_line[0], visible_line[1], (0, 255, 255), 1, cv2.LINE_AA)

    cv2.arrowedLine(
        frame,
        display_line.point_a,
        display_line.point_b,
        (255, 0, 255),
        2,
        cv2.LINE_AA,
        tipLength=0.06,
    )

    ax, ay = display_line.point_a
    bx, by = display_line.point_b
    _draw_outlined_text(frame, "A", (ax + 6, max(18, ay - 8)), 0.65, (255, 0, 255))
    _draw_outlined_text(frame, "B", (bx + 6, min(frame_height - 8, by + 22)), 0.65, (255, 0, 255))

    _draw_outlined_text(
        frame,
        f"Line: {display_line.line_id}",
        (10, frame_height - 12),
        0.55,
        (0, 255, 255),
    )

    arrow_start, arrow_end = calculate_in_arrow(
        display_line.point_a,
        display_line.point_b,
        display_line.positive_direction,
    )
    cv2.arrowedLine(
        frame,
        arrow_start,
        arrow_end,
        (255, 255, 0),
        2,
        cv2.LINE_AA,
        tipLength=0.25,
    )
    _draw_outlined_text(
        frame,
        "IN",
        (arrow_end[0] + 6, max(18, arrow_end[1] - 6)),
        0.65,
        (255, 255, 0),
    )


def draw_overlay(
    frame,
    frame_idx: int,
    total_frames: int,
    playing: bool,
    event_count: int,
    display_line: DisplayLine | None = None,
):
    """Draw current playback state on the displayed frame."""
    status = "PLAYING" if playing else "PAUSED"
    text_lines = [
        f"Frame: {frame_idx}/{max(total_frames - 1, 0)}",
        f"Status: {status}",
        f"Annotations: {event_count}",
        "SPACE pause/resume | LEFT/RIGHT step | M mark | U undo | Q quit",
    ]

    result = frame.copy()

    for index, text in enumerate(text_lines):
        cv2.putText(
            result,
            text,
            (15, 30 + index * 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    if display_line is not None:
        draw_display_line(result, display_line)

    return result


def run_annotation(
    video_path: Path,
    output_path: Path,
    display_line: DisplayLine | None = None,
) -> None:
    """Run the interactive OpenCV annotation loop."""
    capture = cv2.VideoCapture(str(video_path))

    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    raw_fps = float(capture.get(cv2.CAP_PROP_FPS))
    if is_invalid_fps(raw_fps):
        logger.warning(
            "Invalid or zero FPS (%s) reported by video container. Falling back to default: %.1f FPS",
            raw_fps,
            DEFAULT_FALLBACK_FPS,
        )
    fps = resolve_annotation_fps(raw_fps)

    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    video_name = video_path.name
    events: list[AnnotationEvent] = []

    current_idx = 0
    playing = True
    window_name = "Ground Truth Annotation"

    last_decoded_idx = -1

    try:
        while True:
            if current_idx != last_decoded_idx + 1:
                capture.set(cv2.CAP_PROP_POS_FRAMES, current_idx)

            success, frame = capture.read()

            if not success:
                break

            last_decoded_idx = current_idx

            displayed = draw_overlay(
                frame=frame,
                frame_idx=current_idx,
                total_frames=total_frames,
                playing=playing,
                event_count=len(events),
                display_line=display_line,
            )
            cv2.imshow(window_name, displayed)

            delay = annotation_wait_delay_ms(fps, playing=playing)
            key = cv2.waitKeyEx(delay)

            if key == -1:
                if playing:
                    if current_idx + 1 < total_frames:
                        current_idx += 1
                    else:
                        playing = False
                continue

            action = normalize_key(key)

            if action in ("q", "\x1b"):
                break

            if action == " ":
                playing = not playing
                continue

            if action == "left":
                current_idx = max(0, current_idx - 1)
                playing = False
                continue

            if action == "right":
                current_idx = min(max(total_frames - 1, 0), current_idx + 1)
                playing = False
                continue

            if action == "m":
                was_playing = playing
                playing = False
                print(f"\nMarking crossing at frame {current_idx}")
                details = ask_crossing_details()
                playing = was_playing

                if details is not None:
                    class_name, direction, line_id = details
                    event = AnnotationEvent(
                        frame_idx=current_idx,
                        timestamp_seconds=calculate_timestamp(current_idx, fps),
                        class_name=class_name,
                        direction=direction,
                        line_id=line_id,
                        video_name=video_name,
                    )
                    record_event(event, events, output_path)
                    print("Annotation added and auto-saved.")

                continue

            if action == "u":
                if events:
                    removed = events.pop()
                    save_events_to_csv(events, output_path)
                    print(f"Removed annotation at frame {removed.frame_idx} and updated CSV.")
                else:
                    print("No annotation to remove.")

                continue

            if playing:
                if current_idx + 1 < total_frames:
                    current_idx += 1
                else:
                    playing = False

    finally:
        capture.release()
        cv2.destroyAllWindows()
        save_events_to_csv(events, output_path)
        print(f"Saved {len(events)} annotation(s) to {output_path}")


def main() -> None:
    """Validate inputs and start the annotation tool."""
    args = parse_args()

    if not args.video.is_file():
        raise FileNotFoundError(f"Video file does not exist: {args.video}")

    run_annotation(
        video_path=args.video,
        output_path=args.output,
        display_line=args.display_line,
    )


if __name__ == "__main__":
    main()
