import os
os.makedirs('/home/codex/work/repo/figures', exist_ok=True)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
import numpy as np

sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
mpl.rcParams.update({
    'figure.figsize': (8, 5),
    'figure.dpi': 300,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.linewidth': 0.8,
    'axes.labelsize': 13,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'legend.framealpha': 0.9,
    'legend.edgecolor': '0.8',
    'font.family': 'serif',
    'grid.alpha': 0.3,
    'grid.linewidth': 0.5,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
})

FIGDIR = '/home/codex/work/repo/figures'

# ============================================================
# Figure 1: validation_iou_bar
# ============================================================
targets = ['Eros', 'Itokawa', 'Kleopatra', 'Gaspra', 'Betulia']
iou_values = [0.177, 0.425, 0.308, 0.352, 0.707]

palette_muted = sns.color_palette("muted")
blue = palette_muted[0]
green = palette_muted[2]
bar_colors = [green if v >= 0.70 else blue for v in iou_values]

fig1, ax1 = plt.subplots(figsize=(8, 5))
bars = ax1.bar(
    targets, iou_values,
    color=bar_colors,
    edgecolor='0.3',
    linewidth=0.8,
    width=0.6,
    zorder=3,
)

# Value annotations on top of each bar
for bar, val in zip(bars, iou_values):
    ax1.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.015,
        f'{val:.3f}',
        ha='center', va='bottom',
        fontsize=11, fontweight='semibold',
    )

# Acceptance threshold line
ax1.axhline(
    y=0.70, color='0.35', linestyle='--', linewidth=1.2, zorder=2,
)
ax1.text(
    len(targets) - 0.5, 0.715,
    'Acceptance threshold',
    ha='right', va='bottom',
    fontsize=10, fontstyle='italic', color='0.35',
)

ax1.set_ylabel('Volumetric IoU')
ax1.set_xlabel('Validation Target')
ax1.set_title('Shape Recovery Accuracy: Volumetric IoU by Target')
ax1.set_ylim(0, 0.85)
ax1.yaxis.set_major_locator(mpl.ticker.MultipleLocator(0.10))

fig1.savefig(os.path.join(FIGDIR, 'validation_iou_bar.png'), dpi=300)
fig1.savefig(os.path.join(FIGDIR, 'validation_iou_bar.pdf'))
plt.close(fig1)
print("Figure 1 saved: validation_iou_bar.png / .pdf")


# ============================================================
# Figure 2: sparse_threshold
# ============================================================
n_points = [25, 50, 100, 200]
pole_error = {
    'Eros':      [20.54, 102.25, 93.43, 93.43],
    'Kleopatra': [24.54, 155.46, 24.54, 24.54],
    'Gaspra':    [96.03, 124.63, 55.37, 55.37],
}

markers = ['o', 's', 'D']
linestyles = ['-', '--', '-.']
line_palette = sns.color_palette("muted", n_colors=3)

fig2, ax2 = plt.subplots(figsize=(8, 5))

for idx, (name, errors) in enumerate(pole_error.items()):
    ax2.plot(
        n_points, errors,
        marker=markers[idx],
        linestyle=linestyles[idx],
        color=line_palette[idx],
        linewidth=1.8,
        markersize=7,
        label=name,
        zorder=3,
    )

# Viable threshold line
ax2.axhline(
    y=30, color='0.35', linestyle='--', linewidth=1.2, zorder=2,
)
ax2.text(
    200, 33,
    'Viable threshold (30°)',
    ha='right', va='bottom',
    fontsize=10, fontstyle='italic', color='0.35',
)

ax2.set_xlabel('Number of Sparse Data Points')
ax2.set_ylabel('Pole Error (degrees)')
ax2.set_title('Sparse-Only Inversion: Pole Error vs Data Density')
ax2.set_xticks(n_points)
ax2.set_xticklabels([str(n) for n in n_points])
ax2.set_ylim(0, 175)
ax2.legend(loc='best', title='Target')

fig2.savefig(os.path.join(FIGDIR, 'sparse_threshold.png'), dpi=300)
fig2.savefig(os.path.join(FIGDIR, 'sparse_threshold.pdf'))
plt.close(fig2)
print("Figure 2 saved: sparse_threshold.png / .pdf")


# ============================================================
# Figure 3: convergence_chi2
# ============================================================
chi2_initial = [462986, 0.289, 877508418, 21429, 1539]
chi2_final   = [462986, 0.289, 877508418, 21429, 1539]  # GA didn't improve

x_idx = np.arange(len(targets))
bar_width = 0.35

conv_palette = sns.color_palette("muted", n_colors=2)

fig3, ax3 = plt.subplots(figsize=(8, 5))

bars_init = ax3.bar(
    x_idx - bar_width / 2, chi2_initial,
    width=bar_width,
    color=conv_palette[0],
    edgecolor='0.3',
    linewidth=0.8,
    label='Initial (Convex)',
    zorder=3,
)
bars_final = ax3.bar(
    x_idx + bar_width / 2, chi2_final,
    width=bar_width,
    color=conv_palette[1],
    edgecolor='0.3',
    linewidth=0.8,
    label='Final (GA)',
    zorder=3,
)

ax3.set_yscale('log')
ax3.set_xticks(x_idx)
ax3.set_xticklabels(targets)
ax3.set_ylabel(r'$\chi^2$ (log scale)')
ax3.set_xlabel('Validation Target')
ax3.set_title(r'Convergence: $\chi^2$ Residuals by Target')
ax3.legend(loc='upper right')

# Adjust y-limits so labels fit
ymin = min(chi2_initial) * 0.3
ymax = max(chi2_initial) * 8
ax3.set_ylim(ymin, ymax)

fig3.savefig(os.path.join(FIGDIR, 'convergence_chi2.png'), dpi=300)
fig3.savefig(os.path.join(FIGDIR, 'convergence_chi2.pdf'))
plt.close(fig3)
print("Figure 3 saved: convergence_chi2.png / .pdf")

print("\nAll figures generated successfully in:", FIGDIR)
