import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\manip\Desktop\AEFI_Acquisition_Exports\2026-07-23_184324_narda_ep600.csv"

df = pd.read_csv(path)
df = df.rename(columns={"field_component_0": "field_x", "field_component_1": "field_y", "field_component_2": "field_z"})
components = [c for c in df.columns if c.startswith("field_") and "std_dev" not in c]
ok = (df[components].abs() < 500).all(axis=1)
df = df[ok]

X_SPLIT, Y_SPLIT = 660, 670  # quadrant boundaries: exactly one maximum expected per quadrant
# first estimators given by hand — kept only as reference labels next to the actual quadrant max
TARGETS = {
    "field_y": [(592, 607), (578, 723), (676, 732), (676, 709)],
    "field_z": [(598, 701), (672, 701), (671, 638), (599, 638)],
}
COLORS = {"field_y": "tab:red", "field_z": "tab:orange"}


def find_quadrant_max(df, comp, x_side, y_side):
    mask = (df.x < X_SPLIT if x_side == "lo" else df.x >= X_SPLIT) & (df.y < Y_SPLIT if y_side == "lo" else df.y >= Y_SPLIT)
    sub = df[mask]
    row = sub.loc[sub[comp].idxmax()]
    return row.x, row.y, row[comp]


def nearest_target(targets, x, y):
    return min(targets, key=lambda t: np.hypot(t[0] - x, t[1] - y))


found = {}
for comp, targets in TARGETS.items():
    pts = [find_quadrant_max(df, comp, x_side, y_side) for x_side in ("lo", "hi") for y_side in ("lo", "hi")]
    found[comp] = pts
    centroid = np.mean([(x, y) for x, y, _ in pts], axis=0)
    print(f"{comp}:")
    for (x, y, v) in pts:
        x0, y0 = nearest_target(targets, x, y)
        print(f"  target ({x0},{y0}) -> max at ({x:g},{y:g}) = {v:.2f}")
    print(f"  centroid: ({centroid[0]:g}, {centroid[1]:g})")

c1 = np.mean([(x, y) for x, y, _ in found["field_y"]], axis=0)
c2 = np.mean([(x, y) for x, y, _ in found["field_z"]], axis=0)
print(f"offset between centroids (compo1 vs compo2): {np.hypot(*(c1 - c2)):.2f} mm")

fig, axes = plt.subplots(1, len(components), figsize=(5.5 * len(components), 5))
for ax, comp in zip(axes.flat, components):
    pivot = df.pivot(index="y", columns="x", values=comp)
    step = np.diff(pivot.columns).min()  # grid pitch, for half-pixel centering
    extent = (
        pivot.columns.min() - step / 2, pivot.columns.max() + step / 2,
        pivot.index.min() - step / 2, pivot.index.max() + step / 2,
    )
    im = ax.imshow(pivot.values, extent=extent, origin="lower", cmap="viridis", aspect="equal")
    plt.colorbar(im, ax=ax)

    for target_comp, pts in found.items():
        xs, ys = zip(*[(x, y) for x, y, _ in pts])
        ax.scatter(xs, ys, color=COLORS[target_comp], marker="x", s=120, linewidths=2.5, label=f"{target_comp} maxima")
        centroid = np.mean([(x, y) for x, y, _ in pts], axis=0)
        ax.scatter(*centroid, color=COLORS[target_comp], marker="*", s=300, edgecolors="black", label=f"{target_comp} centroid")

    ax.set_title(f"{comp} (raw grid)")
    ax.set_xlabel("x")
    ax.set_ylabel("y")

axes.flat[0].legend(fontsize=8)
fig.suptitle(path.split("\\")[-1] + " — raw grid pixels")
plt.tight_layout()
plt.show()
