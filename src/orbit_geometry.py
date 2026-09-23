import math
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from skyfield.api import EarthSatellite, load, wgs84

from config import (
    GROUND_STATION_LAT_DEG,
    GROUND_STATION_LON_DEG,
    GROUND_STATION_ELEVATION_M,
    TLE_NAME,
    TLE_LINE1,
    TLE_LINE2,
    PASS_SEARCH_START_UTC,
    PASS_SEARCH_HOURS,
    PASS_HORIZON_DEG,
    PASS_SAMPLE_STEP_S,
)


# ============================================================================
# CREATE ORBIT / GROUND STATION
# ============================================================================

def create_orbit_context():
    timescale = load.timescale(builtin=True)

    satellite = EarthSatellite(
        TLE_LINE1,
        TLE_LINE2,
        TLE_NAME,
        timescale,
    )

    ground_station = wgs84.latlon(
        latitude_degrees=GROUND_STATION_LAT_DEG,
        longitude_degrees=GROUND_STATION_LON_DEG,
        elevation_m=GROUND_STATION_ELEVATION_M,
    )

    return timescale, satellite, ground_station


# ============================================================================
# DATE HELPERS
# ============================================================================

def parse_utc_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# ============================================================================
# FIND ACTUAL PASSES
# ============================================================================

def find_passes(timescale, satellite, ground_station):
    start_datetime = parse_utc_datetime(PASS_SEARCH_START_UTC)
    end_datetime = start_datetime + timedelta(hours=PASS_SEARCH_HOURS)

    start_time = timescale.from_datetime(start_datetime)
    end_time = timescale.from_datetime(end_datetime)

    event_times, events = satellite.find_events(
        ground_station,
        start_time,
        end_time,
        altitude_degrees=PASS_HORIZON_DEG,
    )

    passes = []
    current_pass = None

    for event_time, event in zip(event_times, events):
        # Rise
        if event == 0:
            current_pass = {
                "rise_time": event_time,
            }

        # Culmination
        elif event == 1 and current_pass is not None:
            current_pass["culmination_time"] = event_time

        # Set
        elif event == 2 and current_pass is not None and "culmination_time" in current_pass:
            current_pass["set_time"] = event_time

            topocentric = (satellite - ground_station).at(
                current_pass["culmination_time"]
            )

            altitude, azimuth, distance = topocentric.altaz()

            current_pass["pass_id"] = len(passes) + 1
            current_pass["max_elevation_deg"] = altitude.degrees
            current_pass["peak_azimuth_deg"] = azimuth.degrees
            current_pass["peak_slant_range_km"] = distance.km

            rise_datetime = current_pass["rise_time"].utc_datetime()
            set_datetime = current_pass["set_time"].utc_datetime()

            current_pass["duration_s"] = (
                set_datetime - rise_datetime
            ).total_seconds()

            passes.append(current_pass)
            current_pass = None

    return passes


# ============================================================================
# SAMPLE ONE PASS
# ============================================================================

def sample_pass(timescale, satellite, ground_station, pass_info):
    duration_s = pass_info["duration_s"]

    number_of_samples = max(
        2,
        int(math.ceil(duration_s / PASS_SAMPLE_STEP_S)) + 1,
    )

    times = timescale.linspace(
        pass_info["rise_time"],
        pass_info["set_time"],
        number_of_samples,
    )

    topocentric = (satellite - ground_station).at(times)
    altitude, azimuth, distance = topocentric.altaz()

    elapsed_s = np.linspace(0.0, duration_s, number_of_samples)

    peak_time_tt = pass_info["culmination_time"].tt
    time_from_peak_s = (times.tt - peak_time_tt) * 86400.0

    utc_strings = [
        value.isoformat()
        for value in times.utc_datetime()
    ]

    los_angular_rate_deg_s = estimate_los_angular_rate_deg_s(
        elevation_deg=altitude.degrees,
        azimuth_deg=azimuth.degrees,
        elapsed_s=elapsed_s,
    )

    return pd.DataFrame(
        {
            "pass_id": pass_info["pass_id"],
            "utc": utc_strings,
            "elapsed_s": elapsed_s,
            "time_from_peak_s": time_from_peak_s,
            "elevation_deg": altitude.degrees,
            "azimuth_deg": azimuth.degrees,
            "slant_range_km": distance.km,
            "los_angular_rate_deg_s": los_angular_rate_deg_s,
        }
    )


# ============================================================================
# LINE-OF-SIGHT ANGULAR RATE
#
# Approximates how fast a target-tracking antenna would need to slew to
# keep boresight on the other end of the link
#
# This uses the ground-station-frame (topocentric az/el) line-of-sight rate
# as a proxy for the true satellite-body-frame tracking rate the spacecraft
# ADCS would need to sustain. The two are not identical (they are rates in
# different rotating frames), but are the same order of magnitude, and this
# is a reasonable approximation until a rigorous ECI-frame slew-rate
# calculation is needed
# ============================================================================

def estimate_los_angular_rate_deg_s(elevation_deg, azimuth_deg, elapsed_s):
    elevation_rad = np.radians(elevation_deg)
    azimuth_rad = np.radians(azimuth_deg)

    line_of_sight_unit_vectors = np.stack(
        [
            np.cos(elevation_rad) * np.sin(azimuth_rad),
            np.cos(elevation_rad) * np.cos(azimuth_rad),
            np.sin(elevation_rad),
        ],
        axis=1,
    )

    dot_products = np.clip(
        np.sum(
            line_of_sight_unit_vectors[:-1] * line_of_sight_unit_vectors[1:],
            axis=1,
        ),
        -1.0,
        1.0,
    )

    angle_between_deg = np.degrees(np.arccos(dot_products))
    dt_s = np.diff(elapsed_s)

    rate_deg_s = np.zeros(len(elapsed_s))

    with np.errstate(divide="ignore", invalid="ignore"):
        rate_deg_s[1:] = np.where(
            dt_s > 0,
            angle_between_deg / dt_s,
            0.0,
        )

    if len(rate_deg_s) > 1:
        rate_deg_s[0] = rate_deg_s[1]

    return rate_deg_s


# ============================================================================
# PASS SUMMARY
# ============================================================================

def passes_to_dataframe(passes):
    rows = []

    for pass_info in passes:
        rows.append(
            {
                "pass_id": pass_info["pass_id"],
                "rise_utc": pass_info["rise_time"].utc_datetime().isoformat(),
                "culmination_utc": pass_info["culmination_time"].utc_datetime().isoformat(),
                "set_utc": pass_info["set_time"].utc_datetime().isoformat(),
                "max_elevation_deg": pass_info["max_elevation_deg"],
                "peak_azimuth_deg": pass_info["peak_azimuth_deg"],
                "peak_slant_range_km": pass_info["peak_slant_range_km"],
                "duration_min": pass_info["duration_s"] / 60.0,
            }
        )

    return pd.DataFrame(rows)