from pathlib import Path


# ============================================================================
# PROJECT PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_DIRECTORY = PROJECT_ROOT / "output"
DATA_OUTPUT_DIRECTORY = OUTPUT_DIRECTORY / "data"
PLOTS_OUTPUT_DIRECTORY = OUTPUT_DIRECTORY / "plots"

# Plot generation is the slow part of a run
GENERATE_PLOTS = False

RATE_PLOT_DIRECTORY = PLOTS_OUTPUT_DIRECTORY / "rate_vs_elevation"
ENERGY_PLOT_DIRECTORY = PLOTS_OUTPUT_DIRECTORY / "energy_vs_pass_elevation"
PAYLOAD_PLOT_DIRECTORY = PLOTS_OUTPUT_DIRECTORY / "payload_vs_pass_elevation"
TX_TIME_PLOT_DIRECTORY = PLOTS_OUTPUT_DIRECTORY / "tx_time_vs_pass_elevation"
HARDWARE_TRADE_PLOT_DIRECTORY = PLOTS_OUTPUT_DIRECTORY / "hardware_trade"


# ============================================================================
# GROUND STATION
# ============================================================================

GROUND_STATION_LAT_DEG = 40.442144
GROUND_STATION_LON_DEG = -79.945850
GROUND_STATION_ELEVATION_M = 0.0


# ============================================================================
# REPRESENTATIVE ORBIT
# ============================================================================

TLE_NAME = "TRANSPORTER-17 OBJECT AS / NORAD 69909"

TLE_LINE1 = "1 69909U 26156AS 26255.96938999 .00000649 00000-0 70414-4 0 9994"
TLE_LINE2 = "2 69909 97.7460 155.2608 0003940 282.9568 77.1211 14.91498474 10080"


# ============================================================================
# PASS SEARCH
# ============================================================================

PASS_SEARCH_START_UTC = "2026-09-12T23:15:55+00:00"
PASS_SEARCH_HOURS = 168.0

PASS_HORIZON_DEG = 0.0
PASS_SAMPLE_STEP_S = 1.0


# ============================================================================
# MISSION REQUIREMENT
# ============================================================================

MESSAGE_SIZE_MB = 2.0
MESSAGE_SIZE_BITS = MESSAGE_SIZE_MB * 1e6 * 8.0


# ============================================================================
# SELECTED HARDWARE CONFIGURATION
# ============================================================================

TX_POWER_DBM_OPTIONS = [
    27.0,
]

SAT_ANTENNA_GAIN_DBI_OPTIONS = [
    6.3,
]

GROUND_ANTENNA_GAIN_DBI_OPTIONS = [
    27.0,
]


# ============================================================================
# RF
# ============================================================================

DOWNLINK_FREQUENCY_MHZ = 2425.0


# ============================================================================
# SPACECRAFT POINTING
# ============================================================================

SAT_POINTING_ERROR_DEG = 10.0

SAT_ANTENNA_BEAM_CONSTANT_DEG2 = 41253.0


# ============================================================================
# TARGET-TRACK ACQUISITION AND SLEW LIMIT
# ============================================================================

TARGET_ACQUISITION_TIME_S = 10.0

MAX_TARGET_TRACK_SLEW_RATE_DEG_S = 2.0


# ============================================================================
# GROUND ANTENNA TRACKING
# ============================================================================

GROUND_TRACKING_ERROR_DEG = 1.0

GROUND_DISH_EFFICIENCY = 0.60


# ============================================================================
# POINTING LOSS CAP
# ============================================================================

MAX_POINTING_LOSS_DB = 15.0


# ============================================================================
# OTHER RF LOSSES
# ============================================================================

SAT_RF_PATH_LOSS_DB = 0.5
GROUND_RF_PATH_LOSS_DB = 0.5

POLARIZATION_LOSS_DB = 0.5
ATMOSPHERIC_LOSS_DB = 0.5

OTHER_RF_LOSS_DB = 0.0

LINK_MARGIN_DB = 6.0

PROTOCOL_EFFICIENCY = 0.80


# ============================================================================
# LEGACY TRADE FILTERS
# ============================================================================

DESIGN_MIN_PEAK_ELEVATION_DEG = 30.0
MAX_S_BAND_TX_POWER_W = 3.0


# ============================================================================
# ELECTRICAL POWER MODEL
# ============================================================================

SX1280_MAX_RF_OUTPUT_DBM = 12.5

SX1280_SUPPLY_VOLTAGE_V = 3.3
SX1280_TX_CURRENT_A = 0.024
SX1280_DC_POWER_W = SX1280_SUPPLY_VOLTAGE_V * SX1280_TX_CURRENT_A

PA_EFFICIENCY = 0.35

MAINBOARD_MCU_TX_POWER_W = 0.0
OTHER_TX_ELECTRONICS_POWER_W = 0.0