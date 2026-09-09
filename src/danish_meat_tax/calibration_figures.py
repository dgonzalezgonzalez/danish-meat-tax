"""Render Stata-computed calibration surfaces; perform no estimation."""
from __future__ import annotations

from pathlib import Path


def render_calibration_surfaces(root: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    import pandas as pd

    data = pd.read_csv(root / "outputs/models/stata/calibration_surfaces.csv")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13})
    fig = plt.figure(figsize=(12, 12))
    panels = [
        (rf"{letter}. Taxable share $f={share}$", r"Persistence, $a$", r"Pass-through, $\lambda$")
        for letter, share in zip("ABCD", ["0.25", "0.50", "0.75", "1.00"])
    ]
    for panel, (title, xlabel, ylabel) in enumerate(panels, 1):
        ax = fig.add_subplot(2, 2, panel, projection="3d")
        rows = data.loc[data.panel == panel].sort_values(["y", "x"])
        if len(rows) != 51 * 51 or rows.duplicated(["x", "y"]).any():
            raise ValueError("Expected a unique 51 by 51 Stata grid for each panel")
        x, y = (rows[c].to_numpy().reshape(51, 51) for c in ["x", "y"])
        z, low, high = (rows[c].to_numpy().reshape(51, 51) for c in ["remaining_gap_dkk_kg", "sensitivity_low", "sensitivity_high"])
        ax.plot_surface(x, y, z, color="#356A91", alpha=.87, shade=False,
                        edgecolor="none", rcount=51, ccount=51)
        for bound in (low, high):
            ax.plot_wireframe(x, y, bound, rstride=10, cstride=10,
                              color="#454545", linewidth=.65, linestyle="--", alpha=.8)
        ax.set_title(title, fontsize=13, pad=18)
        ax.set_xlabel(xlabel, labelpad=5)
        ax.set_ylabel(ylabel, labelpad=5)
        ax.set_zlabel("")
        ax.text2D(.01, .84, r"$R$ (DKK/kg)", transform=ax.transAxes, fontsize=12)
        ax.set(xlim=(0, 1), ylim=(0, 1), zlim=(0, 160),
               xticks=[0, .5, 1], yticks=[0, .5, 1], zticks=[0, 50, 100, 150])
        ax.view_init(elev=24, azim=-125)
        # Both horizontal axes share the near origin; label its zero once.
        ax.set_yticklabels(["", "0.5", "1.0"])
        ax.set_box_aspect((1, 1, .85))
        ax.tick_params(labelsize=11, pad=0)
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.pane.fill = False
            axis._axinfo["grid"].update(color="#dddddd", linewidth=.5)
    fig.legend(handles=[Patch(facecolor="#356A91", label="Point estimate"),
                        Line2D([0], [0], color="#454545", linestyle="--", label="Combined 95% sensitivity bounds")],
               loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(.5, .015))
    fig.subplots_adjust(left=.07, right=.97, top=.95, bottom=.11, wspace=.23, hspace=.28)
    destination = root / "outputs/figures/python/calibration_surfaces.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=240, facecolor="white", bbox_inches="tight", pad_inches=.2)
    plt.close(fig)
    return destination
