import base64
import io
from typing import Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import flet as ft

from theme import ACCENT, PURPLE, SURFACE, TEXT, TEXT_SECONDARY


def _image(buffer: io.BytesIO, height: int) -> ft.Image:
    data_uri = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
    return ft.Image(src=data_uri, height=height, fit=ft.BoxFit.CONTAIN)


def line_chart(series: dict[str, Iterable[float]], labels: list[str], height: int = 210) -> ft.Image:
    figure, axis = plt.subplots(figsize=(6, 2.3), dpi=120)
    figure.patch.set_facecolor(SURFACE)
    axis.set_facecolor(SURFACE)
    colors = ["#2DD4BF", "#A78BFA", "#F59E0B", "#10B981"]
    for (name, values), color in zip(series.items(), colors):
        axis.plot(range(len(labels)), list(values), label=name, color=color, linewidth=2)
    axis.tick_params(colors="#9CA3AF", labelsize=8)
    axis.set_xticks(range(len(labels)))
    axis.set_xticklabels(labels, rotation=30, ha="right")
    for spine in axis.spines.values():
        spine.set_color("#374151")
    legend = axis.legend(frameon=False, fontsize=8)
    for text in legend.get_texts():
        text.set_color("#FFFFFF")
    figure.tight_layout()
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", facecolor=figure.get_facecolor())
    plt.close(figure)
    return _image(buffer, height)


def pie_chart(values: dict[str, float], height: int = 220) -> ft.Image:
    figure, axis = plt.subplots(figsize=(4, 2.5), dpi=120)
    figure.patch.set_facecolor(SURFACE)
    cleaned = {name: max(value, 0) for name, value in values.items()}
    if sum(cleaned.values()) == 0:
        cleaned = {"Нет данных": 1}
    wedges, labels, _ = axis.pie(cleaned.values(), labels=cleaned.keys(), autopct="%1.0f%%", colors=["#2DD4BF", "#A78BFA", "#F59E0B", "#10B981"], textprops={"color": "#FFFFFF", "fontsize": 9})
    figure.tight_layout()
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", facecolor=figure.get_facecolor())
    plt.close(figure)
    return _image(buffer, height)


def bar_chart(values: dict[str, float], height: int = 210) -> ft.Image:
    figure, axis = plt.subplots(figsize=(6, 2.3), dpi=120)
    figure.patch.set_facecolor(SURFACE)
    axis.set_facecolor(SURFACE)
    axis.bar(list(values.keys()), list(values.values()), color="#2DD4BF")
    axis.tick_params(colors="#9CA3AF", labelsize=8)
    for spine in axis.spines.values():
        spine.set_color("#374151")
    figure.tight_layout()
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", facecolor=figure.get_facecolor())
    plt.close(figure)
    return _image(buffer, height)
