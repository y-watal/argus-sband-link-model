from pathlib import Path


# ============================================================================
# PROJECT PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_DIRECTORY = PROJECT_ROOT / "output"
DATA_OUTPUT_DIRECTORY = OUTPUT_DIRECTORY / "data"
PLOTS_OUTPUT_DIRECTORY = OUTPUT_DIRECTORY / "plots"

# Plot generation is the slow part of a run (one PNG per sat-gain x
# ground-gain combination, x4 plot types). Disable while iterating on the
# CSVs; re-enable for a final presentation run
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
# HARDWARE SWEEP
#
# Spacecraft antenna and TX power are currently fixed
# Ground antenna gain is being swept
# ============================================================================

TX_POWER_DBM_OPTIONS = [
    12.5,
    20.0,
    27.0,
    33.0,
]

SAT_ANTENNA_GAIN_DBI_OPTIONS = [
    0.0,
    1.0,
    2.0,
    3.0,
    4.0,
    5.0,
    6.0,
    7.0,
    8.0,
]

GROUND_ANTENNA_GAIN_DBI_OPTIONS = [
    20.0,
    22.0,
    24.0,
    26.0,
    26.5,
    28.0,
    30.0,
    32.0,
    34.0,
    36.0,
]


# ============================================================================
# RF
# ============================================================================

DOWNLINK_FREQUENCY_MHZ = 2425.0


# ============================================================================
# SPACECRAFT POINTING
#
# Target-track: the spacecraft slews to keep boresight on the ground station,
# so the off-nadir angle drops out and only the residual pointing error
# matters
#
# Satellite pointing loss is calculated dynamically from antenna gain,
# mirroring the ground dish treatment below, because a higher-gain satellite
# antenna has a narrower beam and pays a larger penalty for the same
# pointing error
# ============================================================================

SAT_POINTING_ERROR_DEG = 10.0

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
#
# PLACEHOLDER VALUES - confirm with the ADCS team
#
# The bulk of the slew onto the ground station is assumed to happen before
# the pass starts, using the predicted rise time from the propagated orbit,
# so it does not eat into the pass window. What is modeled here is:
#
#   1. A fixed settle time after the pass begins, during which the
#      spacecraft is assumed to still be stabilizing onto the ground
#      station within pointing tolerance
#   2. A maximum sustained slew rate - if the required tracking rate at some
#      point in the pass (see orbit_geometry.estimate_los_angular_rate_deg_s)
#      exceeds this, the ADCS cannot keep boresight on the ground station
#      and that portion of the pass is treated as unusable
# ============================================================================

TARGET_ACQUISITION_TIME_S = 10.0

MAX_TARGET_TRACK_SLEW_RATE_DEG_S = 2.0


# ============================================================================
# GROUND ANTENNA TRACKING
#
# Default az/el tracking accuracy, used unless a caller passes a different
# value into build_link_timeline() - e.g. for a rotator-precision
# sensitivity sweep. A bigger dish does not track for free: its beam
# narrows with gain, so the same tracking error costs it more. There is a
# practical ceiling on useful dish size for a given rotator's precision
#
# Ground pointing loss is calculated dynamically from antenna gain because
# higher-gain dishes have narrower beams
# ============================================================================

GROUND_TRACKING_ERROR_DEG = 1.0

# Preliminary aperture efficiency used to estimate dish beamwidth from gain
GROUND_DISH_EFFICIENCY = 0.60


# ============================================================================
# POINTING LOSS CAP
#
# The near-boresight quadratic approximation (12 * (error/HPBW)^2) used for
# both satellite and ground pointing loss is only valid while the pointing
# error is smaller than the antenna beamwidth. Past that point it diverges
# without bound, which is not physical - a real antenna pattern flattens
# out at a sidelobe/backlobe floor instead. Cap the modeled loss there as a
# placeholder until real antenna patterns are available
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

# Reserve beyond explicitly modeled physical losses
LINK_MARGIN_DB = 6.0

# Preliminary application-throughput derating
PROTOCOL_EFFICIENCY = 0.80


# ============================================================================
# LEGACY TRADE FILTERS
#
# Existing design_trade.py still imports these
# hardware_coverage_summary.csv remains the main output for current sweeps
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