import sys
import numpy as np
import pandas as pd

path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\manip\Desktop\AEFI_Acquisition_Exports\2026-07-23_184324_narda_ep600_10kHz_frequency-corrected.csv"
out_path = path.rsplit(".", 1)[0] + "_padded_square.csv"

df = pd.read_csv(path)

step = np.diff(np.sort(df.x.unique())).min()
lo = min(df.x.min(), df.y.min())
hi = max(df.x.max(), df.y.max())
grid = np.arange(lo, hi + step / 2, step)

full = pd.MultiIndex.from_product([grid, grid], names=["x", "y"]).to_frame(index=False)
padded = full.merge(df, on=["x", "y"], how="left")

padded["scan_id"] = df.scan_id.iloc[0]
new_rows = padded.point_index.isna()
padded.loc[new_rows, "point_index"] = np.arange(new_rows.sum()) + df.point_index.max() + 1
padded["point_index"] = padded.point_index.astype(int)

padded.to_csv(out_path, index=False)
print(f"{len(df)} -> {len(padded)} points ({new_rows.sum()} added as NaN), square {lo:g}-{hi:g}mm step {step:g}mm")
print(f"written to {out_path}")
