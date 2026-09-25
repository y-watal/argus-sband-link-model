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
# REFERENCE IMAGE SIZE
#
# Image size is variable - the primary output is the maximum payload each
# pass can carry (max_payload_possible_mb). This reference size is only used
# to report how long / how much energy it takes to send one image of this
# size, and on how many passes it would fit. It is not a pass/fail
# requirement
# ============================================================================

MESSAGE_SIZE_MB = 2.0
MESSAGE_SIZE_BITS = MESSAGE_SIZE_MB * 1e6 * 8.0


# ============================================================================
# HARDWARE SWEEP
#
# Spacecraft antenna and TX power are set to the selected candidate hardware:
# Southwest Antennas 1055-342 (RHCP patch, space-rated) driven at 27 dBm -
# the only TX power in the earlier broader sweep that landed on a
# realistically sized ground dish (~1.1 m) while staying within the 3 W
# power budget
#
# The 1055-342 is sold as 6.3 dBi, but that is its peak at 2400 MHz. Its
# datasheet gain-vs-frequency plot (measured every 25 MHz) shows 3.6 dBi at
# 2425 MHz and 5.9 dBi at 2450 MHz. Use the measured value at
# DOWNLINK_FREQUENCY_MHZ, not the headline number
#
# Ground antenna gain is still swept to size the dish. Satellite and ground
# pointing error are now swept instead (see below) since the antenna
# hardware itself is fixed
# ============================================================================

TX_POWER_DBM_OPTIONS = [
    27.0,
]

SAT_ANTENNA_GAIN_DBI_OPTIONS = [
    5.9,
]

# Realistic gain at DOWNLINK_FREQUENCY_MHZ for the ground antenna candidates,
# estimated from dish diameter at 60% aperture efficiency (the same
# assumption GROUND_DISH_EFFICIENCY uses for beamwidth), not vendor
# headline numbers:
#
#   24.9  Mimotik MK-2327PA-27DP, 3 ft, dual linear - 25.2 dBi minus ~0.3 dB
#         for the 90 deg hybrid needed to make it circular (rated 27 dBi,
#         likely at the top of its 2.3-2.7 GHz band)
#   27.6  RF HAMDESIGN 1.2 m mesh kit + LHCP feed (vendor ~27.8 dBi scaled)
#   29.5  RF HAMDESIGN 1.5 m mesh kit + LHCP feed (vendor ~29.8 dBi scaled)
GROUND_ANTENNA_GAIN_DBI_OPTIONS = [
    24.9,
    27.6,
    29.5,
]


# ============================================================================
# RF
# ============================================================================

# Placed in the gap between 2.4 GHz Wi-Fi channels 6 (ends ~2448 MHz) and
# 11 (starts ~2451 MHz), where the satellite antenna's measured gain is
# 5.9 dBi. 2425 MHz sat on the antenna's measured gain dip (~3.6 dBi).
# Confirm with a site survey and the experimental license before flight
DOWNLINK_FREQUENCY_MHZ = 2450.0


# ============================================================================
# SPACECRAFT POINTING
# ============================================================================

SAT_POINTING_ERROR_DEG = 10.0

# Swept in the main sweep now that satellite antenna and TX power are fixed
# to the selected hardware, to see how much target-track pointing accuracy
# the ADCS actually needs to deliver
SAT_POINTING_ERROR_DEG_OPTIONS = [
    2.0,
    5.0,
    10.0,
    20.0,
]

# Preliminary pencil-beam approximation relating gain to half-power
# beamwidth for the satellite antenna (patch / horn style, not a parabolic
# aperture like the ground dish):
#
#     G_linear ~= constant / HPBW_deg^2
#
# 41253 deg^2 is the standard approximation for a symmetric pencil beam
# (Balanis). Replace with the actual antenna pattern once one is chosen
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

# Swept in the main sweep alongside satellite pointing error, to see how
# much rotator precision is actually worth investing in
GROUND_TRACKING_ERROR_DEG_OPTIONS = [
    0.25,
    0.5,
    1.0,
    2.0,
]

# Preliminary aperture efficiency used to estimate dish beamwidth from gain
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
# POWER BUDGET
#
# Every predicted pass is evaluated, whatever its peak elevation. A hardware
# combination is valid if it stays within MAX_S_BAND_TX_POWER_W and the link
# closes (delivers some data) on every pass
# ============================================================================

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