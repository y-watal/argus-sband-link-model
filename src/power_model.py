from config import (
    SX1280_MAX_RF_OUTPUT_DBM,
    SX1280_DC_POWER_W,
    PA_EFFICIENCY,
    MAINBOARD_MCU_TX_POWER_W,
    OTHER_TX_ELECTRONICS_POWER_W,
)


# ============================================================================
# RF POWER CONVERSION
# ============================================================================

def dbm_to_watts(dbm):
    return 10.0 ** ((dbm - 30.0) / 10.0)


# ============================================================================
# TRANSMITTER ELECTRICAL POWER
# ============================================================================

def transmitter_dc_power_w(tx_power_dbm):
    if tx_power_dbm <= SX1280_MAX_RF_OUTPUT_DBM:
        pa_dc_w = 0.0
        pa_used = False

    else:
        rf_output_w = dbm_to_watts(tx_power_dbm)
        pa_dc_w = rf_output_w / PA_EFFICIENCY
        pa_used = True

    total_dc_w = (
        MAINBOARD_MCU_TX_POWER_W
        + SX1280_DC_POWER_W
        + pa_dc_w
        + OTHER_TX_ELECTRONICS_POWER_W
    )

    return {
        "mainboard_mcu_dc_w": MAINBOARD_MCU_TX_POWER_W,
        "sx1280_dc_w": SX1280_DC_POWER_W,
        "pa_dc_w": pa_dc_w,
        "other_tx_electronics_dc_w": OTHER_TX_ELECTRONICS_POWER_W,
        "total_dc_w": total_dc_w,
        "pa_used": pa_used,
    }


# ============================================================================
# ENERGY FOR A TRANSMISSION DURATION
# ============================================================================

def energy_for_duration(tx_power_dbm, duration_s):
    power = transmitter_dc_power_w(tx_power_dbm)

    energy_j = power["total_dc_w"] * duration_s
    energy_wh = energy_j / 3600.0

    return {
        **power,
        "duration_s": duration_s,
        "energy_j": energy_j,
        "energy_wh": energy_wh,
    }