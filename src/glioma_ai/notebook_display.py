"""Show a Matplotlib figure in a notebook regardless of the active backend.

Several package modules select the non-interactive Agg backend on import, which
makes plt.show() a no-op in a kernel. Rendering to PNG bytes and displaying them
works with any backend and inside ipywidgets output areas.
"""

from io import BytesIO

import matplotlib.pyplot as plt


def figure_png(figure, dpi: int = 110) -> bytes:
    """PNG bytes of a figure; the figure is closed afterwards."""
    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(figure)
    return buffer.getvalue()


def show_figure(figure, dpi: int = 110) -> None:
    """Display a figure as a PNG image in the current notebook output."""
    from IPython.display import Image, display

    display(Image(data=figure_png(figure, dpi)))


def figure_widget(render, controls: dict, dpi: int = 110):
    """A widget that redraws ``render(**values)`` in place whenever a control changes.

    ``render`` returns ``(figure or None, text)``. The PNG and the text replace the
    previous ones instead of being appended to an output area, so front ends that
    mishandle ``clear_output`` cannot stack repeated copies.
    """
    import html

    import ipywidgets as widgets

    image = widgets.Image(format="png", layout=widgets.Layout(max_width="100%"))
    caption = widgets.HTML()

    def update(_=None):
        figure, text = render(**{name: control.value for name, control in controls.items()})
        image.layout.display = None if figure is not None else "none"
        if figure is not None:
            image.value = figure_png(figure, dpi)
        caption.value = f"<pre style='font-size:85%'>{html.escape(text)}</pre>"

    for control in controls.values():
        control.observe(update, names="value")
    update()
    return widgets.VBox([image, caption])
