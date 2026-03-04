import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, PillowWriter

# --- Parameters ---
AREA = 100
N_AGENTS = 5
T = 200
r_sense = 12
r_comm = 8
W_min = 10
W_max = 70
CELL_SIZE = 4

COLORS = ['#4C72B0', '#DD4444', '#2CA02C', '#FF7F0E', '#9467BD']
GRID = AREA // CELL_SIZE

# --- Initialize agents ---
np.random.seed(42)
positions = np.random.uniform(5, AREA-5, (N_AGENTS, 2))
velocities = np.random.uniform(-1.2, 1.2, (N_AGENTS, 2))

# Each agent has its own explored map
local_maps = [np.zeros((GRID, GRID), dtype=bool) for _ in range(N_AGENTS)]
global_map = np.zeros((GRID, GRID), dtype=bool)

# Adaptive W per agent pair
W_matrix = np.full((N_AGENTS, N_AGENTS), 40.0)
t_last = np.full((N_AGENTS, N_AGENTS), -40.0)
new_cells_count = np.zeros(N_AGENTS)

# --- Pre-compute simulation ---
all_positions = []
all_local_maps = []
all_W = []
all_coverage = []
exchange_events = []

pos = positions.copy()
vel = velocities.copy()
lmaps = [m.copy() for m in local_maps]

for t in range(T):
    # Move
    for i in range(N_AGENTS):
        pos[i] += vel[i]
        for d in range(2):
            if pos[i][d] < 2: pos[i][d] = 2; vel[i][d] *= -1
            if pos[i][d] > AREA-2: pos[i][d] = AREA-2; vel[i][d] *= -1

    # Sense environment
    for i in range(N_AGENTS):
        prev = lmaps[i].sum()
        cx = int(pos[i][0] / CELL_SIZE)
        cy = int(pos[i][1] / CELL_SIZE)
        r_cells = int(r_sense / CELL_SIZE)
        for dx in range(-r_cells, r_cells+1):
            for dy in range(-r_cells, r_cells+1):
                nx, ny = cx+dx, cy+dy
                if 0 <= nx < GRID and 0 <= ny < GRID:
                    if dx**2 + dy**2 <= r_cells**2:
                        lmaps[i][nx][ny] = True
        new_cells_count[i] = lmaps[i].sum() - prev

    # Agent meetings + Adaptive W + map exchange
    step_exchanges = []
    for i in range(N_AGENTS):
        for j in range(i+1, N_AGENTS):
            dist = np.linalg.norm(pos[i] - pos[j])
            AoI = t - t_last[i][j]

            # Adaptive W
            avg_new = (new_cells_count[i] + new_cells_count[j]) / 2
            if avg_new > 3:
                W_matrix[i][j] = max(W_min, W_matrix[i][j] - 2)
            else:
                W_matrix[i][j] = min(W_max, W_matrix[i][j] + 0.5)
            W_matrix[j][i] = W_matrix[i][j]

            # Meeting
            if dist <= r_comm and AoI >= W_matrix[i][j]:
                t_last[i][j] = t
                t_last[j][i] = t
                # Share maps (incremental)
                merged = lmaps[i] | lmaps[j]
                lmaps[i] = merged.copy()
                lmaps[j] = merged.copy()
                step_exchanges.append((i, j, pos[i].copy(), pos[j].copy()))

    # Global coverage
    combined = np.zeros((GRID, GRID), dtype=bool)
    for m in lmaps:
        combined |= m
    coverage = combined.sum() / (GRID * GRID) * 100

    all_positions.append(pos.copy())
    all_local_maps.append([m.copy() for m in lmaps])
    all_coverage.append(coverage)
    all_W.append(W_matrix.copy())
    exchange_events.append(step_exchanges)

# --- Animation ---
fig, ax = plt.subplots(figsize=(8, 8))

def update(frame):
    ax.clear()
    ax.set_xlim(0, AREA)
    ax.set_ylim(0, AREA)
    ax.set_facecolor('white')
    ax.set_aspect('equal')

    pos = all_positions[frame]
    lmaps_f = all_local_maps[frame]
    coverage = all_coverage[frame]
    exchanges = exchange_events[frame]

    # Draw each agent's explored map
    for i in range(N_AGENTS):
        color = COLORS[i]
        for gx in range(GRID):
            for gy in range(GRID):
                if lmaps_f[i][gx][gy]:
                    rect = patches.Rectangle(
                        (gx * CELL_SIZE, gy * CELL_SIZE),
                        CELL_SIZE, CELL_SIZE,
                        linewidth=0,
                        facecolor=color,
                        alpha=0.18
                    )
                    ax.add_patch(rect)

    # Draw exchange lines
    for (i, j, pi, pj) in exchanges:
        ax.plot([pi[0], pj[0]], [pi[1], pj[1]],
                color='gold', linewidth=2.5, alpha=0.9, zorder=3)
        mid = (pi + pj) / 2
        ax.text(mid[0], mid[1], 'exchange', fontsize=7,
                ha='center', color='darkorange', fontweight='bold')

    # Draw agents
    for i in range(N_AGENTS):
        # Sensing range
        sense_circle = plt.Circle(pos[i], r_sense,
                                   color=COLORS[i], fill=False,
                                   linestyle='--', linewidth=1, alpha=0.5)
        # Comm range
        comm_circle = plt.Circle(pos[i], r_comm,
                                  color=COLORS[i], fill=False,
                                  linestyle='-', linewidth=1.5, alpha=0.8)
        ax.add_patch(sense_circle)
        ax.add_patch(comm_circle)
        ax.scatter(*pos[i], color=COLORS[i], s=80, zorder=5)

    # Border
    border = patches.Rectangle((0,0), AREA, AREA,
                                 linewidth=2, edgecolor='black', facecolor='none')
    ax.add_patch(border)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0],[0], marker='o', color='w', markerfacecolor='gray',
               markersize=8, label='Explorer'),
        Line2D([0],[0], linestyle='--', color='gray', label=f'Sensing r_s={r_sense}'),
        Line2D([0],[0], linestyle='-', color='gray', label=f'Comm r_c={r_comm}'),
        patches.Patch(facecolor='lightgreen', alpha=0.5, label='exchange'),
        patches.Patch(facecolor='lightgray', alpha=0.5, label='explored (background)')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=8)

    ax.set_title(f'tick = {frame:3d}    global_coverage = {coverage:.2f}%', fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])

print("Computing animation... please wait")
anim = FuncAnimation(fig, update, frames=T, interval=100, repeat=False)

# Save as GIF
writer = PillowWriter(fps=10)
anim.save('simulation.gif', writer=writer)
print("Done! simulation.gif saved.")
# plt.show()


