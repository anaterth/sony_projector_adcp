"""Constants for Sony Projector ADCP integration."""

DOMAIN = "sony_projector_adcp"

# Configuration
CONF_HOST = "host"
CONF_PORT = "port"
CONF_PASSWORD = "password"
CONF_USE_AUTH = "use_auth"

# Defaults
DEFAULT_PORT = 53595
DEFAULT_PASSWORD = "Projector"
DEFAULT_USE_AUTH = True
DEFAULT_NAME = "Sony Projector"

# Update intervals
SCAN_INTERVAL = 30  # seconds

# Input sources (ADCP-supported; projector rejects unsupported ones with err_val)
INPUT_SOURCES = {
    "hdmi1": "HDMI 1",
    "hdmi2": "HDMI 2",
}

# Picture modes
PICTURE_MODES = {
    "cinema_film1": "Cinema Film 1",
    "cinema_film2": "Cinema Film 2",
    "reference": "Reference",
    "tv": "TV",
    "photo": "Photo",
    "game": "Game",
    "brt_cinema": "Bright Cinema",
    "brt_tv": "Bright TV",
    "imax": "IMAX Enhanced",
    "user": "User",
    "user1": "User 1",
    "user2": "User 2",
    "user3": "User 3",
    "cinema_digital": "Cinema Digital",
}

# Power states — startup/cooling map to transitional HA states
POWER_STATE_MAP = {
    "standby": "off",
    "startup": "startup",
    "on": "on",
    "cooling1": "cooling",
    "cooling2": "cooling",
}

# Aspect ratios
ASPECT_RATIOS = {
    "normal": "Normal",
    "v_stretch": "V Stretch",
    "squeeze": "Squeeze",
    "1.85_1_zoom": "1.85:1 Zoom",
    "2.35_1_zoom": "2.35:1 Zoom",
    "stretch": "Stretch",
}

# HDR modes
HDR_MODES = {
    "auto": "Auto",
    "on": "On",
    "hdr10": "HDR10",
    "hdr_reference": "HDR Reference",
    "hlg": "HLG",
    "off": "Off",
}

# Motionflow modes
MOTIONFLOW_MODES = {
    "smooth_high": "Smooth High",
    "smooth_low": "Smooth Low",
    "impulse": "Impulse",
    "combination": "Combination",
    "true_cinema": "True Cinema",
    "off": "Off",
}

# Color temperature presets
COLOR_TEMP_MODES = {
    "d93": "D93",
    "d75": "D75",
    "d65": "D65",
    "d55": "D55",
    "dci": "DCI",
    "custom1": "Custom 1",
    "custom2": "Custom 2",
    "custom3": "Custom 3",
    "custom4": "Custom 4",
    "custom5": "Custom 5",
}

# Gamma correction presets
GAMMA_MODES = {
    "1.8": "1.8",
    "2.0": "2.0",
    "2.1": "2.1",
    "2.2": "2.2",
    "2.4": "2.4",
    "2.6": "2.6",
    "gamma7": "Gamma 7",
    "gamma8": "Gamma 8",
    "gamma9": "Gamma 9",
    "gamma10": "Gamma 10",
    "off": "Off",
}

# Color space modes
COLOR_SPACE_MODES = {
    "bt709": "BT.709",
    "bt2020": "BT.2020",
    "adobe_rgb": "Adobe RGB",
    "dci": "DCI",
    "color_space1": "Color Space 1",
    "color_space2": "Color Space 2",
    "color_space3": "Color Space 3",
    "custom": "Custom",
    "custom1": "Custom 1",
    "custom2": "Custom 2",
}

# Noise reduction modes
NOISE_REDUCTION_MODES = {
    "auto": "Auto",
    "high": "High",
    "mid": "Mid",
    "low": "Low",
    "off": "Off",
}

# Film modes
FILM_MODES = {
    "auto": "Auto",
    "off": "Off",
}

# Auto iris modes
IRIS_MODES = {
    "full": "Full",
    "limited": "Limited",
    "off": "Off",
}

# Lamp / laser control
LAMP_CONTROL_MODES = {
    "high": "High",
    "low": "Low",
}

# Light output dynamic control
LIGHT_OUTPUT_DYN_MODES = {
    "full": "Full",
    "limited": "Limited",
    "off": "Off",
}

# Remote key commands (full ADCP set)
KEY_COMMANDS = [
    # Power
    "power_on", "power_off", "power",
    # Navigation
    "menu", "up", "down", "left", "right", "enter", "reset",
    # Input
    "input_a", "input_b", "input_c", "input_d", "input",
    # Video muting
    "blank", "muting",
    # Picture presets
    "picmode1", "picmode2", "picmode3", "picmode4", "picmode5",
    "picmode6", "picmode7", "picmode8", "picmode9", "picmode",
    # Picture adjustments
    "picture +", "picture -",
    "color +", "color -",
    "bright +", "bright -",
    "hue +", "hue -",
    "sharpness +", "sharpness -",
    # Laser brightness
    "laser_brightness +", "laser_brightness -",
    # Toggles
    "color_temp", "color_mode", "black_level",
    "reality_creation", "iris_mode", "motionflow",
    "gamma_correction", "color_correction", "aspect",
    # Lens
    "lens_control", "lens_focus", "lens_focus_far", "lens_focus_near",
    "lens_zoom", "lens_zoom_up", "lens_zoom_down",
    "lens_shift", "lens_shift_up", "lens_shift_down",
    "lens_shift_left", "lens_shift_right",
    "lens_position", "lens_position1", "lens_position2",
    "lens_position3", "lens_position4", "lens_position5",
    # Aspect shortcuts
    "aspect_normal", "aspect_v_stretch",
    "aspect_1.85_1_zoom", "aspect_2.35_1_zoom",
    "aspect_stretch", "aspect_squeeze",
    # Display
    "status_on", "status_off",
    # 3D
    "3d", "2d_3d_display_select",
    "3d_format", "3d_glasses_brightness", "3d_brightness",
]

# Responses
RESPONSE_OK = "ok"
ERROR_PREFIX = "err_"
