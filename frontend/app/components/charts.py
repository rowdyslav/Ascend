import base64
import io
from typing import Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import flet as ft

from app.theme import ACCENT, MUTED, PURPLE, SUCCESS, SURFACE, TEXT, TEXT_SECONDARY, WARNING

CHART_COLORS = [ACCENT, PURPLE, WARNING, SUCCESS]


def _image(buffer: io.BytesIO, height: int) -> ft.Image:
    data_uri = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
    return ft.Image(src=data_uri, height=height, fit=ft.BoxFit.CONTAIN)


def _new_figure(size: tuple[float, float]):
    """Matplotlib figure/axis with the shared dark styling applied."""
    figure, axis = plt.subplots(figsize=size, dpi=120)
    figure.patch.set_facecolor(SURFACE)
    axis.set_facecolor(SURFACE)
    axis.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    for spine in axis.spines.values():
        spine.set_color(MUTED)
    return figure, axis


def _to_png(figure) -> io.BytesIO:
    figure.tight_layout()
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", facecolor=figure.get_facecolor())
    plt.close(figure)
    return buffer


def line_chart(series: dict[str, Iterable[float]], labels: list[str], height: int = 210) -> ft.Image:
    figure, axis = _new_figure((6, 2.3))
    for (name, values), color in zip(series.items(), CHART_COLORS):
        axis.plot(range(len(labels)), list(values), label=name, color=color, linewidth=2)
    axis.set_xticks(range(len(labels)))
    axis.set_xticklabels(labels, rotation=30, ha="right")
    legend = axis.legend(frameon=False, fontsize=8)
    for text in legend.get_texts():
        text.set_color(TEXT)
    return _image(_to_png(figure), height)


def pie_chart(values: dict[str, float], height: int = 220) -> ft.Image:
    figure, axis = _new_figure((4, 2.5))
    cleaned = {name: max(value, 0) for name, value in values.items()}
    if sum(cleaned.values()) == 0:
        cleaned = {"Нет данных": 1}
    axis.pie(cleaned.values(), labels=cleaned.keys(), autopct="%1.0f%%", colors=CHART_COLORS, textprops={"color": TEXT, "fontsize": 9})
    return _image(_to_png(figure), height)
