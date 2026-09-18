import numpy as np

from config import (
    DOWNLINK_FREQUENCY_MHZ,
    POINTING_LOSS_DB,
    OTHER_RF_LOSS_DB,
    LINK_MARGIN_DB,
    PROTOCOL_EFFICIENCY,
)


# ============================================================================
# SX1280 MODES
# ============================================================================

def build_sx1280_modes():
    modes = []

    spreading_factors = [5, 6, 7, 8, 9, 10, 11, 12]

    lora_raw_rates_kbps = {
        203: [31.72, 19.03, 11.10, 6.34, 3.57, 1.98, 1.09, 0.595],
        406: [63.44, 38.06, 22.20, 12.69, 7.14, 3.96, 2.18, 1.19],
        812: [126.88, 76.13, 44.41, 25.38, 14.27, 7.93, 4.36, 2.38],
        1625: [253.91, 152.34, 88.87, 50.78, 28.56, 15.87, 8.73, 4.76],
    }

    lora_sensitivity_dbm = {
        203: [-109, -111, -115, -118, -121, -124, -127, -130],
        406: [-107, -110, -113, -116, -119, -122, -125, -128],
        812: [-105, -108, -112, -115, -117, -120, -123, -126],
        1625: [-99, -103, -106, -109, -111, -114, -117, -120],
    }

    coding_factor = 4.0 / 5.0

    for bandwidth_khz in lora_raw_rates_kbps:
        for index, spreading_factor in enumerate(spreading_factors):
            rate_bps = (
                lora_raw_rates_kbps[bandwidth_khz][index]
                * 1000.0
                * coding_factor
            )

            modes.append(
                {
                    "mode_name": f"LoRa SF{spreading_factor} BW{bandwidth_khz}",
                    "modulation": "LoRa",
                    "radio_rate_bps": rate_bps,
                    "sensitivity_dbm": lora_sensitivity_dbm[bandwidth_khz][index],
                }
            )

    flrc_modes = [
        (1.300, -96),
        (0.975, -100),
        (0.650, -99),
        (1.040, -97),
        (0.780, -100),
        (0.520, -101),
        (0.650, -99),
        (0.488, -103),
        (0.325, -104),
        (0.520, -100),
        (0.390, -104),
        (0.260, -104),
        (0.325, -101),
        (0.244, -106),
        (0.163, -106),
        (0.260, -103),
        (0.195, -105),
        (0.130, -106),
    ]

    for rate_mbps, sensitivity_dbm in flrc_modes:
        modes.append(
            {
                "mode_name": f"FLRC {rate_mbps:.3f} Mbps",
                "modulation": "FLRC",
                "radio_rate_bps": rate_mbps * 1e6,
                "sensitivity_dbm": sensitivity_dbm,
            }
        )

    fsk_modes = [
        (2.000, -83),
        (1.600, -84),
        (1.000, -87),
        (1.000, -88),
        (0.800, -87),
        (0.800, -89),
        (0.500, -90),
        (0.500, -89),
        (0.400, -91),
        (0.400, -90),
        (0.250, -92),
        (0.250, -93),
        (0.125, -95),
    ]

    for rate_mbps, sensitivity_dbm in fsk_modes:
        modes.append(
            {
                "mode_name": f"FSK {rate_mbps:.3f} Mbps",
                "modulation": "FSK",
                "radio_rate_bps": rate_mbps * 1e6,
                "sensitivity_dbm": sensitivity_dbm,
            }
        )

    # Keep the more sensitive duplicate rate
    best = {}

    for mode in modes:
        key = (
            mode["modulation"],
            round(mode["radio_rate_bps"], 3),
        )

        if (
            key not in best
            or mode["sensitivity_dbm"] < best[key]["sensitivity_dbm"]
        ):
            best[key] = mode

    modes = list(best.values())

    # Fastest first
    modes.sort(
        key=lambda mode: mode["radio_rate_bps"],
        reverse=True,
    )

    return modes


SX1280_MODES = build_sx1280_modes()


# ============================================================================
# RF LINK MATH
# ============================================================================

def free_space_path_loss_db(distance_km):
    return (
        32.44
        + 20.0 * np.log10(distance_km)
        + 20.0 * np.log10(DOWNLINK_FREQUENCY_MHZ)
    )


def calculate_received_power_dbm(
    path_loss_db,
    tx_power_dbm,
    sat_gain_dbi,
    ground_gain_dbi,
):
    return (
        tx_power_dbm
        + sat_gain_dbi
        + ground_gain_dbi
        - path_loss_db
        - POINTING_LOSS_DB
        - OTHER_RF_LOSS_DB
    )


# ============================================================================
# FASTEST SUPPORTED MODE
# ============================================================================

def choose_fastest_modes(received_power_dbm):
    received_power_dbm = np.asarray(received_power_dbm, dtype=float)

    rates_bps = np.zeros(len(received_power_dbm), dtype=float)

    mode_names = np.full(
        len(received_power_dbm),
        "NO LINK",
        dtype=object,
    )

    for index, power_dbm in enumerate(received_power_dbm):
        for mode in SX1280_MODES:
            required_power_dbm = mode["sensitivity_dbm"] + LINK_MARGIN_DB

            if power_dbm >= required_power_dbm:
                rates_bps[index] = (
                    mode["radio_rate_bps"]
                    * PROTOCOL_EFFICIENCY
                )

                mode_names[index] = mode["mode_name"]
                break

    return rates_bps, mode_names


# ============================================================================
# ADD LINK DATA TO PASS
# ============================================================================

def build_link_timeline(
    pass_df,
    tx_power_dbm,
    sat_gain_dbi,
    ground_gain_dbi,
):
    df = pass_df.copy()

    df["path_loss_db"] = free_space_path_loss_db(
        df["slant_range_km"].to_numpy()
    )

    df["received_power_dbm"] = calculate_received_power_dbm(
        df["path_loss_db"].to_numpy(),
        tx_power_dbm,
        sat_gain_dbi,
        ground_gain_dbi,
    )

    rates_bps, mode_names = choose_fastest_modes(
        df["received_power_dbm"].to_numpy()
    )

    df["useful_rate_bps"] = rates_bps
    df["useful_rate_kbps"] = rates_bps / 1000.0
    df["selected_mode"] = mode_names

    return df