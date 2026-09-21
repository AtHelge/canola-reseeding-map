import logging
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

logger = logging.getLogger(__name__)


def make_png(
    tiles_gdf: gpd.GeoDataFrame,
    zones_gdf: gpd.GeoDataFrame,
    field_boundary_gdf: gpd.GeoDataFrame,
    out_path: Path,
    target_density: float,
    critical_density: float,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 10))

    has_density = tiles_gdf["density_per_m2"].notna()
    data_tiles = tiles_gdf[has_density]
    no_data_tiles = tiles_gdf[~has_density]

    if not data_tiles.empty:
        data_tiles.plot(
            ax=ax,
            column="density_per_m2",
            cmap="RdYlGn",
            legend=True,
            legend_kwds={"label": "Density (detections / m2)"},
            edgecolor="none",
        )

    if not no_data_tiles.empty:
        no_data_tiles.plot(ax=ax, color="grey", edgecolor="none")

    if not zones_gdf.empty:
        zones_gdf.boundary.plot(ax=ax, color="red", linewidth=1.5)

    field_boundary_gdf.boundary.plot(ax=ax, color="black", linewidth=1.0)

    ax.set_title(
        f"Canola stand density (target {target_density}/m2, critical {critical_density}/m2)"
    )
    ax.set_axis_off()

    legend_handles = [
        Line2D([0], [0], color="red", lw=1.5, label="Gap zone"),
        Line2D([0], [0], color="black", lw=1.0, label="Field boundary"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="grey", markersize=10, label="No data"),
    ]
    ax.legend(handles=legend_handles, loc="lower left")

    _add_north_arrow(ax)
    _add_scale_bar(ax)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved map to %s", out_path)


def _add_north_arrow(ax) -> None:
    ax.annotate(
        "N",
        xy=(0.95, 0.85),
        xytext=(0.95, 0.75),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops=dict(facecolor="black", width=4, headwidth=12),
        ha="center",
        fontsize=12,
    )


def _add_scale_bar(ax) -> None:
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    span = x_max - x_min
    bar_length = _round_to_nice_number(span * 0.2)

    x_start = x_min + span * 0.05
    y_pos = y_min + (y_max - y_min) * 0.05

    ax.plot([x_start, x_start + bar_length], [y_pos, y_pos], color="black", linewidth=3)
    ax.text(
        x_start + bar_length / 2,
        y_pos,
        f"{bar_length:.0f} m",
        ha="center",
        va="bottom",
        fontsize=9,
    )


def _round_to_nice_number(value: float) -> float:
    if value < 1:
        return round(value, 2)

    magnitude = 10 ** (len(str(int(value))) - 1)
    return round(value / magnitude) * magnitude
