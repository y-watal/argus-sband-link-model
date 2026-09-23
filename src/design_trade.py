import numpy as np
import pandas as pd

from config import (
    DESIGN_MIN_PEAK_ELEVATION_DEG,
    MAX_S_BAND_TX_POWER_W,
)


# ============================================================================
# BUILD HARDWARE TRADE SUMMARY
#
# This table uses only passes whose peak elevation is at least the configured
# design threshold
# ============================================================================

def build_hardware_trade_summary(pass_sweep_df):
    design_pass_df = pass_sweep_df[
        pass_sweep_df["max_elevation_deg"] >= DESIGN_MIN_PEAK_ELEVATION_DEG
    ].copy()

    if design_pass_df.empty:
        raise RuntimeError(
            "No passes satisfy the configured minimum design elevation."
        )

    group_columns = [
        "tx_power_dbm",
        "sat_antenna_gain_dbi",
        "ground_antenna_gain_dbi",
        "sat_pointing_error_deg",
        "ground_tracking_error_deg",
    ]

    rows = []

    for hardware, group in design_pass_df.groupby(group_columns):
        (
            tx_power_dbm,
            sat_gain_dbi,
            ground_gain_dbi,
            sat_pointing_error_deg,
            ground_tracking_error_deg,
        ) = hardware

        total_tx_dc_w = float(group["total_tx_dc_w"].iloc[0])

        completed_mask = group["optimized_completed"].astype(bool)
        successful_passes = group[completed_mask]

        passes_considered = len(group)
        passes_completed = int(completed_mask.sum())

        pass_success_fraction = (
            passes_completed / passes_considered
            if passes_considered > 0
            else 0.0
        )

        within_power_budget = total_tx_dc_w <= MAX_S_BAND_TX_POWER_W

        meets_link_requirement = (
            passes_considered > 0
            and passes_completed == passes_considered
        )

        design_valid = (
            within_power_budget
            and meets_link_requirement
        )

        minimum_payload_sent_mb = float(
            group["optimized_payload_sent_mb"].min()
        )

        if successful_passes.empty:
            worst_case_energy_wh = np.nan
            median_energy_wh = np.nan
            worst_case_tx_time_min = np.nan
            worst_case_max_elevation_deg = np.nan

        else:
            worst_energy_row = successful_passes.loc[
                successful_passes["optimized_energy_wh"].idxmax()
            ]

            worst_time_row = successful_passes.loc[
                successful_passes["optimized_tx_time_min"].idxmax()
            ]

            worst_case_energy_wh = float(
                worst_energy_row["optimized_energy_wh"]
            )

            median_energy_wh = float(
                successful_passes["optimized_energy_wh"].median()
            )

            worst_case_tx_time_min = float(
                worst_time_row["optimized_tx_time_min"]
            )

            worst_case_max_elevation_deg = float(
                worst_time_row["max_elevation_deg"]
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
                "design_min_peak_elevation_deg": DESIGN_MIN_PEAK_ELEVATION_DEG,
                "design_passes_considered": passes_considered,
                "design_passes_completed": passes_completed,
                "pass_success_fraction": pass_success_fraction,
                "minimum_payload_sent_mb": minimum_payload_sent_mb,
                "worst_case_tx_time_min": worst_case_tx_time_min,
                "worst_case_max_elevation_deg": worst_case_max_elevation_deg,
                "median_energy_wh": median_energy_wh,
                "worst_case_energy_wh": worst_case_energy_wh,
                "meets_link_requirement": meets_link_requirement,
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
# find the smallest ground antenna gain that satisfies the configured design
# requirement. With the satellite antenna and TX power now fixed to the
# selected hardware, this table is mainly useful for reading off how much
# satellite pointing accuracy and ground tracking accuracy actually buy you
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
                "worst_case_max_elevation_deg",
                "worst_case_tx_time_min",
                "worst_case_energy_wh",
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
                "worst_case_max_elevation_deg": (
                    best_row["worst_case_max_elevation_deg"]
                ),
                "worst_case_tx_time_min": (
                    best_row["worst_case_tx_time_min"]
                ),
                "worst_case_energy_wh": (
                    best_row["worst_case_energy_wh"]
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
        & result_df["optimized_completed"]
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
# This ignores the 30 degree design threshold
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
            group["optimized_completed"]
        ].copy()

        total_passes = len(group)
        successful_pass_count = len(successful)

        if successful.empty:
            minimum_successful_peak_elevation_deg = np.nan
            maximum_successful_peak_elevation_deg = np.nan
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

            worst_successful_tx_time_min = float(
                successful["optimized_tx_time_min"].max()
            )

            worst_successful_energy_wh = float(
                successful["optimized_energy_wh"].max()
            )

            best_successful_tx_time_min = float(
                successful["optimized_tx_time_min"].min()
            )

            best_successful_energy_wh = float(
                successful["optimized_energy_wh"].min()
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