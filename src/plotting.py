import os

import matplotlib.pyplot as plt
import numpy as np

from config import (
    TX_POWER_DBM_OPTIONS,
    SAT_ANTENNA_GAIN_DBI_OPTIONS,
    GROUND_ANTENNA_GAIN_DBI_OPTIONS,
    RATE_PLOT_DIRECTORY,
    ENERGY_PLOT_DIRECTORY,
    PAYLOAD_PLOT_DIRECTORY,
    TX_TIME_PLOT_DIRECTORY,
    HARDWARE_TRADE_PLOT_DIRECTORY,
)


# ============================================================================
# RATE VS ELEVATION
# ============================================================================

def make_rate_plots(rate_df):
    os.makedirs(RATE_PLOT_DIRECTORY, exist_ok=True)

    for sat_gain_dbi in SAT_ANTENNA_GAIN_DBI_OPTIONS:
        for ground_gain_dbi in GROUND_ANTENNA_GAIN_DBI_OPTIONS:
            plt.figure(figsize=(10, 6))

            for tx_power_dbm in TX_POWER_DBM_OPTIONS:
                df = rate_df[
                    (rate_df["sat_antenna_gain_dbi"] == sat_gain_dbi)
                    & (rate_df["ground_antenna_gain_dbi"] == ground_gain_dbi)
                    & (rate_df["tx_power_dbm"] == tx_power_dbm)
                ]

                plt.step(
                    df["elevation_deg"],
                    df["useful_rate_kbps"],
                    where="post",
                    label=f"{tx_power_dbm:g} dBm",
                )

            plt.xlabel("Satellite Elevation (deg)")
            plt.ylabel("Maximum Supported Payload Rate (kbps)")

            plt.title(
                "SX1280 Data Rate vs Elevation\n"
                f"Satellite Gain = {sat_gain_dbi:g} dBi, "
                f"Ground Gain = {ground_gain_dbi:g} dBi"
            )

            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()

            filename = (
                f"sat_{sat_gain_dbi:g}dBi_"
                f"ground_{ground_gain_dbi:g}dBi.png"
            )

            plt.savefig(
                RATE_PLOT_DIRECTORY / filename,
                dpi=300,
            )

            plt.close()


# ============================================================================
# GENERIC PASS METRIC PLOT
# ============================================================================

def make_pass_metric_plots(
    sweep_df,
    output_directory,
    y_column,
    ylabel,
    title_prefix,
    successful_only=False,
):
    os.makedirs(output_directory, exist_ok=True)

    for sat_gain_dbi in SAT_ANTENNA_GAIN_DBI_OPTIONS:
        for ground_gain_dbi in GROUND_ANTENNA_GAIN_DBI_OPTIONS:
            plt.figure(figsize=(10, 6))

            for tx_power_dbm in TX_POWER_DBM_OPTIONS:
                df = sweep_df[
                    (sweep_df["sat_antenna_gain_dbi"] == sat_gain_dbi)
                    & (sweep_df["ground_antenna_gain_dbi"] == ground_gain_dbi)
                    & (sweep_df["tx_power_dbm"] == tx_power_dbm)
                ].sort_values("max_elevation_deg")

                if successful_only:
                    y_values = np.where(
                        df["optimized_completed"],
                        df[y_column],
                        np.nan,
                    )
                else:
                    y_values = df[y_column]

                plt.plot(
                    df["max_elevation_deg"],
                    y_values,
                    marker="o",
                    label=f"{tx_power_dbm:g} dBm",
                )

            plt.xlabel("Actual Peak Elevation of Predicted Pass (deg)")
            plt.ylabel(ylabel)

            plt.title(
                f"{title_prefix}\n"
                f"Satellite Gain = {sat_gain_dbi:g} dBi, "
                f"Ground Gain = {ground_gain_dbi:g} dBi"
            )

            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()

            filename = (
                f"sat_{sat_gain_dbi:g}dBi_"
                f"ground_{ground_gain_dbi:g}dBi.png"
            )

            plt.savefig(
                output_directory / filename,
                dpi=300,
            )

            plt.close()


# ============================================================================
# PASS PLOTS
# ============================================================================

def make_pass_plots(sweep_df):
    make_pass_metric_plots(
        sweep_df,
        ENERGY_PLOT_DIRECTORY,
        "optimized_energy_wh",
        "Electrical Energy to Send Payload (Wh)",
        "Optimized Downlink Energy",
        successful_only=True,
    )

    make_pass_metric_plots(
        sweep_df,
        PAYLOAD_PLOT_DIRECTORY,
        "optimized_payload_sent_mb",
        "Payload Transmitted (MB)",
        "Payload Delivered During Predicted Pass",
        successful_only=False,
    )

    make_pass_metric_plots(
        sweep_df,
        TX_TIME_PLOT_DIRECTORY,
        "optimized_tx_time_min",
        "TX-On Time (min)",
        "Optimized Transmission Time",
        successful_only=True,
    )


# ============================================================================
# HARDWARE TRADE PLOT
#
# Shows the minimum required ground antenna gain for each combination of
# satellite antenna gain and PA output power
# ============================================================================

def make_hardware_trade_plot(minimum_ground_gain_df):
    os.makedirs(HARDWARE_TRADE_PLOT_DIRECTORY, exist_ok=True)

    if minimum_ground_gain_df.empty:
        return

    plt.figure(figsize=(10, 6))

    for tx_power_dbm in sorted(
        minimum_ground_gain_df["tx_power_dbm"].unique()
    ):
        df = minimum_ground_gain_df[
            minimum_ground_gain_df["tx_power_dbm"] == tx_power_dbm
        ].sort_values("sat_antenna_gain_dbi")

        plt.plot(
            df["sat_antenna_gain_dbi"],
            df["minimum_ground_antenna_gain_dbi"],
            marker="o",
            label=f"{tx_power_dbm:g} dBm TX",
        )

    plt.xlabel("Satellite Antenna Gain (dBi)")
    plt.ylabel("Minimum Required Ground Antenna Gain (dBi)")

    plt.title(
        "Antenna Gain Trade for Successful Payload Downlink"
    )

    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        HARDWARE_TRADE_PLOT_DIRECTORY
        / "minimum_ground_gain_vs_satellite_gain.png",
        dpi=300,
    )

    plt.close()