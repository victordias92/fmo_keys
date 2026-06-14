import base64
import io
from collections import Counter

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import sqlite3

STATUS_LABELS = {
    "aberta": "Aberta",
    "em andamento": "Em andamento",
    "resolvida": "Resolvida",
}
STATUS_COLORS = {
    "Aberta": "#E53935",
    "Em andamento": "#FB8C00",
    "Resolvida": "#43A047",
}


def _count_by_status(rows: list[sqlite3.Row]) -> dict[str, int]:
    counts = Counter((row["status"] or "aberta").strip().lower() for row in rows)
    return {
        STATUS_LABELS.get(key, key.title()): counts.get(key, 0)
        for key in ("aberta", "em andamento", "resolvida")
    }


def _top_locations(rows: list[sqlite3.Row], limit: int = 5) -> list[tuple[str, int]]:
    counter = Counter((row["location"] or "Sem local").strip() for row in rows)
    return counter.most_common(limit)


def build_failures_chart_src(rows: list[sqlite3.Row]) -> str:
    status_counts = _count_by_status(rows)
    total = sum(status_counts.values())

    fig, axes = plt.subplots(2, 1, figsize=(4.2, 5.2), gridspec_kw={"height_ratios": [1.1, 1]})
    fig.patch.set_facecolor("#FFFFFF")

    if total == 0:
        axes[0].axis("off")
        axes[1].axis("off")
        fig.text(
            0.5,
            0.5,
            "Nenhuma falha registrada",
            ha="center",
            va="center",
            fontsize=13,
            color="#616161",
        )
    else:
        labels = list(status_counts.keys())
        values = list(status_counts.values())
        colors = [STATUS_COLORS.get(label, "#78909C") for label in labels]

        axes[0].pie(
            values,
            labels=labels,
            colors=colors,
            autopct=lambda pct: f"{pct:.0f}%" if pct >= 8 else "",
            startangle=90,
            textprops={"fontsize": 10},
        )
        axes[0].set_title("Por status", fontsize=12, fontweight="bold", pad=10)

        locations = _top_locations(rows)
        if locations:
            loc_labels = [name[:18] + ("..." if len(name) > 18 else "") for name, _ in locations]
            loc_values = [count for _, count in locations]
            bars = axes[1].barh(loc_labels, loc_values, color="#EF5350", alpha=0.85)
            axes[1].invert_yaxis()
            axes[1].set_title("Top locais", fontsize=12, fontweight="bold", pad=10)
            axes[1].set_xlabel("Quantidade", fontsize=10)
            axes[1].tick_params(axis="both", labelsize=9)
            for bar, value in zip(bars, loc_values):
                axes[1].text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2, str(value), va="center", fontsize=9)
        else:
            axes[1].axis("off")

    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
