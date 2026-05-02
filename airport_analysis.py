"""
airport_analysis.py
===================
Full pipeline for airport passenger-flow analysis.

Steps
-----
  1. Load wifi_logs.csv + access_points.csv
  2. Filter out machine / system accounts
  3. Bin events into 5-min time windows → people count per AP per window
  4. Build per-person movement sequences  → transition matrix (Markov chain)
  5. Simulate 60-min forward predictions from any chosen snapshot
  6. Detect congestion warnings (count > AP threshold)
  7. Export all figures as PNG and print a summary report

Usage
-----
  python airport_analysis.py
"""

import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings("ignore")

plt.rcParams.update({
    "figure.dpi":       130,
    "figure.facecolor": "#0f1117",
    "axes.facecolor":   "#1a1d27",
    "axes.edgecolor":   "#3a3d4d",
    "axes.labelcolor":  "#c8cad4",
    "xtick.color":      "#8a8d9a",
    "ytick.color":      "#8a8d9a",
    "text.color":       "#e0e2ea",
    "grid.color":       "#2e3040",
    "grid.linestyle":   "--",
    "grid.alpha":       0.6,
    "font.family":      "DejaVu Sans",
})

ACCENT  = "#4f9cf9"
WARNING = "#f97b4f"
SUCCESS = "#4fca8c"
PURPLE  = "#a374f9"

# ──────────────────────────────────────────────────────────────────────────────
# STEP 1 – LOAD DATA
# ──────────────────────────────────────────────────────────────────────────────

print("=" * 62)
print("  AIRPORT PASSENGER FLOW ANALYSIS")
print("=" * 62)

logs = pd.read_csv("data/wifi_logs.csv", parse_dates=["timestamp"])
aps  = pd.read_csv("data/access_points.csv")

ap_threshold = dict(zip(aps["ap_id"], aps["threshold"]))
ap_name      = dict(zip(aps["ap_id"], aps["name"]))
ap_zone      = dict(zip(aps["ap_id"], aps["zone"]))

print(f"\n[1] Loaded {len(logs):,} log entries from {logs['mac'].nunique():,} unique MACs")


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2 – MACHINE ACCOUNT FILTERING
# ──────────────────────────────────────────────────────────────────────────────
# Detection rules (applied to the 'identity' field):
#   R1 – email domain is a known infrastructure domain
#   R2 – identity starts with a known machine prefix (PRINTER-, CAMERA-, DISPLAY-)
#   R3 – identity is a pure hostname pattern  (all-caps with hyphens/digits)
#   R4 – identity is NaN but the MAC OUI matches the reserved machine block (AA:BB:*)

INFRA_DOMAINS    = {"airport-systems.com", "airport.aero", "groundops.local"}
MACHINE_PREFIXES = ("PRINTER-", "CAMERA-", "DISPLAY-", "SCANNER-", "KIOSK-", "AP-MGMT-")
MACHINE_HOSTNAME = re.compile(r"^[A-Z][A-Z0-9\-]+$")   # e.g. CAMERA-GATE-A1
MACHINE_OUI      = "AA:BB:"                              # reserved for generated machines

def is_machine(row) -> bool:
    identity = str(row["identity"]) if pd.notna(row["identity"]) else ""
    if identity == "nan":
        return row["mac"].startswith(MACHINE_OUI)
    domain = identity.split("@")[-1] if "@" in identity else ""
    if domain in INFRA_DOMAINS:
        return True
    if identity.startswith(MACHINE_PREFIXES):
        return True
    if MACHINE_HOSTNAME.match(identity) and "-" in identity:
        return True
    return row["mac"].startswith(MACHINE_OUI)

logs["is_machine"] = logs.apply(is_machine, axis=1)

machines = logs[logs["is_machine"]]
humans   = logs[~logs["is_machine"]].copy()

print(f"\n[2] Machine-account filtering")
print(f"    ├─ Machine events : {len(machines):,}  ({machines['mac'].nunique()} devices)")
print(f"    └─ Human events   : {len(humans):,}  ({humans['mac'].nunique()} devices)")


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3 – TIME-WINDOWED OCCUPANCY  (5-minute bins)
# ──────────────────────────────────────────────────────────────────────────────
BIN_MINUTES = 5

humans["window"] = humans["timestamp"].dt.floor(f"{BIN_MINUTES}min")

# For each (window, ap_id) count unique MACs  → unique people
occupancy = (
    humans.groupby(["window", "ap_id"])["mac"]
    .nunique()
    .reset_index()
    .rename(columns={"mac": "count"})
)

# Pivot: rows = time windows, cols = ap_ids
occ_pivot = occupancy.pivot_table(
    index="window", columns="ap_id", values="count", fill_value=0
)
occ_pivot = occ_pivot.sort_index()

print(f"\n[3] Occupancy matrix: {len(occ_pivot)} time windows × {len(occ_pivot.columns)} APs")


# ──────────────────────────────────────────────────────────────────────────────
# STEP 4 – MARKOV CHAIN TRANSITION MATRIX
# ──────────────────────────────────────────────────────────────────────────────
# For each person, derive their ordered sequence of (window, ap_id).
# Every consecutive pair  (ap_i → ap_j)  is a transition.

ALL_APS = list(aps["ap_id"])
AP_IDX  = {ap: i for i, ap in enumerate(ALL_APS)}
N       = len(ALL_APS)

# Build the sequence per person: last-seen AP in each window
person_seq = (
    humans.sort_values("timestamp")
    .groupby(["mac", "window"])["ap_id"]
    .last()
    .reset_index()
    .sort_values(["mac", "window"])
)

# Count raw transitions
trans_counts = np.zeros((N, N), dtype=float)

for mac, seq in person_seq.groupby("mac"):
    prev_ap = None
    prev_win = None
    for _, row in seq.iterrows():
        cur_ap  = row["ap_id"]
        cur_win = row["window"]
        if prev_ap is not None and cur_ap != prev_ap:
            # Only count if the time gap is ≤ 4 windows (≤ 20 min) to avoid stale sessions
            delta_windows = (cur_win - prev_win) / pd.Timedelta(minutes=BIN_MINUTES)
            if delta_windows <= 4:
                i = AP_IDX.get(prev_ap)
                j = AP_IDX.get(cur_ap)
                if i is not None and j is not None:
                    trans_counts[i, j] += 1
        prev_ap  = cur_ap
        prev_win = cur_win

# Add self-loops: people who stay in same AP (observed in data)
stay_counts = np.zeros(N, dtype=float)
for mac, seq in person_seq.groupby("mac"):
    aps_visited = seq["ap_id"].tolist()
    for k in range(len(aps_visited) - 1):
        if aps_visited[k] == aps_visited[k + 1]:
            idx = AP_IDX.get(aps_visited[k])
            if idx is not None:
                stay_counts[idx] += 1

for i in range(N):
    trans_counts[i, i] += stay_counts[i]

# Normalise rows → stochastic matrix (add tiny epsilon to avoid zero rows)
row_sums = trans_counts.sum(axis=1, keepdims=True)
row_sums = np.where(row_sums == 0, 1, row_sums)
trans_matrix = trans_counts / row_sums

print(f"\n[4] Markov transition matrix built  ({N}×{N})")
total_transitions = int(trans_counts.sum() - np.trace(trans_counts))
print(f"    └─ Total observed transitions (excl. self-loops): {total_transitions:,}")


# ──────────────────────────────────────────────────────────────────────────────
# STEP 5 – FORWARD SIMULATION FROM A SNAPSHOT
# ──────────────────────────────────────────────────────────────────────────────
# Choose a busy snapshot (e.g. 08:10 – just before the first wave hits security)
# and simulate 60 minutes ahead in 5-min steps.

SNAPSHOT_TIME = pd.Timestamp("2025-06-12 08:10:00")
STEPS_AHEAD   = 12                          # 12 × 5 min = 60 min

def get_distribution(window: pd.Timestamp) -> np.ndarray:
    """Return person counts per AP at the given 5-min window as a vector."""
    vec = np.zeros(N, dtype=float)
    if window in occ_pivot.index:
        row = occ_pivot.loc[window]
        for ap, val in row.items():
            idx = AP_IDX.get(ap)
            if idx is not None:
                vec[idx] = val
    return vec

current_dist = get_distribution(SNAPSHOT_TIME)

# Simulate: at each step the distribution vector is multiplied by the transition matrix.
# We keep the total mass constant (closed system approximation for short horizons).
simulation = [current_dist.copy()]
state = current_dist.copy()
for step in range(STEPS_AHEAD):
    # Each person independently transitions with probability from trans_matrix
    new_state = state @ trans_matrix
    simulation.append(new_state.copy())
    state = new_state

sim_array = np.array(simulation)        # shape: (STEPS_AHEAD+1, N)

print(f"\n[5] Forward simulation: {STEPS_AHEAD} steps × {BIN_MINUTES} min from {SNAPSHOT_TIME.strftime('%H:%M')}")


# ──────────────────────────────────────────────────────────────────────────────
# STEP 6 – CONGESTION WARNINGS
# ──────────────────────────────────────────────────────────────────────────────
print(f"\n[6] Congestion warnings (threshold breach)")
print(f"    {'Window':<22} {'AP':<18} {'Count':>6} {'Threshold':>9} {'Ratio':>7}")
print(f"    {'-'*65}")

warnings_list = []
for window, row in occ_pivot.iterrows():
    for ap_id, count in row.items():
        thr = ap_threshold.get(ap_id, 999)
        if count >= thr * 0.85:          # warn at 85 % of threshold
            ratio = count / thr
            warnings_list.append({"window": window, "ap_id": ap_id,
                                   "count": count, "threshold": thr, "ratio": ratio})
            flag = "🔴 CRITICAL" if ratio >= 1.0 else "🟠 WARNING"
            print(f"    {str(window):<22} {ap_id:<18} {count:>6} {thr:>9}  {ratio:>6.1%}  {flag}")

if not warnings_list:
    print("    No congestion detected.")


# ──────────────────────────────────────────────────────────────────────────────
# STEP 7 – VISUALISATIONS
# ──────────────────────────────────────────────────────────────────────────────
import os
os.makedirs("output", exist_ok=True)


# ── Fig 1: Occupancy heatmap ──────────────────────────────────────────────────
print("\n[7] Generating figures …")

fig, ax = plt.subplots(figsize=(16, 6))
fig.suptitle("Passenger Occupancy per Access Point (5-min windows)",
             fontsize=14, fontweight="bold", color="#e0e2ea")

# Only show operating hours
mask = (occ_pivot.index >= "2025-06-12 05:30") & (occ_pivot.index <= "2025-06-12 16:00")
plot_data = occ_pivot.loc[mask]

cmap = LinearSegmentedColormap.from_list("heat",
    ["#1a1d27", "#1a3a6e", "#4f9cf9", "#f97b4f", "#ff2d2d"])

im = ax.imshow(plot_data.T, aspect="auto", cmap=cmap, interpolation="nearest")

# Axes labels
x_step = max(1, len(plot_data) // 20)
ax.set_xticks(range(0, len(plot_data), x_step))
ax.set_xticklabels(
    [ts.strftime("%H:%M") for ts in plot_data.index[::x_step]],
    rotation=45, ha="right", fontsize=8
)
ap_labels = [ap_name.get(c, c) for c in plot_data.columns]
ax.set_yticks(range(len(plot_data.columns)))
ax.set_yticklabels(ap_labels, fontsize=8)

cbar = fig.colorbar(im, ax=ax, pad=0.01)
cbar.set_label("Simultaneous persons", fontsize=9, color="#c8cad4")
cbar.ax.yaxis.set_tick_params(color="#c8cad4")

ax.axvline(
    x=list(plot_data.index).index(
        plot_data.index[plot_data.index >= SNAPSHOT_TIME][0]
    ),
    color=WARNING, linewidth=1.5, linestyle="--", label=f"Simulation start ({SNAPSHOT_TIME.strftime('%H:%M')})"
)
ax.legend(fontsize=8, loc="upper right")
plt.tight_layout()
plt.savefig("output/fig1_heatmap.png", bbox_inches="tight")
plt.close()
print("    ├─ fig1_heatmap.png")


# ── Fig 2: Top-5 AP occupancy over time ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 5))
fig.suptitle("Passenger Count Over Time – Top APs", fontsize=13, fontweight="bold")

top_aps = occ_pivot.sum().nlargest(6).index.tolist()
colors  = [ACCENT, SUCCESS, WARNING, PURPLE, "#f9d74f", "#4ff9e8"]

for ap, color in zip(top_aps, colors):
    if ap in plot_data.columns:
        ax.plot(plot_data.index, plot_data[ap],
                label=ap_name.get(ap, ap), color=color, linewidth=1.6, alpha=0.85)
        thr = ap_threshold.get(ap, None)
        if thr:
            ax.axhline(y=thr, color=color, linestyle=":", linewidth=0.8, alpha=0.5)

ax.axvline(x=SNAPSHOT_TIME, color=WARNING, linewidth=1.5,
           linestyle="--", label=f"Snapshot ({SNAPSHOT_TIME.strftime('%H:%M')})")
ax.set_xlabel("Time")
ax.set_ylabel("Simultaneous persons")
ax.legend(fontsize=7, ncol=2)
ax.grid(True)
plt.tight_layout()
plt.savefig("output/fig2_timeseries.png", bbox_inches="tight")
plt.close()
print("    ├─ fig2_timeseries.png")


# ── Fig 3: Markov transition matrix heatmap ───────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 9))
fig.suptitle("Markov Transition Matrix\n(P[from AP → to AP] per 5-min window)",
             fontsize=12, fontweight="bold")

im = ax.imshow(trans_matrix, cmap="Blues", vmin=0, vmax=trans_matrix.max())
short_names = [ap_name.get(a, a).replace(" ", "\n") for a in ALL_APS]
ax.set_xticks(range(N)); ax.set_xticklabels(short_names, fontsize=6, rotation=45, ha="right")
ax.set_yticks(range(N)); ax.set_yticklabels(short_names, fontsize=6)
ax.set_xlabel("Destination AP", labelpad=8)
ax.set_ylabel("Origin AP", labelpad=8)

for i in range(N):
    for j in range(N):
        val = trans_matrix[i, j]
        if val > 0.04:
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=5.5, color="white" if val > 0.5 else "#333")

fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02).set_label("Transition probability", fontsize=9)
plt.tight_layout()
plt.savefig("output/fig3_markov_matrix.png", bbox_inches="tight")
plt.close()
print("    ├─ fig3_markov_matrix.png")


# ── Fig 4: 60-min forward prediction ─────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
fig.suptitle(
    f"60-min Prediction from {SNAPSHOT_TIME.strftime('%H:%M')}\n"
    "(Markov chain forward simulation, 5-min steps)",
    fontsize=13, fontweight="bold"
)

future_times = [SNAPSHOT_TIME + pd.Timedelta(minutes=BIN_MINUTES * s)
                for s in range(STEPS_AHEAD + 1)]

# Panel A – Gates
gate_aps = [a for a in ALL_APS if "GATE" in a]
ax = axes[0]
ax.set_title("Gates", fontsize=10, color=ACCENT)
for ap, color in zip(gate_aps, [ACCENT, SUCCESS, WARNING, PURPLE, "#f9d74f", "#4ff9e8"]):
    idx = AP_IDX[ap]
    predicted = sim_array[:, idx]
    actual_windows = [get_distribution(w)[idx] for w in future_times]
    ax.plot(future_times, predicted,      color=color, linewidth=2,   label=ap_name[ap]+" (pred)")
    ax.plot(future_times, actual_windows, color=color, linewidth=1,
            linestyle="--", alpha=0.6,                                label=ap_name[ap]+" (actual)")
    thr = ap_threshold.get(ap)
    if thr: ax.axhline(thr, color=color, linestyle=":", alpha=0.35)
ax.set_ylabel("Persons"); ax.legend(fontsize=7, ncol=2); ax.grid(True)

# Panel B – Check-in & Security
ci_sec_aps = [a for a in ALL_APS if "CHECKIN" in a or "SECURITY" in a]
ax = axes[1]
ax.set_title("Check-in & Security", fontsize=10, color=WARNING)
for ap, color in zip(ci_sec_aps, [ACCENT, SUCCESS, WARNING, PURPLE]):
    idx = AP_IDX[ap]
    ax.plot(future_times, sim_array[:, idx],
            color=color, linewidth=2, label=ap_name[ap]+" (pred)")
    ax.plot(future_times, [get_distribution(w)[idx] for w in future_times],
            color=color, linewidth=1, linestyle="--", alpha=0.6,
            label=ap_name[ap]+" (actual)")
    thr = ap_threshold.get(ap)
    if thr: ax.axhline(thr, color=color, linestyle=":", alpha=0.35)
ax.set_ylabel("Persons"); ax.legend(fontsize=7, ncol=2); ax.grid(True)

# Panel C – Food & Arrivals
misc_aps = [a for a in ALL_APS if "FOOD" in a or "ARRIVALS" in a or "BAGGAGE" in a]
ax = axes[2]
ax.set_title("Food Court & Arrivals", fontsize=10, color=SUCCESS)
for ap, color in zip(misc_aps, [ACCENT, SUCCESS, WARNING, PURPLE, "#f9d74f"]):
    idx = AP_IDX[ap]
    ax.plot(future_times, sim_array[:, idx],
            color=color, linewidth=2, label=ap_name[ap]+" (pred)")
    ax.plot(future_times, [get_distribution(w)[idx] for w in future_times],
            color=color, linewidth=1, linestyle="--", alpha=0.6,
            label=ap_name[ap]+" (actual)")
    thr = ap_threshold.get(ap)
    if thr: ax.axhline(thr, color=color, linestyle=":", alpha=0.35)
ax.set_ylabel("Persons"); ax.set_xlabel("Time"); ax.legend(fontsize=7, ncol=2); ax.grid(True)

for ax in axes:
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%H:%M"))

plt.tight_layout()
plt.savefig("output/fig4_prediction.png", bbox_inches="tight")
plt.close()
print("    ├─ fig4_prediction.png")


# ── Fig 5: Airport map with live occupancy ────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 8))
fig.suptitle(f"Airport Map – Occupancy at {SNAPSHOT_TIME.strftime('%H:%M')}",
             fontsize=13, fontweight="bold")
ax.set_xlim(0, 100); ax.set_ylim(0, 100)
ax.set_facecolor("#0a0d14")
ax.set_aspect("equal")
ax.axis("off")

# Draw terminal outline
terminal_rect = plt.Polygon(
    [[5, 10], [95, 10], [95, 92], [5, 92]], fill=True,
    facecolor="#141820", edgecolor="#3a3d4d", linewidth=1.5, zorder=0
)
ax.add_patch(terminal_rect)

snap_vec = get_distribution(SNAPSHOT_TIME)

zone_colors = {
    "Check-in":   "#4f9cf9",
    "Security":   "#f97b4f",
    "Food Court": "#4fca8c",
    "Lounge":     "#a374f9",
    "Gates A":    "#f9d74f",
    "Gates B":    "#f9a24f",
    "Arrivals":   "#4ff9e8",
}

for _, ap_row in aps.iterrows():
    ap_id  = ap_row["ap_id"]
    x, y   = ap_row["x"], ap_row["y"]
    zone   = ap_row["zone"]
    thr    = ap_row["threshold"]
    idx    = AP_IDX.get(ap_id)
    count  = int(snap_vec[idx]) if idx is not None else 0
    ratio  = count / thr
    base_c = zone_colors.get(zone, "#888")

    radius = 3 + ratio * 4                   # bubble size scales with occupancy
    color  = "#ff2d2d" if ratio >= 1.0 else ("#f97b4f" if ratio >= 0.85 else base_c)
    alpha  = 0.35 + min(ratio, 1.0) * 0.55

    circle = plt.Circle((x, y), radius, color=color, alpha=alpha, zorder=2)
    ax.add_patch(circle)
    ax.text(x, y, str(count), ha="center", va="center",
            fontsize=7, fontweight="bold", color="white", zorder=3)
    short = ap_row["name"].replace("Check-in Hall", "CI").replace("Security Lane", "Sec")
    ax.text(x, y - radius - 1.5, short, ha="center", va="top",
            fontsize=5.5, color="#aaa", zorder=3)

# Legend
patches = [mpatches.Patch(color=c, label=z) for z, c in zone_colors.items()]
ax.legend(handles=patches, loc="lower left", fontsize=7,
          framealpha=0.5, facecolor="#1a1d27")
ax.text(95, 95, "● size = occupancy ratio", ha="right", va="top",
        fontsize=7, color="#888", style="italic")

plt.tight_layout()
plt.savefig("output/fig5_airport_map.png", bbox_inches="tight")
plt.close()
print("    └─ fig5_airport_map.png")


# ──────────────────────────────────────────────────────────────────────────────
# SUMMARY REPORT
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 62)
print("  SUMMARY REPORT")
print("=" * 62)

total_pax = humans["mac"].nunique()
busiest_ap_id  = occ_pivot.max().idxmax()
busiest_count  = int(occ_pivot.max().max())
busiest_window = occ_pivot[busiest_ap_id].idxmax()

print(f"  Total unique passengers tracked  : {total_pax:,}")
print(f"  Time range                       : {logs['timestamp'].min()} → {logs['timestamp'].max()}")
print(f"  5-min windows analysed           : {len(occ_pivot)}")
print(f"  Congestion events (≥85% thr)     : {len(warnings_list)}")
print(f"  Busiest AP                       : {ap_name.get(busiest_ap_id)} ({busiest_count} persons at {busiest_window.strftime('%H:%M')})")

# Markov steady-state
vals, vecs = np.linalg.eig(trans_matrix.T)
ss_idx = np.argmin(np.abs(vals - 1.0))
steady = np.real(vecs[:, ss_idx])
steady = steady / steady.sum()
top3_ss = sorted(zip(steady, ALL_APS), reverse=True)[:3]
print(f"\n  Markov steady-state (top-3 attractors):")
for prob, ap in top3_ss:
    print(f"    {ap_name.get(ap):<30} {prob:.1%}")

print("\n  Output figures saved in ./output/")
print("=" * 62)
