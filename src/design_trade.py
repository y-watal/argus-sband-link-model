import numpy as np
import pandas as pd

from config import (
    MAX_S_BAND_TX_POWER_W,
    MESSAGE_SIZE_MB,
)


# ============================================================================
# BUILD HARDWARE TRADE SUMMARY
#
# Uses every predicted pass, whatever its peak elevation
#
# Image size is variable, so the headline numbers are the maximum payload
# each pass can carry. A combination is valid if it is within the power
# budget and the link closes (delivers some data) on every pass. Whether a
# MESSAGE_SIZE_MB reference image fits in one pass is reported for
# information only
# ============================================================================

def build_hardware_trade_summary(pass_sweep_df):
    group_columns = [
        "tx_power_dbm",
        "sat_antenna_gain_dbi",
        "ground_antenna_gain_dbi",
        "sat_pointing_error_deg",
        "ground_tracking_error_deg",
    ]

    rows = []

    for hardware, group in pass_sweep_df.groupby(group_columns):
        (
            tx_power_dbm,
            sat_gain_dbi,
            ground_gain_dbi,
            sat_pointing_error_deg,
            ground_tracking_error_deg,
        ) = hardware

        total_tx_dc_w = float(group["total_tx_dc_w"].iloc[0])

        passes_considered = len(group)

        payload_mb = group["max_payload_possible_mb"]

        passes_with_link = int((payload_mb > 0).sum())

        within_power_budget = total_tx_dc_w <= MAX_S_BAND_TX_POWER_W

        link_closes_all_passes = (
            passes_considered > 0
            and passes_with_link == passes_considered
        )

        design_valid = (
            within_power_budget
            and link_closes_all_passes
        )

        smallest_pass_row = group.loc[payload_mb.idxmin()]

        reference_image_passes = int(
            group["optimized_completed"].astype(bool).sum()
        )

        rows.append(
            {
                "tx_power_dbm": tx_power_dbm,
                "sat_antenna_gain_dbi": sat_gain_dbi,
                "ground_antenna_gain_dbi": ground_gain_dbi,
                "sat_pointing_error_deg": sat_pointing_error_deg,
                "ground_tracking_error_deg": ground_tracking_error_deg,
                "total_tx_dc_w": total_tx_dc_w,
                "max_allowed_tx_dc_w": MAX_S_BAND_TX_POWER_W,
                "within_power_budget": within_power_budget,
                "passes_considered": passes_considered,
                "passes_with_link": passes_with_link,
                "min_pass_payload_mb": float(payload_mb.min()),
                "median_pass_payload_mb": float(payload_mb.median()),
                "max_pass_payload_mb": float(payload_mb.max()),
                "total_payload_mb": float(payload_mb.sum()),
                "min_payload_pass_max_elevation_deg": float(
                    smallest_pass_row["max_elevation_deg"]
                ),
                "worst_full_window_tx_time_min": float(
                    group["full_window_tx_time_min"].max()
                ),
                "worst_full_window_energy_wh": float(
                    group["full_window_energy_wh"].max()
                ),
                "reference_image_mb": MESSAGE_SIZE_MB,
                "reference_image_passes": reference_image_passes,
                "link_closes_all_passes": link_closes_all_passes,
                "design_valid": design_valid,
            }
        )

    return pd.DataFrame(rows).sort_values(
        [
            "tx_power_dbm",
            "sat_antenna_gain_dbi",
            "ground_antenna_gain_dbi",
            "sat_pointing_error_deg",
            "ground_tracking_error_deg",
        ]
    ).reset_index(drop=True)


# ============================================================================
# MINIMUM GROUND ANTENNA GAIN
#
# For every satellite antenna / TX power / pointing-accuracy combination,
# find the smallest ground antenna gain for which the link closes on every
# pass, and how much the smallest pass can carry with that ground antenna
# ============================================================================

def build_minimum_ground_gain_table(hardware_trade_df):
    valid_df = hardware_trade_df[
        hardware_trade_df["design_valid"]
    ].copy()

    group_columns = [
        "tx_power_dbm",
        "sat_antenna_gain_dbi",
        "sat_pointing_error_deg",
        "ground_tracking_error_deg",
    ]

    if valid_df.empty:
        return pd.DataFrame(
            columns=group_columns + [
                "minimum_ground_antenna_gain_dbi",
                "total_tx_dc_w",
                "min_pass_payload_mb",
                "median_pass_payload_mb",
                "min_payload_pass_max_elevation_deg",
            ]
        )

    rows = []

    for hardware, group in valid_df.groupby(group_columns):
        (
            tx_power_dbm,
            sat_gain_dbi,
            sat_pointing_error_deg,
            ground_tracking_error_deg,
        ) = hardware

        best_row = group.loc[
            group["ground_antenna_gain_dbi"].idxmin()
        ]

        rows.append(
            {
                "tx_power_dbm": tx_power_dbm,
                "sat_antenna_gain_dbi": sat_gain_dbi,
                "sat_pointing_error_deg": sat_pointing_error_deg,
                "ground_tracking_error_deg": ground_tracking_error_deg,
                "minimum_ground_antenna_gain_dbi": (
                    best_row["ground_antenna_gain_dbi"]
                ),
                "total_tx_dc_w": best_row["total_tx_dc_w"],
                "min_pass_payload_mb": best_row["min_pass_payload_mb"],
                "median_pass_payload_mb": (
                    best_row["median_pass_payload_mb"]
                ),
                "min_payload_pass_max_elevation_deg": (
                    best_row["min_payload_pass_max_elevation_deg"]
                ),
            }
        )

    return pd.DataFrame(rows).sort_values(
        [
            "tx_power_dbm",
            "sat_antenna_gain_dbi",
            "sat_pointing_error_deg",
            "ground_tracking_error_deg",
        ]
    ).reset_index(drop=True)


# ============================================================================
# PASS-LEVEL HARDWARE RESULTS
#
# One row = one actual pass + one complete hardware configuration
# ============================================================================

def build_pass_hardware_results(pass_sweep_df):
    columns = [
        "pass_id",
        "rise_utc",
        "max_elevation_deg",
        "pass_duration_min",
        "tx_power_dbm",
        "sat_antenna_gain_dbi",
        "ground_antenna_gain_dbi",
        "sat_pointing_error_deg",
        "ground_tracking_error_deg",
        "total_tx_dc_w",
        "pa_dc_w",
        "max_payload_possible_mb",
        "full_window_tx_time_min",
        "full_window_energy_wh",
        "optimized_completed",
        "optimized_payload_sent_mb",
        "optimized_tx_time_min",
        "optimized_start_elevation_deg",
        "optimized_end_elevation_deg",
        "optimized_energy_wh",
    ]

    result_df = pass_sweep_df[columns].copy()

    result_df["within_power_budget"] = (
        result_df["total_tx_dc_w"] <= MAX_S_BAND_TX_POWER_W
    )

    result_df["hardware_and_link_valid"] = (
        result_df["within_power_budget"]
        & (result_df["max_payload_possible_mb"] > 0)
    )

    return result_df.sort_values(
        [
            "max_elevation_deg",
            "tx_power_dbm",
            "sat_antenna_gain_dbi",
            "ground_antenna_gain_dbi",
            "sat_pointing_error_deg",
            "ground_tracking_error_deg",
        ]
    ).reset_index(drop=True)


# ============================================================================
# HARDWARE COVERAGE SUMMARY
#
# A pass counts as successful if the link closes on it at all; payload,
# TX time and energy are for using the pass's whole usable window
# ============================================================================

def build_hardware_coverage_summary(pass_sweep_df):
    group_columns = [
        "tx_power_dbm",
        "sat_antenna_gain_dbi",
        "ground_antenna_gain_dbi",
        "sat_pointing_error_deg",
        "ground_tracking_error_deg",
    ]

    rows = []

    for hardware, group in pass_sweep_df.groupby(group_columns):
        (
            tx_power_dbm,
            sat_gain_dbi,
            ground_gain_dbi,
            sat_pointing_error_deg,
            ground_tracking_error_deg,
        ) = hardware

        total_tx_dc_w = float(group["total_tx_dc_w"].iloc[0])
        within_power_budget = total_tx_dc_w <= MAX_S_BAND_TX_POWER_W

        successful = group[
            group["max_payload_possible_mb"] > 0
        ].copy()

        total_passes = len(group)
        successful_pass_count = len(successful)

        total_payload_all_passes_mb = float(
            group["max_payload_possible_mb"].sum()
        )

        if successful.empty:
            minimum_successful_peak_elevation_deg = np.nan
            maximum_successful_peak_elevation_deg = np.nan
            min_successful_payload_mb = np.nan
            max_successful_payload_mb = np.nan
            worst_successful_tx_time_min = np.nan
            worst_successful_energy_wh = np.nan
            best_successful_tx_time_min = np.nan
            best_successful_energy_wh = np.nan

        else:
            minimum_successful_peak_elevation_deg = float(
                successful["max_elevation_deg"].min()
            )

            maximum_successful_peak_elevation_deg = float(
                successful["max_elevation_deg"].max()
            )

            min_successful_payload_mb = float(
                successful["max_payload_possible_mb"].min()
            )

            max_successful_payload_mb = float(
                successful["max_payload_possible_mb"].max()
            )

            worst_successful_tx_time_min = float(
                successful["full_window_tx_time_min"].max()
            )

            worst_successful_energy_wh = float(
                successful["full_window_energy_wh"].max()
            )

            best_successful_tx_time_min = float(
                successful["full_window_tx_time_min"].min()
            )

            best_successful_energy_wh = float(
                successful["full_window_energy_wh"].min()
            )

        rows.append(
            {
                "tx_power_dbm": tx_power_dbm,
                "sat_antenna_gain_dbi": sat_gain_dbi,
                "ground_antenna_gain_dbi": ground_gain_dbi,
                "sat_pointing_error_deg": sat_pointing_error_deg,
                "ground_tracking_error_deg": ground_tracking_error_deg,
                "total_tx_dc_w": total_tx_dc_w,
                "within_power_budget": within_power_budget,
                "total_passes_tested": total_passes,
                "successful_passes": successful_pass_count,
                "pass_success_fraction": (
                    successful_pass_count / total_passes
                    if total_passes > 0
                    else 0.0
                ),
                "minimum_successful_peak_elevation_deg": (
                    minimum_successful_peak_elevation_deg
                ),
                "maximum_successful_peak_elevation_deg": (
                    maximum_successful_peak_elevation_deg
                ),
                "min_successful_payload_mb": min_successful_payload_mb,
                "max_successful_payload_mb": max_successful_payload_mb,
                "total_payload_all_passes_mb": total_payload_all_passes_mb,
                "best_successful_tx_time_min": (
                    best_successful_tx_time_min
                ),
                "worst_successful_tx_time_min": (
                    worst_successful_tx_time_min
                ),
                "best_successful_energy_wh": (
                    best_successful_energy_wh
                ),
                "worst_successful_energy_wh": (
                    worst_successful_energy_wh
                ),
            }
        )

    return pd.DataFrame(rows).sort_values(
        [
            "tx_power_dbm",
            "sat_antenna_gain_dbi",
            "ground_antenna_gain_dbi",
            "sat_pointing_error_deg",
            "ground_tracking_error_deg",
        ]
    ).reset_index(drop=True)