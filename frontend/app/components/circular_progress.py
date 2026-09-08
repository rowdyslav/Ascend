import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
import flet as ft

from app.theme import ACCENT, COLORS, PURPLE, SURFACE, TEXT

GRADIENT_COLORS = [ACCENT, PURPLE]  # teal -> purple


def _lerp_hex(color_a: str, color_b: str, t: float) -> str:
    a = color_a.lstrip("#")
    b = color_b.lstrip("#")
    channels = []
    for i in (0, 2, 4):
        ca, cb = int(a[i:i + 2], 16), int(b[i:i + 2], 16)
        channels.append(round(ca + (cb - ca) * t))
    return "#%02X%02X%02X" % tuple(channels)


def _gradient_ring_uri(pct: float, size: int, stroke: int) -> str:
    """Render a teal->purple arc ring to a PNG data URI (matplotlib already a
    project dependency). Track colour matches progress_bg.

    pct is a fraction in [0, 1]."""
    pct = max(0.0, min(1.0, float(pct)))
    segments = 72
    figure = plt.figure(figsize=(3, 3), dpi=100)
    axis = figure.add_axes([0, 0, 1, 1])
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")
    figure.patch.set_alpha(0)
    axis.patch.set_alpha(0)
    stroke_frac = stroke / size
    axis.add_patch(Wedge((0.5, 0.5), 0.46, 0, 360, width=stroke_frac, facecolor=COLORS["progress_bg"]))
    if pct > 0:
        step = 360 / segments
        full_segments = int(pct * segments)
        for i in range(full_segments):
            t = i / (segments - 1)
            axis.add_patch(Wedge(
                (0.5, 0.5), 0.46,
                theta1=90 - (i + 1) * step, theta2=90 - i * step,
                width=stroke_frac, facecolor=_lerp_hex(GRADIENT_COLORS[0], GRADIENT_COLORS[1], t),
            ))
        remainder = pct * 360 - full_segments * step
        if remainder > 0:
            t = pct
            axis.add_patch(Wedge(
                (0.5, 0.5), 0.46,
                theta1=90 - full_segments * step - remainder, theta2=90 - full_segments * step,
                width=stroke_frac, facecolor=_lerp_hex(GRADIENT_COLORS[0], GRADIENT_COLORS[1], t),
            ))
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", transparent=True)
    plt.close(figure)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


class CircularProgress(ft.Stack):
    """Backward-compatible progress ring.

    gradient=False keeps the original single-colour ft.ProgressRing behaviour;
    gradient=True renders a teal->purple arc (matplotlib) for the design system.
    """

    def __init__(self, value: float, size: int = 92, stroke: int = 9,
                 gradient: bool = False, label: str | None = None):
        self.value_pct = max(0.0, min(float(value), 100.0))
        self.size = size
        self.stroke = stroke
        self.gradient = gradient
        self.custom_label = label
        self.ring: ft.ProgressRing | None = None
        self.image: ft.Image | None = None
        self.label = ft.Text(self._label_text(), size=20 if gradient else 18,
                             weight=ft.FontWeight.BOLD, color=TEXT)
        if gradient:
            self.image = ft.Image(src=self._render(), width=size, height=size, fit=ft.BoxFit.CONTAIN)
            super().__init__([self.image, ft.Container(content=self.label, width=size, height=size, alignment=ft.Alignment.CENTER)], width=size, height=size)
        else:
            self.ring = ft.ProgressRing(value=self.value_pct / 100, width=size, height=size,
                                        stroke_width=stroke, color=ACCENT, bgcolor=SURFACE)
            super().__init__([self.ring, ft.Container(content=self.label, width=size, height=size, alignment=ft.Alignment.CENTER)], width=size, height=size)

    def _label_text(self) -> str:
        return self.custom_label if self.custom_label is not None else f"{round(self.value_pct)}%"

    def _render(self) -> str:
        return _gradient_ring_uri(self.value_pct / 100.0, self.size, self.stroke)

    def set_value(self, value: float) -> None:
        self.value_pct = max(0.0, min(float(value), 100.0))
        self.label.value = self._label_text()
        if self.gradient:
            self.image.src = self._render()
        else:
            self.ring.value = self.value_pct / 100
        self.update()
