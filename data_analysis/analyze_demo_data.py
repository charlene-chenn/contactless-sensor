#!/usr/bin/env python3
"""
Wind Sensor Performance Analysis Script
Analyzes contact wind sensor performance against ground truth with uncertainty bounds
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration
# Get the script's directory and set paths relative to parent directory
SCRIPT_DIR = Path(__file__).parent
PARENT_DIR = SCRIPT_DIR.parent
DEMO_DATA_PATH = PARENT_DIR / "demo_data"
GT_FILE = DEMO_DATA_PATH / "1_GT.csv"
STUDENT_FILE = DEMO_DATA_PATH / "1_ST.csv"
OUTPUT_DIR = SCRIPT_DIR / "analysis_results"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_and_align_data(gt_file, student_file):
    """
    Load ground truth and student data, then align them based on timestamps
    """
    print("Loading data files...")
    gt_df = pd.read_csv(gt_file)
    student_df = pd.read_csv(student_file)

    print(f"Ground truth data points: {len(gt_df)}")
    print(f"Student data points: {len(student_df)}")

    # Use timestamp_epoch for alignment
    gt_df = gt_df.sort_values('timestamp_epoch')
    student_df = student_df.sort_values('timestamp_epoch')

    # Merge on nearest timestamp (using merge_asof for time-series data)
    # Tolerance set to ~3x mean sampling interval (~5ms * 3 = 15ms)
    # Both sensors sample at ~203 Hz, so 15ms tolerance is appropriate
    merged_df = pd.merge_asof(
        student_df,
        gt_df,
        on='timestamp_epoch',
        direction='nearest',
        suffixes=('_student', '_gt'),
        tolerance=0.015  # 15 millisecond tolerance (appropriate for ~203 Hz sampling)
    )

    # Remove rows with missing data
    merged_df = merged_df.dropna(subset=['value_clipped_mps_gt', 'value_clipped_mps_student'])

    print(f"Aligned data points: {len(merged_df)}")

    return merged_df


def calculate_rmse(errors):
    """Calculate Root Mean Square Error"""
    return np.sqrt(np.mean(errors ** 2))


def analyze_performance(df):
    """
    Perform comprehensive performance analysis with different RMSE calculations
    """
    results = {}

    # Extract relevant columns
    gt_values = df['value_clipped_mps_gt'].values
    student_values = df['value_clipped_mps_student'].values
    gt_lower = df['cov_lower_mps_gt'].values
    gt_upper = df['cov_upper_mps_gt'].values

    print("\n" + "="*70)
    print("PERFORMANCE ANALYSIS RESULTS")
    print("="*70)

    # 1. Standard RMSE (all data)
    print("\n1. STANDARD RMSE (All Data)")
    print("-" * 70)
    errors_standard = student_values - gt_values
    rmse_standard = calculate_rmse(errors_standard)
    results['standard'] = {
        'rmse': rmse_standard,
        'errors': errors_standard,
        'gt_values': gt_values,
        'student_values': student_values,
        'n_samples': len(errors_standard)
    }
    print(f"   RMSE: {rmse_standard:.6f} m/s")
    print(f"   Mean Error: {np.mean(errors_standard):.6f} m/s")
    print(f"   Std Dev: {np.std(errors_standard):.6f} m/s")
    print(f"   Samples: {len(errors_standard)}")

    # 2. RMSE excluding negative ground truth values
    print("\n2. RMSE EXCLUDING NEGATIVE GROUND TRUTH VALUES")
    print("-" * 70)
    mask_positive = gt_values >= 0
    gt_positive = gt_values[mask_positive]
    student_positive = student_values[mask_positive]
    errors_positive = student_positive - gt_positive
    rmse_positive = calculate_rmse(errors_positive)
    results['positive_only'] = {
        'rmse': rmse_positive,
        'errors': errors_positive,
        'gt_values': gt_positive,
        'student_values': student_positive,
        'n_samples': len(errors_positive)
    }
    print(f"   RMSE: {rmse_positive:.6f} m/s")
    print(f"   Mean Error: {np.mean(errors_positive):.6f} m/s")
    print(f"   Std Dev: {np.std(errors_positive):.6f} m/s")
    print(f"   Samples: {len(errors_positive)} (excluded {np.sum(~mask_positive)} negative values)")

    # 3. RMSE using uncertainty boundaries (closest boundary)
    print("\n3. RMSE USING UNCERTAINTY BOUNDARIES (Closest Boundary)")
    print("-" * 70)
    print("   Method: If student value is outside [lower, upper] bounds,")
    print("           use distance to closest boundary; otherwise error = 0")

    errors_boundary = np.zeros_like(student_values)
    for i in range(len(student_values)):
        if student_values[i] < gt_lower[i]:
            # Below lower bound
            errors_boundary[i] = student_values[i] - gt_lower[i]
        elif student_values[i] > gt_upper[i]:
            # Above upper bound
            errors_boundary[i] = student_values[i] - gt_upper[i]
        else:
            # Within bounds
            errors_boundary[i] = 0.0

    rmse_boundary = calculate_rmse(errors_boundary)
    results['boundary'] = {
        'rmse': rmse_boundary,
        'errors': errors_boundary,
        'gt_values': gt_values,
        'student_values': student_values,
        'gt_lower': gt_lower,
        'gt_upper': gt_upper,
        'n_samples': len(errors_boundary),
        'n_within_bounds': np.sum(errors_boundary == 0)
    }
    print(f"   RMSE: {rmse_boundary:.6f} m/s")
    print(f"   Mean Error: {np.mean(errors_boundary):.6f} m/s")
    print(f"   Std Dev: {np.std(errors_boundary):.6f} m/s")
    print(f"   Samples: {len(errors_boundary)}")
    print(f"   Within bounds: {np.sum(errors_boundary == 0)} ({100*np.sum(errors_boundary == 0)/len(errors_boundary):.1f}%)")

    # 4. RMSE using uncertainty boundaries, excluding negative GT values
    print("\n4. RMSE USING BOUNDARIES, EXCLUDING NEGATIVE GT VALUES")
    print("-" * 70)
    errors_boundary_positive = errors_boundary[mask_positive]
    rmse_boundary_positive = calculate_rmse(errors_boundary_positive)
    results['boundary_positive'] = {
        'rmse': rmse_boundary_positive,
        'errors': errors_boundary_positive,
        'gt_values': gt_positive,
        'student_values': student_positive,
        'gt_lower': gt_lower[mask_positive],
        'gt_upper': gt_upper[mask_positive],
        'n_samples': len(errors_boundary_positive),
        'n_within_bounds': np.sum(errors_boundary_positive == 0)
    }
    print(f"   RMSE: {rmse_boundary_positive:.6f} m/s")
    print(f"   Mean Error: {np.mean(errors_boundary_positive):.6f} m/s")
    print(f"   Std Dev: {np.std(errors_boundary_positive):.6f} m/s")
    print(f"   Samples: {len(errors_boundary_positive)}")
    print(f"   Within bounds: {np.sum(errors_boundary_positive == 0)} ({100*np.sum(errors_boundary_positive == 0)/len(errors_boundary_positive):.1f}%)")

    print("\n" + "="*70)

    return results


def create_visualizations(results, df):
    """
    Generate comprehensive visualization graphs
    """
    print("\nGenerating visualizations...")

    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')

    # 1. Time series comparison for all scenarios
    print("  - Time series plots...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Wind Sensor Performance Analysis: Time Series', fontsize=16, fontweight='bold')

    time_axis = df['t_rel_s_student'].values

    # Standard RMSE plot
    ax = axes[0, 0]
    ax.plot(time_axis, results['standard']['gt_values'],
            label='Ground Truth', alpha=0.7, linewidth=1)
    ax.plot(time_axis, results['standard']['student_values'],
            label='Student Sensor', alpha=0.7, linewidth=1)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Wind Speed (m/s)')
    ax.set_title(f'1. All Data (RMSE: {results["standard"]["rmse"]:.4f} m/s)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Positive only RMSE plot
    ax = axes[0, 1]
    mask_positive = results['standard']['gt_values'] >= 0
    time_positive = time_axis[mask_positive]
    ax.plot(time_positive, results['positive_only']['gt_values'],
            label='Ground Truth (≥0)', alpha=0.7, linewidth=1)
    ax.plot(time_positive, results['positive_only']['student_values'],
            label='Student Sensor', alpha=0.7, linewidth=1)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Wind Speed (m/s)')
    ax.set_title(f'2. Positive GT Only (RMSE: {results["positive_only"]["rmse"]:.4f} m/s)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Boundary RMSE plot
    ax = axes[1, 0]
    ax.plot(time_axis, results['boundary']['gt_values'],
            label='Ground Truth', alpha=0.5, linewidth=1)
    ax.fill_between(time_axis,
                     results['boundary']['gt_lower'],
                     results['boundary']['gt_upper'],
                     alpha=0.2, label='Uncertainty Bounds')
    ax.plot(time_axis, results['boundary']['student_values'],
            label='Student Sensor', alpha=0.7, linewidth=1)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Wind Speed (m/s)')
    ax.set_title(f'3. With Uncertainty Bounds (RMSE: {results["boundary"]["rmse"]:.4f} m/s)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Boundary + Positive RMSE plot
    ax = axes[1, 1]
    ax.plot(time_positive, results['boundary_positive']['gt_values'],
            label='Ground Truth (≥0)', alpha=0.5, linewidth=1)
    ax.fill_between(time_positive,
                     results['boundary_positive']['gt_lower'],
                     results['boundary_positive']['gt_upper'],
                     alpha=0.2, label='Uncertainty Bounds')
    ax.plot(time_positive, results['boundary_positive']['student_values'],
            label='Student Sensor', alpha=0.7, linewidth=1)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Wind Speed (m/s)')
    ax.set_title(f'4. Bounds + Positive GT (RMSE: {results["boundary_positive"]["rmse"]:.4f} m/s)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'time_series_comparison.png', dpi=300, bbox_inches='tight')
    print(f"    Saved: {OUTPUT_DIR / 'time_series_comparison.png'}")

    # 2. Error distribution plots
    print("  - Error distribution plots...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Wind Sensor Performance Analysis: Error Distributions', fontsize=16, fontweight='bold')

    scenarios = [
        ('standard', '1. All Data'),
        ('positive_only', '2. Positive GT Only'),
        ('boundary', '3. With Uncertainty Bounds'),
        ('boundary_positive', '4. Bounds + Positive GT')
    ]

    for idx, (key, title) in enumerate(scenarios):
        ax = axes[idx // 2, idx % 2]
        errors = results[key]['errors']
        rmse = results[key]['rmse']

        ax.hist(errors, bins=50, alpha=0.7, edgecolor='black')
        ax.axvline(0, color='red', linestyle='--', linewidth=2, label='Zero Error')
        ax.axvline(np.mean(errors), color='green', linestyle='--', linewidth=2,
                   label=f'Mean: {np.mean(errors):.4f}')
        ax.set_xlabel('Error (m/s)')
        ax.set_ylabel('Frequency')
        ax.set_title(f'{title}\nRMSE: {rmse:.4f} m/s, Std: {np.std(errors):.4f} m/s')
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'error_distributions.png', dpi=300, bbox_inches='tight')
    print(f"    Saved: {OUTPUT_DIR / 'error_distributions.png'}")

    # 3. Scatter plots
    print("  - Scatter plots...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Wind Sensor Performance Analysis: Scatter Plots', fontsize=16, fontweight='bold')

    for idx, (key, title) in enumerate(scenarios):
        ax = axes[idx // 2, idx % 2]
        gt = results[key]['gt_values']
        student = results[key]['student_values']
        rmse = results[key]['rmse']

        # Scatter plot
        ax.scatter(gt, student, alpha=0.3, s=10)

        # Perfect agreement line
        min_val = min(gt.min(), student.min())
        max_val = max(gt.max(), student.max())
        ax.plot([min_val, max_val], [min_val, max_val],
                'r--', linewidth=2, label='Perfect Agreement')

        ax.set_xlabel('Ground Truth (m/s)')
        ax.set_ylabel('Student Sensor (m/s)')
        ax.set_title(f'{title}\nRMSE: {rmse:.4f} m/s')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.axis('equal')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'scatter_plots.png', dpi=300, bbox_inches='tight')
    print(f"    Saved: {OUTPUT_DIR / 'scatter_plots.png'}")

    # 4. RMSE comparison bar chart
    print("  - RMSE comparison chart...")
    fig, ax = plt.subplots(figsize=(10, 6))

    scenario_names = ['All Data', 'Positive GT Only', 'With Bounds', 'Bounds + Positive']
    rmse_values = [results[key]['rmse'] for key, _ in scenarios]

    bars = ax.bar(scenario_names, rmse_values, alpha=0.7, edgecolor='black')
    ax.set_ylabel('RMSE (m/s)', fontsize=12)
    ax.set_title('RMSE Comparison Across Different Calculation Methods',
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for bar, value in zip(bars, rmse_values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.4f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.xticks(rotation=15, ha='right')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'rmse_comparison.png', dpi=300, bbox_inches='tight')
    print(f"    Saved: {OUTPUT_DIR / 'rmse_comparison.png'}")

    # 5. Bland-Altman plot for standard case
    print("  - Bland-Altman plot...")
    fig, ax = plt.subplots(figsize=(10, 6))

    gt = results['standard']['gt_values']
    student = results['standard']['student_values']
    mean_values = (gt + student) / 2
    differences = student - gt

    mean_diff = np.mean(differences)
    std_diff = np.std(differences)

    ax.scatter(mean_values, differences, alpha=0.3, s=10)
    ax.axhline(mean_diff, color='red', linestyle='-', linewidth=2,
               label=f'Mean Difference: {mean_diff:.4f}')
    ax.axhline(mean_diff + 1.96*std_diff, color='red', linestyle='--', linewidth=1.5,
               label=f'+1.96 SD: {mean_diff + 1.96*std_diff:.4f}')
    ax.axhline(mean_diff - 1.96*std_diff, color='red', linestyle='--', linewidth=1.5,
               label=f'-1.96 SD: {mean_diff - 1.96*std_diff:.4f}')

    ax.set_xlabel('Mean of GT and Student (m/s)', fontsize=12)
    ax.set_ylabel('Difference (Student - GT) (m/s)', fontsize=12)
    ax.set_title('Bland-Altman Plot: Agreement Analysis', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'bland_altman.png', dpi=300, bbox_inches='tight')
    print(f"    Saved: {OUTPUT_DIR / 'bland_altman.png'}")

    print("\n✓ All visualizations generated successfully!")


def save_summary_report(results):
    """
    Save a text summary report
    """
    print("\nSaving summary report...")

    with open(OUTPUT_DIR / 'analysis_summary.txt', 'w') as f:
        f.write("="*70 + "\n")
        f.write("WIND SENSOR PERFORMANCE ANALYSIS SUMMARY\n")
        f.write("="*70 + "\n\n")

        scenarios = [
            ('standard', '1. STANDARD RMSE (All Data)'),
            ('positive_only', '2. RMSE EXCLUDING NEGATIVE GROUND TRUTH VALUES'),
            ('boundary', '3. RMSE USING UNCERTAINTY BOUNDARIES'),
            ('boundary_positive', '4. RMSE USING BOUNDARIES, EXCLUDING NEGATIVE GT')
        ]

        for key, title in scenarios:
            f.write(title + "\n")
            f.write("-" * 70 + "\n")
            f.write(f"RMSE:          {results[key]['rmse']:.6f} m/s\n")
            f.write(f"Mean Error:    {np.mean(results[key]['errors']):.6f} m/s\n")
            f.write(f"Std Dev:       {np.std(results[key]['errors']):.6f} m/s\n")
            f.write(f"Samples:       {results[key]['n_samples']}\n")
            if 'n_within_bounds' in results[key]:
                pct = 100 * results[key]['n_within_bounds'] / results[key]['n_samples']
                f.write(f"Within Bounds: {results[key]['n_within_bounds']} ({pct:.1f}%)\n")
            f.write("\n")

    print(f"  Saved: {OUTPUT_DIR / 'analysis_summary.txt'}")


def main():
    """
    Main execution function
    """
    print("\n" + "="*70)
    print("WIND SENSOR PERFORMANCE ANALYSIS")
    print("="*70 + "\n")

    # Load and align data
    df = load_and_align_data(GT_FILE, STUDENT_FILE)

    # Perform analysis
    results = analyze_performance(df)

    # Create visualizations
    create_visualizations(results, df)

    # Save summary report
    save_summary_report(results)


if __name__ == "__main__":
    main()
