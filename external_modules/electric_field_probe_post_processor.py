import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from scipy.ndimage import binary_dilation

path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\manip\Desktop\AEFI_Acquisition_Exports\2026-07-23_184324_narda_ep600.csv"
fill_path = sys.argv[2] if len(sys.argv) > 2 else None  # optional: complete a cut-short fine scan with a coarse one

df = pd.read_csv(path)
components = [c for c in df.columns if c.startswith("field_component_")]

ok = (df[components].abs() < 500).all(axis=1)
print(f"{(~ok).sum()} outliers dropped / {len(df)} points ({path.split(chr(92))[-1]})")
fine_ok = df[ok]


def local_neighbor_fill(Z, max_iter=10):
    # ponytail: average each hole from its immediate valid neighbors, repeated until stable.
    # Columns that are entirely NaN (scan never reached them) are excluded from both source and
    # target so they stay untouched here — they get rebuilt from the coarse scan afterwards.
    Z = Z.copy()
    empty_cols = np.isnan(Z).all(axis=0)
    sub = Z[:, ~empty_cols]
    for _ in range(max_iter):
        nan_mask = np.isnan(sub)
        if not nan_mask.any():
            break
        border = binary_dilation(~nan_mask) & nan_mask
        if not border.any():
            break
        for i, j in zip(*np.where(border)):
            neighborhood = sub[max(0, i - 1):i + 2, max(0, j - 1):j + 2]
            vals = neighborhood[~np.isnan(neighborhood)]
            if vals.size:
                sub[i, j] = vals.mean()
    Z[:, ~empty_cols] = sub
    return Z


if fill_path:
    coarse = pd.read_csv(fill_path)
    ok_c = (coarse[components].abs() < 500).all(axis=1)
    print(f"{(~ok_c).sum()} outliers dropped / {len(coarse)} points ({fill_path.split(chr(92))[-1]})")
    coarse_ok = coarse[ok_c]

    step = np.diff(np.sort(fine_ok.x.unique())).min()  # fine scan grid pitch (e.g. 8mm)
    lo = min(fine_ok.x.min(), fine_ok.y.min(), coarse_ok.x.min(), coarse_ok.y.min())
    hi = max(coarse_ok.x.max(), coarse_ok.y.max())  # full intended extent comes from the complete coarse scan
    grid = np.arange(lo, hi + step / 2, step)
    XI, YI = np.meshgrid(grid, grid)

    MIRROR_WEIGHT = 0.5  # vs coarse-scan weight (1 - MIRROR_WEIGHT); tune here

    fig, axes = plt.subplots(1, len(components), figsize=(5 * len(components), 4.5))
    for ax, comp in zip(axes.flat, components):
        pivot = fine_ok.pivot(index="y", columns="x", values=comp).reindex(index=grid, columns=grid)
        Z = local_neighbor_fill(pivot.values)
        missing = np.isnan(Z)
        if missing.any():
            # grid is symmetric about (lo+hi)/2 = 635mm here, so column-flip = mirror across x=635
            mirror_vals = Z[:, ::-1]
            coarse_vals = griddata((coarse_ok.x, coarse_ok.y), coarse_ok[comp], (XI, YI), method="cubic")
            has_mirror, has_coarse = ~np.isnan(mirror_vals), ~np.isnan(coarse_vals)
            combined = np.where(
                has_mirror & has_coarse, MIRROR_WEIGHT * mirror_vals + (1 - MIRROR_WEIGHT) * coarse_vals,
                np.where(has_mirror, mirror_vals, coarse_vals),
            )
            Z[missing] = combined[missing]
        im = ax.imshow(Z, extent=(lo, hi, lo, hi), origin="lower", cmap="viridis", aspect="equal")
        plt.colorbar(im, ax=ax)
        ax.set_title(comp)
        ax.set_xlabel("x")
        ax.set_ylabel("y")

    fig.suptitle(f"{path.split(chr(92))[-1]} completed with {fill_path.split(chr(92))[-1]} — {step:g}mm grid")
    plt.tight_layout()
    plt.show()
    raise SystemExit

# --- single-file mode ---
x_ok, y_ok = fine_ok.x, fine_ok.y
lo, hi = min(x_ok.min(), y_ok.min()), max(x_ok.max(), y_ok.max())  # square range covering both axes

fig, axes = plt.subplots(1, len(components), figsize=(5 * len(components), 4.5))
for ax, comp in zip(axes.flat, components):
    sc = ax.scatter(x_ok, y_ok, c=fine_ok[comp], cmap="viridis", s=20)
    plt.colorbar(sc, ax=ax)
    ax.set_title(comp)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal")

fig.suptitle(path.split("\\")[-1])
plt.tight_layout()

xi = np.linspace(lo, hi, 200)
yi = np.linspace(lo, hi, 200)
XI, YI = np.meshgrid(xi, yi)


def fill_nan_with_border_mean(Z):
    nan_mask = np.isnan(Z)
    if not nan_mask.any():
        return Z
    border_mask = binary_dilation(nan_mask) & ~nan_mask
    Z = Z.copy()
    Z[nan_mask] = Z[border_mask].mean()
    return Z


fig2, axes2 = plt.subplots(1, len(components), figsize=(5 * len(components), 4.5))
for ax, comp in zip(axes2.flat, components):
    ZI = griddata((x_ok, y_ok), fine_ok[comp], (XI, YI), method="cubic")
    ZI = fill_nan_with_border_mean(ZI)
    im = ax.imshow(ZI, extent=(lo, hi, lo, hi), origin="lower", cmap="viridis", aspect="equal")
    plt.colorbar(im, ax=ax)
    ax.set_title(f"{comp} (interpolated)")
    ax.set_xlabel("x")
    ax.set_ylabel("y")

fig2.suptitle(path.split("\\")[-1] + " — interpolated")
plt.tight_layout()

fig3, axes3 = plt.subplots(1, len(components), figsize=(5 * len(components), 4.5))
for ax, comp in zip(axes3.flat, components):
    pivot = fine_ok.pivot(index="y", columns="x", values=comp)
    im = ax.imshow(pivot.values, extent=(lo, hi, lo, hi), origin="lower", cmap="viridis", aspect="equal")
    plt.colorbar(im, ax=ax)
    ax.set_title(f"{comp} (raw grid)")
    ax.set_xlabel("x")
    ax.set_ylabel("y")

fig3.suptitle(path.split("\\")[-1] + " — raw grid pixels")
plt.tight_layout()
plt.show()
