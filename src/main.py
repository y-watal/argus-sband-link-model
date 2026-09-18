import numpy as np
import pandas as pd

from config import (
    DATA_OUTPUT_DIRECTORY,
    MESSAGE_SIZE_MB,
    MESSAGE_SIZE_BITS,
    TX_POWER_DBM_OPTIONS,
    SAT_ANTENNA_GAIN_DBI_OPTIONS,
    GROUND_ANTENNA_GAIN_DBI_OPTIONS,
    GROUND_STATION_LAT_DEG,
    GROUND_STATION_LON_DEG,
    PASS_SEARCH_HOURS,
)

from orbit_geometry import (
    create_orbit_context,
    find_passes,
    sample_pass,
    passes_to_dataframe,
)

from radio_link import build_link_timeline
from power_model import transmitter_dc_power_w
from plotting import make_rate_plots, make_pass_plots


# ============================================================================
# HELPERS
# ============================================================================

def interpolate_value(times, values, target_time):
    return float(np.interp(target_time, times, values))


# ============================================================================
# POLICY 1
#
# START TRANSMITTING AS SOON AS A LINK EXISTS
# ============================================================================

def simulate_earliest_transmission(link_df, tx_power_dbm):
    times = link_df["elapsed_s"].to_numpy()
    elevations = link_df["elevation_deg"].to_numpy()
    rates = link_df["useful_rate_bps"].to_numpy()

    power = transmitter_dc_power_w(tx_power_dbm)

    remaining_bits = MESSAGE_SIZE_BITS
    total_bits = 0.0
    tx_time_s = 0.0

    start_time_s = np.nan
    end_time_s = np.nan

    for index in range(len(times) - 1):
        dt_s = times[index + 1] - times[index]
        rate_bps = rates[index]

        if dt_s <= 0 or rate_bps <= 0 or remaining_bits <= 0:
            continue

        if np.isnan(start_time_s):
            start_time_s = times[index]

        seconds_to_finish = remaining_bits / rate_bps
        active_time_s = min(dt_s, seconds_to_finish)

        bits_sent = rate_bps * active_time_s

        total_bits += bits_sent
        remaining_bits -= bits_sent
        tx_time_s += active_time_s

        if remaining_bits <= 1e-9:
            remaining_bits = 0.0
            end_time_s = times[index] + active_time_s
            break

    completed = remaining_bits <= 0

    if not completed and not np.isnan(start_time_s):
        positive_indices = np.where(rates[:-1] > 0)[0]

        if len(positive_indices) > 0:
            final_index = positive_indices[-1]
            end_time_s = times[final_index + 1]

    start_elevation_deg = np.nan
    end_elevation_deg = np.nan

    if not np.isnan(start_time_s):
        start_elevation_deg = interpolate_value(
            times,
            elevations,
            start_time_s,
        )

    if not np.isnan(end_time_s):
        end_elevation_deg = interpolate_value(
            times,
            elevations,
            end_time_s,
        )

    energy_j = power["total_dc_w"] * tx_time_s

    return {
        "completed": completed,
        "payload_sent_mb": min(total_bits / 8.0 / 1e6, MESSAGE_SIZE_MB),
        "tx_time_s": tx_time_s,
        "tx_time_min": tx_time_s / 60.0,
        "start_time_s": start_time_s,
        "end_time_s": end_time_s,
        "start_elevation_deg": start_elevation_deg,
        "end_elevation_deg": end_elevation_deg,
        "energy_j": energy_j,
        "energy_wh": energy_j / 3600.0,
    }


# ============================================================================
# POLICY 2
#
# FIND THE SHORTEST CONTIGUOUS WINDOW THAT CAN SEND 5 MB
# ============================================================================

def simulate_optimized_transmission(link_df, tx_power_dbm):
    times = link_df["elapsed_s"].to_numpy()
    elevations = link_df["elevation_deg"].to_numpy()
    rates = link_df["useful_rate_bps"].to_numpy()

    dt_s = np.diff(times)

    interval_rates = rates[:-1]
    interval_bits = interval_rates * dt_s

    total_possible_bits = np.sum(interval_bits)

    power = transmitter_dc_power_w(tx_power_dbm)

    # Pass cannot carry all 5 MB
    if total_possible_bits < MESSAGE_SIZE_BITS:
        active = interval_rates > 0

        tx_time_s = np.sum(dt_s[active])
        energy_j = power["total_dc_w"] * tx_time_s

        if np.any(active):
            active_indices = np.where(active)[0]

            start_index = active_indices[0]
            end_index = active_indices[-1]

            start_time_s = times[start_index]
            end_time_s = times[end_index + 1]

            start_elevation_deg = interpolate_value(
                times,
                elevations,
                start_time_s,
            )

            end_elevation_deg = interpolate_value(
                times,
                elevations,
                end_time_s,
            )

        else:
            start_time_s = np.nan
            end_time_s = np.nan
            start_elevation_deg = np.nan
            end_elevation_deg = np.nan

        return {
            "completed": False,
            "payload_sent_mb": total_possible_bits / 8.0 / 1e6,
            "tx_time_s": tx_time_s,
            "tx_time_min": tx_time_s / 60.0,
            "start_time_s": start_time_s,
            "end_time_s": end_time_s,
            "start_elevation_deg": start_elevation_deg,
            "end_elevation_deg": end_elevation_deg,
            "energy_j": energy_j,
            "energy_wh": energy_j / 3600.0,
        }

    # Find shortest contiguous window whose integrated capacity >= 5 MB
    best = None

    left = 0
    window_bits = 0.0
    window_duration_s = 0.0

    for right in range(len(interval_bits)):
        window_bits += interval_bits[right]
        window_duration_s += dt_s[right]

        while (
            left < right
            and window_bits - interval_bits[left] >= MESSAGE_SIZE_BITS
        ):
            window_bits -= interval_bits[left]
            window_duration_s -= dt_s[left]
            left += 1

        if window_bits < MESSAGE_SIZE_BITS:
            continue

        excess_bits = window_bits - MESSAGE_SIZE_BITS

        # Try trimming excess from left side
        left_rate = interval_rates[left]
        left_trim_s = 0.0

        if left_rate > 0:
            left_trim_s = excess_bits / left_rate

        left_trim_s = min(left_trim_s, dt_s[left])

        candidate_duration_s = window_duration_s - left_trim_s
        candidate_start_s = times[left] + left_trim_s
        candidate_end_s = times[right + 1]

        # Try trimming excess from right side
        right_rate = interval_rates[right]

        if right_rate > 0 and excess_bits <= interval_bits[right]:
            right_trim_s = excess_bits / right_rate
            right_duration_s = window_duration_s - right_trim_s

            if right_duration_s < candidate_duration_s:
                candidate_duration_s = right_duration_s
                candidate_start_s = times[left]
                candidate_end_s = times[right + 1] - right_trim_s

        if best is None or candidate_duration_s < best["duration_s"]:
            best = {
                "duration_s": candidate_duration_s,
                "start_time_s": candidate_start_s,
                "end_time_s": candidate_end_s,
            }

    tx_time_s = best["duration_s"]
    start_time_s = best["start_time_s"]
    end_time_s = best["end_time_s"]

    start_elevation_deg = interpolate_value(
        times,
        elevations,
        start_time_s,
    )

    end_elevation_deg = interpolate_value(
        times,
        elevations,
        end_time_s,
    )

    energy_j = power["total_dc_w"] * tx_time_s

    return {
        "completed": True,
        "payload_sent_mb": MESSAGE_SIZE_MB,
        "tx_time_s": tx_time_s,
        "tx_time_min": tx_time_s / 60.0,
        "start_time_s": start_time_s,
        "end_time_s": end_time_s,
        "start_elevation_deg": start_elevation_deg,
        "end_elevation_deg": end_elevation_deg,
        "energy_j": energy_j,
        "energy_wh": energy_j / 3600.0,
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    DATA_OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    timescale, satellite, ground_station = create_orbit_context()

    passes = find_passes(
        timescale,
        satellite,
        ground_station,
    )

    if not passes:
        raise RuntimeError(
            "No passes were found in the configured search window."
        )

    pass_summary_df = passes_to_dataframe(passes)

    pass_summary_df.to_csv(
        DATA_OUTPUT_DIRECTORY / "actual_passes.csv",
        index=False,
    )

    print(
        "\n"
        "============================================================"
    )

    print("ARGUS S-BAND WHOLE-PASS LINK + ENERGY MODEL")

    print(
        "============================================================"
    )

    print("\nGround station:")
    print(f"  Latitude:  {GROUND_STATION_LAT_DEG:.6f} deg")
    print(f"  Longitude: {GROUND_STATION_LON_DEG:.6f} deg")

    print(
        f"\nPass search window: "
        f"{PASS_SEARCH_HOURS:.1f} hours"
    )

    print(
        f"Predicted passes found: "
        f"{len(passes)}"
    )

    print("\nActual predicted passes:")

    print(
        pass_summary_df.to_string(
            index=False
        )
    )

    # ========================================================================
    # USE HIGHEST-ELEVATION REAL PASS FOR RATE-VS-ELEVATION PLOTS
    # ========================================================================

    presentation_pass = max(
        passes,
        key=lambda value: value["max_elevation_deg"],
    )

    presentation_pass_df = sample_pass(
        timescale,
        satellite,
        ground_station,
        presentation_pass,
    )

    rising_pass_df = (
        presentation_pass_df[
            presentation_pass_df["time_from_peak_s"] <= 0
        ]
        .copy()
        .sort_values("elevation_deg")
    )

    rate_frames = []

    for sat_gain_dbi in SAT_ANTENNA_GAIN_DBI_OPTIONS:
        for ground_gain_dbi in GROUND_ANTENNA_GAIN_DBI_OPTIONS:
            for tx_power_dbm in TX_POWER_DBM_OPTIONS:
                link_df = build_link_timeline(
                    rising_pass_df,
                    tx_power_dbm,
                    sat_gain_dbi,
                    ground_gain_dbi,
                )

                link_df["tx_power_dbm"] = tx_power_dbm
                link_df["sat_antenna_gain_dbi"] = sat_gain_dbi
                link_df["ground_antenna_gain_dbi"] = ground_gain_dbi

                rate_frames.append(link_df)

    rate_df = pd.concat(
        rate_frames,
        ignore_index=True,
    )

    rate_df.to_csv(
        DATA_OUTPUT_DIRECTORY / "rate_vs_elevation_sweep.csv",
        index=False,
    )

    # ========================================================================
    # ACTUAL PASS + HARDWARE SWEEP
    # ========================================================================

    sweep_rows = []

    for pass_info in passes:
        pass_df = sample_pass(
            timescale,
            satellite,
            ground_station,
            pass_info,
        )

        for sat_gain_dbi in SAT_ANTENNA_GAIN_DBI_OPTIONS:
            for ground_gain_dbi in GROUND_ANTENNA_GAIN_DBI_OPTIONS:
                for tx_power_dbm in TX_POWER_DBM_OPTIONS:
                    link_df = build_link_timeline(
                        pass_df,
                        tx_power_dbm,
                        sat_gain_dbi,
                        ground_gain_dbi,
                    )

                    earliest = simulate_earliest_transmission(
                        link_df,
                        tx_power_dbm,
                    )

                    optimized = simulate_optimized_transmission(
                        link_df,
                        tx_power_dbm,
                    )

                    power = transmitter_dc_power_w(tx_power_dbm)

                    energy_saved_pct = np.nan

                    if (
                        earliest["completed"]
                        and optimized["completed"]
                        and earliest["energy_wh"] > 0
                    ):
                        energy_saved_pct = (
                            (
                                earliest["energy_wh"]
                                - optimized["energy_wh"]
                            )
                            / earliest["energy_wh"]
                            * 100.0
                        )

                    sweep_rows.append(
                        {
                            "pass_id": pass_info["pass_id"],
                            "rise_utc": pass_info[
                                "rise_time"
                            ].utc_datetime().isoformat(),
                            "max_elevation_deg": pass_info["max_elevation_deg"],
                            "pass_duration_min": pass_info["duration_s"] / 60.0,
                            "tx_power_dbm": tx_power_dbm,
                            "sat_antenna_gain_dbi": sat_gain_dbi,
                            "ground_antenna_gain_dbi": ground_gain_dbi,
                            "total_tx_dc_w": power["total_dc_w"],
                            "pa_dc_w": power["pa_dc_w"],
                            "earliest_completed": earliest["completed"],
                            "earliest_payload_sent_mb": earliest["payload_sent_mb"],
                            "earliest_tx_time_min": earliest["tx_time_min"],
                            "earliest_start_elevation_deg": earliest[
                                "start_elevation_deg"
                            ],
                            "earliest_end_elevation_deg": earliest[
                                "end_elevation_deg"
                            ],
                            "earliest_energy_wh": earliest["energy_wh"],
                            "optimized_completed": optimized["completed"],
                            "optimized_payload_sent_mb": optimized["payload_sent_mb"],
                            "optimized_tx_time_min": optimized["tx_time_min"],
                            "optimized_start_elevation_deg": optimized[
                                "start_elevation_deg"
                            ],
                            "optimized_end_elevation_deg": optimized[
                                "end_elevation_deg"
                            ],
                            "optimized_energy_wh": optimized["energy_wh"],
                            "energy_saved_pct": energy_saved_pct,
                        }
                    )

    sweep_df = pd.DataFrame(sweep_rows)

    sweep_df.to_csv(
        DATA_OUTPUT_DIRECTORY / "pass_energy_sweep.csv",
        index=False,
    )

    feasible_df = sweep_df[
        sweep_df["optimized_completed"]
    ].copy()

    feasible_df.to_csv(
        DATA_OUTPUT_DIRECTORY / "feasible_energy_designs.csv",
        index=False,
    )

    # ========================================================================
    # PLOTS
    # ========================================================================

    make_rate_plots(rate_df)
    make_pass_plots(sweep_df)

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print(
        f"\nTotal pass/hardware combinations tested: "
        f"{len(sweep_df)}"
    )

    print(
        f"Configurations that can send all 5 MB: "
        f"{len(feasible_df)}"
    )

    if not feasible_df.empty:
        best = (
            feasible_df
            .sort_values("optimized_energy_wh")
            .iloc[0]
        )

        print("\nLowest-energy successful case:")
        print(f"  Pass ID: {int(best['pass_id'])}")
        print(f"  Peak elevation: {best['max_elevation_deg']:.1f} deg")
        print(f"  TX RF power: {best['tx_power_dbm']:.1f} dBm")
        print(f"  Satellite gain: {best['sat_antenna_gain_dbi']:.1f} dBi")
        print(f"  Ground gain: {best['ground_antenna_gain_dbi']:.1f} dBi")

        print(
            f"  Optimized start elevation: "
            f"{best['optimized_start_elevation_deg']:.1f} deg"
        )

        print(
            f"  Optimized end elevation: "
            f"{best['optimized_end_elevation_deg']:.1f} deg"
        )

        print(
            f"  TX-on time: "
            f"{best['optimized_tx_time_min']:.3f} min"
        )

        print(
            f"  Energy: "
            f"{best['optimized_energy_wh']:.6f} Wh"
        )

        if not np.isnan(best["energy_saved_pct"]):
            print(
                f"  Energy saved vs immediate transmission: "
                f"{best['energy_saved_pct']:.1f}%"
            )

    print("\nFiles written:")
    print(f"  {DATA_OUTPUT_DIRECTORY / 'actual_passes.csv'}")
    print(f"  {DATA_OUTPUT_DIRECTORY / 'rate_vs_elevation_sweep.csv'}")
    print(f"  {DATA_OUTPUT_DIRECTORY / 'pass_energy_sweep.csv'}")
    print(f"  {DATA_OUTPUT_DIRECTORY / 'feasible_energy_designs.csv'}")


if __name__ == "__main__":
    main()