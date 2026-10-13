"""Slide animation of the section-8 model and the in-place explorer display."""

import matplotlib.pyplot as plt
import numpy as np
import pytest
from PIL import Image
from test_lumiere_biology import synthetic_case

from glioma_ai import lumiere_interactive as li
from glioma_ai import lumiere_movie as lm


def test_frame_sequence_holds_selected_days():
    assert lm.frame_sequence([0, 1, 2], {1.0: 2, 2.0: 1}) == [0, 1, 1, 1, 2, 2]


def test_snapshot_days_must_include_the_observed_day():
    case = synthetic_case()
    daily = li.what_if_run(case, days=np.arange(0, 29))
    assert daily["at_observed_day"] == pytest.approx(li.what_if_run(case)["at_observed_day"])
    with pytest.raises(ValueError, match="observed day"):
        li.what_if_run(case, days=np.arange(0, 20))


def test_movie_writes_a_looping_gif_of_slide_size(tmp_path):
    case = synthetic_case()
    days = np.arange(0, 33, 4, dtype=float)
    movie = lm.write_growth_movie(case, tmp_path, days=days, fps=4, mp4=False)
    assert movie["mp4_skipped"] == "not requested" and set(movie["paths"]) == {"gif"}
    assert movie["pixels"] == (1280, 720)
    assert movie["frames"] == len(days) + int(1.5 * 4) + 2 * 4
    with Image.open(movie["paths"]["gif"]) as gif:
        assert gif.size == (1280, 720) and gif.n_frames > 1 and gif.info.get("loop") == 0


def test_movie_strip_renders_four_frames():
    case = synthetic_case()
    result = li.what_if_run(case, days=np.arange(0, 57, 2))
    figure = lm.movie_strip(case, result)
    assert len(figure.axes) == 4
    plt.close(figure)


def test_figure_widget_redraws_in_place():
    widgets = pytest.importorskip("ipywidgets")
    from glioma_ai.notebook_display import figure_widget

    control = widgets.IntSlider(value=1, min=0, max=3)

    def render(level):
        if level == 0:
            return None, "nothing to draw"
        figure = plt.figure(figsize=(2, 2))
        figure.add_subplot().plot(range(level + 1))
        return figure, f"level {level}"

    box = figure_widget(render, {"level": control})
    image, caption = box.children
    first = image.value
    control.value = 2
    assert image.value != first and "level 2" in caption.value and len(box.children) == 2
    control.value = 0
    assert image.layout.display == "none" and "nothing to draw" in caption.value
