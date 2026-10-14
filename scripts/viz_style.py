"""Shared chart styling: one palette, recessive axes, consistent figures."""
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK_2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SURFACE = "#fcfcfb"
# Diverging blue <-> red with a neutral gray midpoint (early ... on time ... late)
DIVERGING = ["#1c5cab", "#6da7ec", "#c3c2b7", "#f0a3a2", "#e66767", "#b82d2d"]
# Sequential blue, light -> dark
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def apply_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "figure.dpi": 110, "savefig.dpi": 150, "savefig.bbox": "tight",
        "font.family": "DejaVu Sans", "font.size": 10,
        "text.color": INK, "axes.labelcolor": INK_2, "axes.titlecolor": INK,
        "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.titlepad": 26, "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.labelcolor": INK_2, "ytick.labelcolor": INK_2,
        "legend.frameon": False, "lines.linewidth": 2,
    })


def money(ax, axis: str = "y", unit: str = "K") -> None:
    """Format an axis as Brazilian reais in thousands (K) or millions (M)."""
    div = 1e3 if unit == "K" else 1e6
    fmt = mtick.FuncFormatter(lambda v, _: f"R${v / div:,.0f}{unit}" if v else "0")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def subtitle(ax, text: str) -> None:
    ax.text(0, 1.01, text, transform=ax.transAxes, color=INK_2, fontsize=9.5, va="bottom")
