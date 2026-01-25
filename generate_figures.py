"""
Generate publication-quality figures for 3x3 Matrix Multiplication Research Paper
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, FancyBboxPatch
import matplotlib.patches as mpatches

# Set publication style
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 14

def remove_spines(ax):
    """Remove top and right spines for cleaner appearance"""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# Figure 1: Algorithm Comparison - Operation Counts
def fig1_algorithm_comparison():
    algorithms = ['Standard', 'Block-\nDecomp', 'Block-\nStrassen', 'Laderman\n(known)']
    multiplications = [27, 27, 26, 23]
    additions = [18, 18, 32, 100]
    total = [45, 45, 58, 123]

    x = np.arange(len(algorithms))
    width = 0.25

    fig, ax = plt.subplots(figsize=(8, 5))

    bars1 = ax.bar(x - width, multiplications, width, label='Multiplications',
                   color='#2E86AB', alpha=0.8, edgecolor='black', linewidth=0.8)
    bars2 = ax.bar(x, additions, width, label='Additions',
                   color='#A23B72', alpha=0.8, edgecolor='black', linewidth=0.8)
    bars3 = ax.bar(x + width, total, width, label='Total Operations',
                   color='#F18F01', alpha=0.8, edgecolor='black', linewidth=0.8)

    # Add constraint line
    ax.axhline(y=81, color='red', linestyle='--', linewidth=2, label='Constraint (<81 ops)', alpha=0.7)

    ax.set_xlabel('Algorithm', fontweight='bold')
    ax.set_ylabel('Number of Operations', fontweight='bold')
    ax.set_title('Operation Count Comparison: 3×3 Matrix Multiplication Algorithms',
                 fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(algorithms)
    ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    remove_spines(ax)

    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig('figures/fig1_algorithm_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Figure 1 saved: fig1_algorithm_comparison.png")

# Figure 2: Ablation Study - Component Effects
def fig2_ablation_study():
    components = ['Baseline\n(Standard)', 'Block\nDecomp', 'Strassen\n2×2', 'Combined\n(Both)']
    mults = [27, 27, 22, 26]
    adds = [18, 18, 28, 32]
    correct = ['✓', '✓', '✗', '✓']
    colors = ['#2E86AB', '#2E86AB', '#C73E1D', '#A23B72']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left plot: Operation counts
    x = np.arange(len(components))
    width = 0.35

    bars1 = ax1.bar(x - width/2, mults, width, label='Multiplications',
                    color='#2E86AB', alpha=0.8, edgecolor='black', linewidth=0.8)
    bars2 = ax1.bar(x + width/2, adds, width, label='Additions',
                    color='#F18F01', alpha=0.8, edgecolor='black', linewidth=0.8)

    ax1.set_xlabel('Component Configuration', fontweight='bold')
    ax1.set_ylabel('Number of Operations', fontweight='bold')
    ax1.set_title('(a) Component Ablation: Operation Counts', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(components)
    ax1.legend(frameon=True, fancybox=True, shadow=True)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    remove_spines(ax1)

    # Add correctness markers
    for i, (bar, corr) in enumerate(zip(x, correct)):
        color = 'green' if corr == '✓' else 'red'
        symbol = corr
        ax1.text(bar, max(mults[i], adds[i]) + 2, symbol,
                ha='center', va='bottom', fontsize=18, color=color, fontweight='bold')

    # Right plot: Total operations with target line
    totals = [m + a for m, a in zip(mults, adds)]
    bars = ax2.bar(x, totals, color=colors, alpha=0.8, edgecolor='black', linewidth=0.8)
    ax2.axhline(y=45, color='green', linestyle='--', linewidth=2,
                label='Standard (optimal)', alpha=0.7)

    ax2.set_xlabel('Component Configuration', fontweight='bold')
    ax2.set_ylabel('Total Operations', fontweight='bold')
    ax2.set_title('(b) Total Operation Count by Configuration', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(components)
    ax2.legend(frameon=True, fancybox=True, shadow=True)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    remove_spines(ax2)

    # Add value labels
    for bar, total, corr in zip(bars, totals, correct):
        height = bar.get_height()
        marker = '✓' if corr == '✓' else '✗'
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}\n{marker}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig('figures/fig2_ablation_study.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Figure 2 saved: fig2_ablation_study.png")

# Figure 3: Theoretical Bounds and Known Results
def fig3_theoretical_bounds():
    fig, ax = plt.subplots(figsize=(10, 6))

    # Multiplication count range
    min_mult = 19  # Proven lower bound
    max_mult = 27  # Standard algorithm
    laderman = 23  # Best known
    target = 22    # Goal (impossible)

    # Create horizontal bar chart showing the landscape
    categories = [
        'Standard Algorithm',
        'Block-Strassen',
        'Target Goal',
        'Laderman (1976)\n[Best Known]',
        'Proven Lower Bound'
    ]
    values = [27, 26, 22, 23, 19]
    colors_map = ['#A8DADC', '#457B9D', '#E63946', '#F77F00', '#06D6A0']

    y_pos = np.arange(len(categories))
    bars = ax.barh(y_pos, values, color=colors_map, alpha=0.8,
                   edgecolor='black', linewidth=1.2)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories)
    ax.set_xlabel('Number of Multiplications', fontweight='bold')
    ax.set_title('Theoretical Landscape: 3×3 Matrix Multiplication Complexity',
                 fontweight='bold', pad=15)
    ax.set_xlim(18, 28)

    # Add vertical lines for key values
    ax.axvline(x=23, color='orange', linestyle='--', linewidth=2, alpha=0.5)
    ax.axvline(x=19, color='green', linestyle='--', linewidth=2, alpha=0.5)

    # Add shaded region for open problem
    ax.axvspan(19, 23, alpha=0.15, color='yellow', label='Open Problem Region')

    remove_spines(ax)
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    # Add value labels
    for bar, val in zip(bars, values):
        width = bar.get_width()
        label = f'{int(val)}'
        ax.text(width + 0.3, bar.get_y() + bar.get_height()/2.,
               label, ha='left', va='center', fontsize=11, fontweight='bold')

    # Add annotation for open problem
    ax.text(21, 3.5, 'Open Problem:\n19 ≤ r₃ₓ₃ ≤ 23',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.3),
            ha='center', va='center', fontsize=10, style='italic')

    plt.tight_layout()
    plt.savefig('figures/fig3_theoretical_bounds.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Figure 3 saved: fig3_theoretical_bounds.png")

# Figure 4: Trade-off Analysis
def fig4_tradeoff_analysis():
    fig, ax = plt.subplots(figsize=(9, 6))

    # Algorithms with their characteristics
    algorithms = [
        ('Standard', 27, 18, 45),
        ('Block-Decomp', 27, 18, 45),
        ('Block-Strassen', 26, 32, 58),
        ('Laderman', 23, 100, 123)
    ]

    names = [a[0] for a in algorithms]
    mults = [a[1] for a in algorithms]
    adds = [a[2] for a in algorithms]

    # Scatter plot
    colors = ['#2E86AB', '#457B9D', '#F18F01', '#C73E1D']
    sizes = [200, 200, 250, 250]

    for i, (name, m, a, total) in enumerate(algorithms):
        ax.scatter(m, a, s=sizes[i], c=colors[i], alpha=0.7,
                  edgecolors='black', linewidth=1.5, label=name)

        # Add labels
        offset_x = 0 if name != 'Laderman' else -0.5
        offset_y = -3 if name not in ['Block-Strassen', 'Laderman'] else 3
        ax.annotate(f'{name}\n({total} ops)',
                   xy=(m, a), xytext=(m + offset_x, a + offset_y),
                   ha='center', fontsize=9, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                            edgecolor=colors[i], linewidth=1.5, alpha=0.8))

    # Add constraint lines
    mult_vals = np.linspace(20, 28, 100)
    constraint_81 = 81 - mult_vals
    ax.plot(mult_vals, constraint_81, 'r--', linewidth=2,
            label='Total = 81 (Constraint)', alpha=0.7)

    ax.fill_between(mult_vals, 0, constraint_81, alpha=0.1, color='green',
                     label='Feasible Region (<81)')

    ax.set_xlabel('Number of Multiplications', fontweight='bold')
    ax.set_ylabel('Number of Additions', fontweight='bold')
    ax.set_title('Trade-off Space: Multiplications vs. Additions',
                 fontweight='bold', pad=15)
    ax.set_xlim(21, 28)
    ax.set_ylim(-5, 110)
    ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
    ax.grid(alpha=0.3, linestyle='--')
    remove_spines(ax)

    plt.tight_layout()
    plt.savefig('figures/fig4_tradeoff_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Figure 4 saved: fig4_tradeoff_analysis.png")

# Figure 5: Block Decomposition Visualization
def fig5_block_decomposition():
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Title
    ax.text(7, 9.5, 'Block Decomposition Strategy for 3×3 Matrices',
            ha='center', fontsize=14, fontweight='bold')

    # Draw Matrix A
    def draw_matrix(x_offset, y_offset, label):
        # 2x2 block
        rect1 = FancyBboxPatch((x_offset, y_offset+1), 2, 2,
                               boxstyle="round,pad=0.05",
                               edgecolor='#2E86AB', facecolor='#A8DADC',
                               linewidth=2, alpha=0.7)
        ax.add_patch(rect1)
        ax.text(x_offset+1, y_offset+2, 'A₁₁\n(2×2)', ha='center', va='center',
                fontsize=10, fontweight='bold')

        # u vector (right column)
        rect2 = FancyBboxPatch((x_offset+2, y_offset+1), 1, 2,
                               boxstyle="round,pad=0.05",
                               edgecolor='#457B9D', facecolor='#CDE5F7',
                               linewidth=2, alpha=0.7)
        ax.add_patch(rect2)
        ax.text(x_offset+2.5, y_offset+2, 'u\n(2×1)', ha='center', va='center',
                fontsize=9, fontweight='bold')

        # v vector (bottom row)
        rect3 = FancyBboxPatch((x_offset, y_offset), 2, 1,
                               boxstyle="round,pad=0.05",
                               edgecolor='#457B9D', facecolor='#CDE5F7',
                               linewidth=2, alpha=0.7)
        ax.add_patch(rect3)
        ax.text(x_offset+1, y_offset+0.5, 'v (1×2)', ha='center', va='center',
                fontsize=9, fontweight='bold')

        # scalar (bottom-right)
        rect4 = FancyBboxPatch((x_offset+2, y_offset), 1, 1,
                               boxstyle="round,pad=0.05",
                               edgecolor='#F18F01', facecolor='#FFE5B4',
                               linewidth=2, alpha=0.7)
        ax.add_patch(rect4)
        ax.text(x_offset+2.5, y_offset+0.5, label, ha='center', va='center',
                fontsize=9, fontweight='bold')

        # Matrix label
        ax.text(x_offset+1.5, y_offset+3.5, f'Matrix {label[0]}',
                ha='center', fontsize=11, fontweight='bold')

    # Draw A and B matrices
    draw_matrix(0.5, 4, 'a₃₃')
    draw_matrix(4.5, 4, 'b₃₃')

    # Multiplication symbol
    ax.text(4, 5.5, '×', ha='center', va='center', fontsize=20, fontweight='bold')

    # Arrow
    ax.annotate('', xy=(9, 5.5), xytext=(6, 5.5),
                arrowprops=dict(arrowstyle='->', lw=2, color='black'))

    # Result matrix C
    ax.text(11, 8, 'C = A × B', ha='center', fontsize=11, fontweight='bold')

    # C components
    components = [
        ('C₁₁ = A₁₁B₁₁ + uy', 7.0, '#A8DADC'),
        ('C₁₂ = A₁₁x + ub₃₃', 6.2, '#CDE5F7'),
        ('C₂₁ = vB₁₁ + a₃₃y', 5.4, '#CDE5F7'),
        ('C₂₂ = vx + a₃₃b₃₃', 4.6, '#FFE5B4')
    ]

    for comp, y, color in components:
        rect = FancyBboxPatch((8.5, y-0.3), 5, 0.6,
                             boxstyle="round,pad=0.05",
                             edgecolor='black', facecolor=color,
                             linewidth=1.5, alpha=0.6)
        ax.add_patch(rect)
        ax.text(11, y, comp, ha='center', va='center', fontsize=9, fontweight='bold')

    # Operation counts
    ops_text = (
        "Operation Counts:\n"
        "• Standard: A₁₁B₁₁ uses 8 mults\n"
        "• Strassen: A₁₁B₁₁ uses 7 mults\n"
        "• Savings: 1 multiplication"
    )
    ax.text(1, 2, ops_text, ha='left', va='top', fontsize=9,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow',
                     edgecolor='black', linewidth=1.5, alpha=0.8))

    plt.tight_layout()
    plt.savefig('figures/fig5_block_decomposition.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Figure 5 saved: fig5_block_decomposition.png")

# Main execution
if __name__ == "__main__":
    print("Generating publication-quality figures...")
    print("=" * 60)

    fig1_algorithm_comparison()
    fig2_ablation_study()
    fig3_theoretical_bounds()
    fig4_tradeoff_analysis()
    fig5_block_decomposition()

    print("=" * 60)
    print("All figures generated successfully!")
    print("\nFigures saved in ./figures/ directory:")
    print("  1. fig1_algorithm_comparison.png")
    print("  2. fig2_ablation_study.png")
    print("  3. fig3_theoretical_bounds.png")
    print("  4. fig4_tradeoff_analysis.png")
    print("  5. fig5_block_decomposition.png")
