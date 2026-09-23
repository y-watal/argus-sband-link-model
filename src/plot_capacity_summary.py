from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "output" / "data" / "pass_hardware_results.csv"
PLOTS_DIRECTORY = PROJECT_ROOT / "output" / "plots" / "capacity_summary"

MISSION_TARGET_MB = 2.0
ELEVATION_BIN_WIDTH_DEG = 5.0


def make_output_directory():
    PLOTS_DIRECTORY.mkdir(parents=True, exist_ok=True)


def load_pass_results():
    df = pd.read_csv(DATA_PATH)

    required_columns = [
        "max_elevation_deg",
        "max_payload_possible_mb",
        "full_window_tx_time_min",
        "full_window_energy_wh",
    ]

    missing_columns = [column for column in required_columns if column not in df.columns]

    if missing_columns:
        raise ValueError(
            "pass_hardware_results.csv is missing required columns: "
            + ", ".join(missing_columns)
        )

    return df


def build_smoothed_curve(df, x_column, y_column, bin_width_deg=5.0):
    x = df[x_column].to_numpy(dtype=float)
    y = df[y_column].to_numpy(dtype=float)

    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]

    if len(x) == 0:
        return pd.DataFrame(
            columns=[
                "bin_center_deg",
                "mean_value",
                "median_value",
                "count",
            ]
        )

    bin_edges = np.arange(0.0, 90.0 + bin_width_deg, bin_width_deg)
    bin_indices = np.digitize(x, bin_edges) - 1

    rows = []

    for i in range(len(bin_edges) - 1):
        mask = bin_indices == i

        if not np.any(mask):
            continue

        bin_x = x[mask]
        bin_y = y[mask]

        rows.append(
            {
                "bin_center_deg": 0.5 * (bin_edges[i] + bin_edges[i + 1]),
                "mean_value": np.mean(bin_y),
                "median_value": np.median(bin_y),
                "count": len(bin_y),
            }
        )

    return pd.DataFrame(rows)


def make_scatter_plus_smooth_plot(
    df,
    x_column,
    y_column,
    y_label,
    title,
    output_filename,
    mission_target_mb=None,
):
    plt.figure(figsize=(10, 6))

    plt.scatter(
        df[x_column],
        df[y_column],
        alpha=0.65,
        s=30,
        label="Individual passes",
    )

    smooth_df = build_smoothed_curve(df, x_column, y_column, ELEVATION_BIN_WIDTH_DEG)

    if not smooth_df.empty:
        plt.plot(
            smooth_df["bin_center_deg"],
            smooth_df["mean_value"],
            marker="o",
            linewidth=2,
            label=f"{int(ELEVATION_BIN_WIDTH_DEG)}° binned mean",
        )

    if mission_target_mb is not None:
        plt.axhline(
            mission_target_mb,
            linestyle="--",
            linewidth=2,
            label=f"Mission target = {mission_target_mb:g} MB",
        )

    plt.xlabel("Peak Pass Elevation (deg)")
    plt.ylabel(y_label)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    plt.savefig(PLOTS_DIRECTORY / output_filename, dpi=300)
    plt.close()


def main():
    make_output_directory()

    df = load_pass_results()

    make_scatter_plus_smooth_plot(
        df=df,
        x_column="max_elevation_deg",
        y_column="max_payload_possible_mb",
        y_label="Maximum Transferable Payload (MB)",
        title="Peak Pass Elevation vs Maximum Transferable Payload",
        output_filename="elevation_vs_max_payload.png",
        mission_target_mb=MISSION_TARGET_MB,
    )

    make_scatter_plus_smooth_plot(
        df=df,
        x_column="max_elevation_deg",
        y_column="full_window_energy_wh",
        y_label="Full-Window Transmission Energy (Wh)",
        title="Peak Pass Elevation vs Full-Window Transmission Energy",
        output_filename="elevation_vs_energy.png",
    )

    make_scatter_plus_smooth_plot(
        df=df,
        x_column="max_elevation_deg",
        y_column="full_window_tx_time_min",
        y_label="Full-Window Transmission Window (min)",
        title="Peak Pass Elevation vs Full-Window Transmission Window",
        output_filename="elevation_vs_tx_time.png",
    )

    print("Saved plots to:", PLOTS_DIRECTORY)


if __name__ == "__main__":
    main()