import math

import numpy as np

from config import (
    DOWNLINK_FREQUENCY_MHZ,
    SAT_POINTING_ERROR_DEG,
    SAT_POINTING_LOSS_DB,
    GROUND_TRACKING_ERROR_DEG,
    GROUND_DISH_EFFICIENCY,
    SAT_RF_PATH_LOSS_DB,
    GROUND_RF_PATH_LOSS_DB,
    POLARIZATION_LOSS_DB,
    ATMOSPHERIC_LOSS_DB,
    OTHER_RF_LOSS_DB,
    LINK_MARGIN_DB,
    PROTOCOL_EFFICIENCY,
)


# ============================================================================
# SX1280 MODE TABLE
# ============================================================================

def build_sx1280_modes():
    modes = []

    spreading_factors = [
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
    ]

    lora_raw_rates_kbps = {
        203: [
            31.72,
            19.03,
            11.10,
            6.34,
            3.57,
            1.98,
            1.09,
            0.595,
        ],
        406: [
            63.44,
            38.06,
            22.20,
            12.69,
            7.14,
            3.96,
            2.18,
            1.19,
        ],
        812: [
            126.88,
            76.13,
            44.41,
            25.38,
            14.27,
            7.93,
            4.36,
            2.38,
        ],
        1625: [
            253.91,
            152.34,
            88.87,
            50.78,
            28.56,
            15.87,
            8.73,
            4.76,
        ],
    }

    lora_sensitivities_dbm = {
        203: [
            -109,
            -111,
            -115,
            -118,
            -121,
            -124,
            -127,
            -130,
        ],
        406: [
            -107,
            -110,
            -113,
            -116,
            -119,
            -122,
            -125,
            -128,
        ],
        812: [
            -105,
            -108,
            -112,
            -115,
            -117,
            -120,
            -123,
            -126,
        ],
        1625: [
            -99,
            -103,
            -106,
            -109,
            -111,
            -114,
            -117,
            -120,
        ],
    }

    lora_coding_efficiency = 4.0 / 5.0

    for bandwidth_khz in lora_raw_rates_kbps:
        for index, spreading_factor in enumerate(spreading_factors):
            raw_rate_bps = lora_raw_rates_kbps[bandwidth_khz][index] * 1000.0
            coded_rate_bps = raw_rate_bps * lora_coding_efficiency

            modes.append(
                {
                    "name": f"LoRa SF{spreading_factor} BW{bandwidth_khz}",
                    "modulation": "LoRa",
                    "rate_bps": coded_rate_bps,
                    "sensitivity_dbm": lora_sensitivities_dbm[bandwidth_khz][index],
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
                "name": f"FLRC {rate_mbps:.3f} Mbps",
                "modulation": "FLRC",
                "rate_bps": rate_mbps * 1e6,
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
                "name": f"FSK {rate_mbps:.3f} Mbps",
                "modulation": "FSK",
                "rate_bps": rate_mbps * 1e6,
                "sensitivity_dbm": sensitivity_dbm,
            }
        )

    best = {}

    for mode in modes:
        key = (
            mode["modulation"],
            round(mode["rate_bps"], 3),
        )

        if key not in best or mode["sensitivity_dbm"] < best[key]["sensitivity_dbm"]:
            best[key] = mode

    modes = list(best.values())
    modes.sort(key=lambda mode: mode["rate_bps"])

    return modes


SX1280_MODES = build_sx1280_modes()


# ============================================================================
# FREE-SPACE PATH LOSS
# ============================================================================

def fspl_db(distance_km):
    if distance_km <= 0:
        raise ValueError("Distance must be greater than zero.")

    return (
        32.44
        + 20.0 * math.log10(distance_km)
        + 20.0 * math.log10(DOWNLINK_FREQUENCY_MHZ)
    )


# ============================================================================
# ESTIMATE GROUND DISH BEAMWIDTH
#
# Gain of a parabolic aperture:
#
#     G = efficiency * (pi D / wavelength)^2
#
# Approximate half-power beamwidth:
#
#     HPBW ~= 70 * wavelength / D
#
# Combining these gives beamwidth directly from antenna gain.
# ============================================================================

def estimate_ground_hpbw_deg(ground_gain_dbi):
    gain_linear = 10.0 ** (ground_gain_dbi / 10.0)

    return (
        70.0
        * math.pi
        * math.sqrt(
            GROUND_DISH_EFFICIENCY
            / gain_linear
        )
    )


# ============================================================================
# GROUND POINTING LOSS
#
# Near-boresight approximation:
#
#     L_point ~= 12 * (pointing_error / HPBW)^2
#
# Higher-gain antennas therefore automatically receive a larger penalty
# because their estimated beamwidth is narrower.
# ============================================================================

def ground_pointing_loss_db(ground_gain_dbi):
    hpbw_deg = estimate_ground_hpbw_deg(
        ground_gain_dbi
    )

    return 12.0 * (
        GROUND_TRACKING_ERROR_DEG
        / hpbw_deg
    ) ** 2


# ============================================================================
# TOTAL PHYSICAL LINK LOSSES
# ============================================================================

def physical_link_losses_db(ground_gain_dbi):
    return (
        SAT_POINTING_LOSS_DB
        + ground_pointing_loss_db(ground_gain_dbi)
        + SAT_RF_PATH_LOSS_DB
        + GROUND_RF_PATH_LOSS_DB
        + POLARIZATION_LOSS_DB
        + ATMOSPHERIC_LOSS_DB
        + OTHER_RF_LOSS_DB
    )


# ============================================================================
# RECEIVED POWER
# ============================================================================

def received_power_dbm(
    tx_power_dbm,
    sat_gain_dbi,
    ground_gain_dbi,
    distance_km,
):
    return (
        tx_power_dbm
        + sat_gain_dbi
        + ground_gain_dbi
        - fspl_db(distance_km)
        - physical_link_losses_db(ground_gain_dbi)
    )


# ============================================================================
# SELECT FASTEST SX1280 MODE THAT CLOSES THE LINK
# ============================================================================

def select_mode(received_power_dbm_value):
    selected_mode = None

    for mode in SX1280_MODES:
        required_received_power_dbm = (
            mode["sensitivity_dbm"]
            + LINK_MARGIN_DB
        )

        if received_power_dbm_value >= required_received_power_dbm:
            selected_mode = mode

    return selected_mode


# ============================================================================
# BUILD LINK TIMELINE
# ============================================================================

def build_link_timeline(
    pass_df,
    tx_power_dbm,
    sat_gain_dbi,
    ground_gain_dbi,
):
    link_df = pass_df.copy()

    ground_hpbw_deg = estimate_ground_hpbw_deg(
        ground_gain_dbi
    )

    ground_pointing_loss = ground_pointing_loss_db(
        ground_gain_dbi
    )

    modeled_losses_db = physical_link_losses_db(
        ground_gain_dbi
    )

    path_losses_db = []
    received_powers_dbm = []
    selected_modes = []
    sensitivities_dbm = []
    required_powers_dbm = []
    link_margin_remaining_db = []
    useful_rates_bps = []

    for distance_km in link_df["slant_range_km"]:
        path_loss_db = fspl_db(
            distance_km
        )

        received_dbm = received_power_dbm(
            tx_power_dbm,
            sat_gain_dbi,
            ground_gain_dbi,
            distance_km,
        )

        mode = select_mode(
            received_dbm
        )

        path_losses_db.append(
            path_loss_db
        )

        received_powers_dbm.append(
            received_dbm
        )

        if mode is None:
            selected_modes.append("NO LINK")
            sensitivities_dbm.append(np.nan)
            required_powers_dbm.append(np.nan)
            link_margin_remaining_db.append(np.nan)
            useful_rates_bps.append(0.0)

        else:
            required_received_power_dbm = (
                mode["sensitivity_dbm"]
                + LINK_MARGIN_DB
            )

            remaining_margin_db = (
                received_dbm
                - required_received_power_dbm
            )

            useful_rate_bps = (
                mode["rate_bps"]
                * PROTOCOL_EFFICIENCY
            )

            selected_modes.append(
                mode["name"]
            )

            sensitivities_dbm.append(
                mode["sensitivity_dbm"]
            )

            required_powers_dbm.append(
                required_received_power_dbm
            )

            link_margin_remaining_db.append(
                remaining_margin_db
            )

            useful_rates_bps.append(
                useful_rate_bps
            )

    link_df["tx_power_dbm"] = tx_power_dbm
    link_df["sat_antenna_gain_dbi"] = sat_gain_dbi
    link_df["ground_antenna_gain_dbi"] = ground_gain_dbi

    link_df["sat_pointing_error_deg"] = SAT_POINTING_ERROR_DEG
    link_df["sat_pointing_loss_db"] = SAT_POINTING_LOSS_DB

    link_df["ground_tracking_error_deg"] = GROUND_TRACKING_ERROR_DEG
    link_df["ground_hpbw_deg"] = ground_hpbw_deg
    link_df["ground_pointing_loss_db"] = ground_pointing_loss

    link_df["sat_rf_path_loss_db"] = SAT_RF_PATH_LOSS_DB
    link_df["ground_rf_path_loss_db"] = GROUND_RF_PATH_LOSS_DB
    link_df["polarization_loss_db"] = POLARIZATION_LOSS_DB
    link_df["atmospheric_loss_db"] = ATMOSPHERIC_LOSS_DB
    link_df["other_rf_loss_db"] = OTHER_RF_LOSS_DB

    link_df["total_physical_loss_db"] = modeled_losses_db
    link_df["design_margin_db"] = LINK_MARGIN_DB

    link_df["fspl_db"] = path_losses_db
    link_df["received_power_dbm"] = received_powers_dbm
    link_df["selected_mode"] = selected_modes
    link_df["selected_mode_sensitivity_dbm"] = sensitivities_dbm
    link_df["required_received_power_dbm"] = required_powers_dbm
    link_df["remaining_link_margin_db"] = link_margin_remaining_db

    link_df["useful_rate_bps"] = useful_rates_bps
    link_df["useful_rate_kbps"] = link_df["useful_rate_bps"] / 1000.0

    return link_df