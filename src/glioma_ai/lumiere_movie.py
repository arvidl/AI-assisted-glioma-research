"""Slide-ready animation of the section-8 model on LUMIERE Patient-048 (notebook 03).

Each frame shows the week-045 CT1 plane with the simulated density, its two
readings (core and T2/FLAIR) and the week-049 automated labels as the target,
beside the reading areas over time. Only day 28 has a scan; later days are drawn
as projections. Frames are rendered once with Agg and written as an animated GIF
(Pillow) and, when an ffmpeg executable is available, as an H.264 MP4. The
images are LUMIERE data under the authors' non-commercial condition, and the
footer of every frame says so.
"""

import shutil
import subprocess
import textwrap
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from PIL import Image

from glioma_ai.lumiere_dynamics import SliceCase, _extent
from glioma_ai.lumiere_interactive import INITIAL_VISIT, OBSERVED_DAY, what_if_run

MOVIE_DAYS = np.arange(0, 57, dtype=float)
CORE_COLOUR, T2_COLOUR = "#f29b38", "#48dbbf"
FOOTER = (
    "LUMIERE Patient-048 (Suter et al., Sci Data 2022; non-commercial use), one axial plane; "
    "automated MONAI labels, not expert masks. Model: proliferation–invasion equation with "
    "published median D and ρ (Wang et al. 2009) – a conditional illustration, not a prediction."
)


def _crop(case: SliceCase, result: dict, pad: int = 22) -> tuple[tuple, tuple]:
    split = result["split"]
    box = np.argwhere(
        (result["run"].density[0] > 0) | split["local_whole"] | split["distant_whole"]
    )
    x = (max(box[:, 0].min() - pad, 0) * case.dx_mm, (box[:, 0].max() + pad) * case.dx_mm)
    y = (max(box[:, 1].min() - pad, 0) * case.dy_mm, (box[:, 1].max() + pad) * case.dy_mm)
    return x, y


def draw_movie_frame(figure, case: SliceCase, result: dict, day: float) -> None:
    """One frame at ``day``: anatomy with density and readings, and the area curves so far."""
    run, split, settings = result["run"], result["split"], result["settings"]
    index = int(np.argmin(np.abs(run.days - day)))
    shown = float(run.days[index])
    extent = _extent(case)
    xlim, ylim = _crop(case, result)
    grid = figure.add_gridspec(1, 2, width_ratios=[1.0, 1.0], wspace=0.32)
    anatomy, curves = figure.add_subplot(grid[0, 0]), figure.add_subplot(grid[0, 1])
    bar = anatomy.inset_axes([1.03, 0.0, 0.04, 1.0])

    visit = case.metadata["visit_names"].index(INITIAL_VISIT)
    windows = case.metadata.get("display_windows_p01_p99")
    low, high = windows[visit] if windows else (None, None)
    anatomy.imshow(
        case.images[visit].T, origin="lower", extent=extent, cmap="gray", vmin=low, vmax=high
    )
    density = anatomy.imshow(
        np.ma.masked_less(run.density[index], 0.02).T,
        origin="lower",
        extent=extent,
        cmap="magma",
        vmin=0,
        vmax=1,
        alpha=0.8,
    )
    target = (
        (split["local_core"] | split["distant_core"], CORE_COLOUR),
        (split["local_whole"] | split["distant_whole"], T2_COLOUR),
    )
    for mask, colour in target:
        if mask.any():
            anatomy.contour(
                mask.T,
                levels=[0.5],
                extent=extent,
                colors=colour,
                linewidths=1.2,
                linestyles="dashed",
            )
    for level, colour in (
        (settings["core_threshold"], CORE_COLOUR),
        (settings["t2_threshold"], T2_COLOUR),
    ):
        mask = run.density[index] >= level
        if mask.any():
            anatomy.contour(mask.T, levels=[0.5], extent=extent, colors=colour, linewidths=2.2)
    if split["distant_whole"].any():
        cx, cy = np.argwhere(split["distant_whole"]).mean(axis=0)
        anatomy.annotate(
            "distant lesion\nat week 049",
            xy=(cx * case.dx_mm, cy * case.dy_mm),
            xytext=(xlim[0] + 3, ylim[0] + 4),
            color="white",
            fontsize=10,
            bbox={"facecolor": "black", "alpha": 0.6, "edgecolor": "none", "pad": 2},
            arrowprops={"arrowstyle": "->", "color": "white", "lw": 1},
        )
    if shown == 0:
        status = "week-045 scan: labels seed the model"
    elif shown < OBSERVED_DAY:
        status = "after the week-045 scan"
    elif shown == OBSERVED_DAY:
        status = "week-049 scan: compare with dashes"
    else:
        status = "projection: no scan on this day"
    backing = {"facecolor": "black", "alpha": 0.6, "edgecolor": "none", "pad": 3}
    anatomy.text(
        0.02,
        0.97,
        f"Day {shown:.0f}",
        transform=anatomy.transAxes,
        color="white",
        fontsize=22,
        fontweight="bold",
        va="top",
        bbox=backing,
    )
    anatomy.text(
        0.02,
        0.85,
        status,
        transform=anatomy.transAxes,
        color="white",
        fontsize=10.5,
        va="top",
        bbox=backing,
    )
    anatomy.set_xlim(*xlim)
    anatomy.set_ylim(*ylim)
    anatomy.set_aspect("equal")
    anatomy.set_xticks([])
    anatomy.set_yticks([])
    anatomy.set_title("Week-045 CT1 with simulated tumour-cell density", fontsize=12, loc="left")
    figure.colorbar(density, cax=bar, label="Density proxy c (0–1)")

    observed = result["observed"]
    pixel_cm2 = 0.01
    days_so_far = run.days[: index + 1]
    for key, colour, name in (
        ("core", CORE_COLOUR, "core reading (c ≥ {:.2f})"),
        ("t2", T2_COLOUR, "T2/FLAIR reading (c ≥ {:.2f})"),
    ):
        level = settings["core_threshold" if key == "core" else "t2_threshold"]
        series = result[f"{key}_area_mm2"] * pixel_cm2
        curves.plot(run.days, series, color=colour, lw=1, alpha=0.25)
        curves.plot(
            days_so_far,
            series[: index + 1],
            color=colour,
            lw=2.6,
            label="model " + name.format(level),
        )
        curves.plot(
            [0, OBSERVED_DAY],
            [observed[f"start_{key}_mm2"] * pixel_cm2, observed[f"later_{key}_mm2"] * pixel_cm2],
            ls="none",
            marker="o" if key == "core" else "s",
            ms=9,
            color=colour,
            markeredgecolor="black",
        )
    curves.axvspan(OBSERVED_DAY, run.days[-1], color="#eeeeee", zorder=0)
    curves.axvline(shown, color="black", lw=1, ls=":")
    curves.text(
        OBSERVED_DAY + 1,
        0.03,
        "projection: no scans",
        transform=curves.get_xaxis_transform(),
        fontsize=10,
    )
    curves.set_xlim(run.days[0], run.days[-1])
    curves.set_xlabel("Days after the week-045 scan", fontsize=11)
    curves.set_ylabel("Area on this plane (cm²)", fontsize=11)
    curves.set_title("Readings over time", fontsize=12, loc="left")
    handles = curves.get_legend_handles_labels()[0] + [
        Line2D(
            [],
            [],
            ls="none",
            marker="o",
            ms=8,
            color=CORE_COLOUR,
            markeredgecolor="black",
            label="labelled core, weeks 045 and 049",
        ),
        Line2D(
            [],
            [],
            ls="none",
            marker="s",
            ms=8,
            color=T2_COLOUR,
            markeredgecolor="black",
            label="labelled whole tumour, weeks 045 and 049",
        ),
        Line2D([], [], color="grey", ls="dashed", label="week-049 labels on the image"),
    ]
    top = max(float(result["t2_area_mm2"].max()), observed["later_t2_mm2"]) * pixel_cm2
    curves.set_ylim(0, 1.08 * top)
    curves.legend(
        handles=handles,
        fontsize=9,
        loc="upper center",
        ncols=2,
        bbox_to_anchor=(0.45, -0.13),
        frameon=False,
    )
    figure.suptitle(
        "A growth model seeded from one MRI visit, compared with the next",
        fontsize=15,
        x=0.02,
        ha="left",
    )
    figure.text(0.02, 0.012, "\n".join(textwrap.wrap(FOOTER, 190)), fontsize=8, color="#444444")


def render_frames(case: SliceCase, result: dict, days, *, size=(12.8, 7.2), dpi=100) -> list:
    """RGB frames (uint8 arrays) for each day, rendered with Agg."""
    frames = []
    for day in days:
        figure = Figure(figsize=size, dpi=dpi)
        canvas = FigureCanvasAgg(figure)
        figure.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.25)
        draw_movie_frame(figure, case, result, day)
        canvas.draw()
        frames.append(np.asarray(canvas.buffer_rgba())[..., :3].copy())
    return frames


def frame_sequence(days, holds: dict[float, int]) -> list[float]:
    """Days in order, with each day in ``holds`` repeated that many extra times."""
    sequence = []
    for day in days:
        sequence.extend([float(day)] * (1 + holds.get(float(day), 0)))
    return sequence


def write_growth_movie(
    case: SliceCase,
    output: Path,
    name: str = "lumiere_growth",
    *,
    days=MOVIE_DAYS,
    fps: int = 8,
    dpi: int = 100,
    mp4: bool = True,
    **settings,
) -> dict:
    """Write ``name``.gif (and ``name``.mp4 with ffmpeg) of the section-8 model.

    Day 28 and the last day are held for 1.5 and 2 seconds. Returns the paths,
    the frame count, the pixel size and the settings used.
    """
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    result = what_if_run(case, days=np.asarray(days, dtype=float), **settings)
    sequence = frame_sequence(days, {float(OBSERVED_DAY): int(1.5 * fps), float(days[-1]): 2 * fps})
    unique = sorted(set(sequence))
    rendered = dict(zip(unique, render_frames(case, result, unique, dpi=dpi), strict=True))
    frames = [rendered[day] for day in sequence]
    height, width = frames[0].shape[:2]
    paths = {}
    gif = output / f"{name}.gif"
    images = [
        Image.fromarray(frame).convert("P", palette=Image.Palette.ADAPTIVE, colors=192)
        for frame in frames
    ]
    images[0].save(
        gif,
        save_all=True,
        append_images=images[1:],
        duration=int(1000 / fps),
        loop=0,
        optimize=True,
    )
    paths["gif"] = gif
    ffmpeg = shutil.which("ffmpeg")
    if mp4 and ffmpeg:
        movie = output / f"{name}.mp4"
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-s",
                f"{width}x{height}",
                "-r",
                str(fps),
                "-i",
                "-",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                "18",
                "-movflags",
                "+faststart",
                str(movie),
            ],
            input=b"".join(frame.tobytes() for frame in frames),
            check=True,
        )
        paths["mp4"] = movie
    return {
        "paths": paths,
        "frames": len(frames),
        "pixels": (width, height),
        "fps": fps,
        "mp4_skipped": None
        if "mp4" in paths
        else ("not requested" if not mp4 else "no ffmpeg executable found"),
        "settings": result["settings"],
        "result": result,
    }


def movie_strip(case: SliceCase, result: dict, days=(0, 14, 28, 56)) -> Figure:
    """A static strip of movie frames for notebooks and printed handouts."""
    frames = render_frames(case, result, days, dpi=70)
    figure = Figure(figsize=(16, 4.4 * len(days) / 2))
    FigureCanvasAgg(figure)
    axes = figure.subplots(len(days) // 2, 2) if len(days) > 2 else figure.subplots(1, len(days))
    for axis, frame in zip(np.ravel(axes), frames, strict=True):
        axis.imshow(frame)
        axis.axis("off")
    figure.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0.01, hspace=0.01)
    return figure
