"""Media Player entity for Sony Projector ADCP."""
import logging
from typing import Any, Optional

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback, async_get_current_platform
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from .const import (
    ASPECT_RATIOS,
    COLOR_SPACE_MODES,
    COLOR_TEMP_MODES,
    DEFAULT_NAME,
    DOMAIN,
    FILM_MODES,
    GAMMA_MODES,
    HDR_MODES,
    INPUT_SOURCES,
    IRIS_MODES,
    KEY_COMMANDS,
    LAMP_CONTROL_MODES,
    LIGHT_OUTPUT_DYN_MODES,
    MOTIONFLOW_MODES,
    NOISE_REDUCTION_MODES,
    PICTURE_MODES,
    POWER_STATE_MAP,
)
from .protocol import SonyProjectorADCP

_LOGGER = logging.getLogger(__name__)

# Service name constants
ATTR_KEY = "key"
ATTR_MODE = "mode"
ATTR_VALUE = "value"
ATTR_COMMAND = "command"
ATTR_STATE = "state"
ATTR_PORT = "port"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Sony Projector media player."""
    projector = hass.data[DOMAIN][config_entry.entry_id]
    name = config_entry.data.get(CONF_NAME, DEFAULT_NAME)

    async_add_entities([SonyProjectorMediaPlayer(projector, name, config_entry.entry_id)])

    # Register services
    platform = async_get_current_platform()

    # ── Key command ───────────────────────────────────────────────────
    platform.async_register_entity_service(
        "send_key",
        {vol.Required(ATTR_KEY): vol.In(KEY_COMMANDS)},
        "async_send_key",
    )

    # ── Picture mode ──────────────────────────────────────────────────
    platform.async_register_entity_service(
        "set_picture_mode",
        {vol.Required(ATTR_MODE): vol.In(list(PICTURE_MODES.keys()))},
        "async_set_picture_mode_service",
    )

    # ── Numeric adjustments (absolute) ────────────────────────────────
    for svc, method, min_val, max_val in [
        ("set_brightness", "async_set_brightness", 0, 100),
        ("set_contrast", "async_set_contrast", 0, 100),
        ("set_sharpness", "async_set_sharpness", 0, 100),
        ("set_light_output", "async_set_light_output", 0, 1000),
        ("set_color", "async_set_color", 0, 100),
        ("set_hue", "async_set_hue", 0, 100),
    ]:
        platform.async_register_entity_service(
            svc,
            {vol.Required(ATTR_VALUE): vol.All(vol.Coerce(int), vol.Range(min=min_val, max=max_val))},
            method,
        )

    # ── Numeric adjustments (increment / decrement via ADCP --rel) ────
    for svc, method in [
        ("increase_brightness", "async_increase_brightness"),
        ("decrease_brightness", "async_decrease_brightness"),
        ("increase_contrast", "async_increase_contrast"),
        ("decrease_contrast", "async_decrease_contrast"),
        ("increase_sharpness", "async_increase_sharpness"),
        ("decrease_sharpness", "async_decrease_sharpness"),
        ("increase_light_output", "async_increase_light_output"),
        ("decrease_light_output", "async_decrease_light_output"),
    ]:
        platform.async_register_entity_service(svc, {}, method)

    # ── Selection-based settings ──────────────────────────────────────
    for svc, choices, method in [
        ("set_aspect_ratio", ASPECT_RATIOS, "async_set_aspect_ratio"),
        ("set_hdr_mode", HDR_MODES, "async_set_hdr_mode"),
        ("set_motionflow", MOTIONFLOW_MODES, "async_set_motionflow"),
        ("set_color_temp", COLOR_TEMP_MODES, "async_set_color_temp"),
        ("set_gamma", GAMMA_MODES, "async_set_gamma"),
        ("set_color_space", COLOR_SPACE_MODES, "async_set_color_space"),
        ("set_noise_reduction", NOISE_REDUCTION_MODES, "async_set_noise_reduction"),
        ("set_film_mode", FILM_MODES, "async_set_film_mode"),
        ("set_iris_mode", IRIS_MODES, "async_set_iris_mode"),
        ("set_lamp_control", LAMP_CONTROL_MODES, "async_set_lamp_control"),
        ("set_light_output_mode", LIGHT_OUTPUT_DYN_MODES, "async_set_light_output_mode"),
    ]:
        platform.async_register_entity_service(
            svc,
            {vol.Required(ATTR_MODE): vol.In(list(choices.keys()))},
            method,
        )

    # ── Reality Creation ──────────────────────────────────────────────
    platform.async_register_entity_service(
        "set_reality_creation",
        {vol.Required(ATTR_STATE): vol.In(["on", "off"])},
        "async_set_reality_creation",
    )
    platform.async_register_entity_service(
        "toggle_reality_creation", {}, "async_toggle_reality_creation",
    )

    # ── Raw command ───────────────────────────────────────────────────
    platform.async_register_entity_service(
        "send_raw_command",
        {vol.Required(ATTR_COMMAND): str},
        "async_send_raw_command",
    )


class SonyProjectorMediaPlayer(MediaPlayerEntity):
    """Representation of a Sony Projector as a Media Player."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(
        self, projector: SonyProjectorADCP, name: str, entry_id: str
    ) -> None:
        """Initialize the media player."""
        self._projector = projector
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_media_player"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": name,
            "manufacturer": "Sony",
            "model": "ADCP Projector",
        }
        self._attr_state = MediaPlayerState.OFF
        self._current_source = None
        self._is_blank = False

        # Picture settings
        self._picture_mode = None
        self._brightness = None
        self._contrast = None
        self._sharpness = None
        self._color = None
        self._hue = None
        self._light_output = None
        self._reality_creation = None

        # Display settings
        self._aspect_ratio = None
        self._hdr_mode = None
        self._motionflow = None
        self._color_temp = None
        self._gamma = None
        self._color_space = None
        self._noise_reduction = None
        self._film_mode = None
        self._iris_mode = None
        self._lamp_control = None
        self._light_output_mode = None

        # Diagnostics (queried less aggressively)
        self._model_name = None
        self._serial_number = None
        self._firmware_version = None
        self._signal_info = None
        self._light_source_hours = None
        self._operation_hours = None
        self._temperature = None
        self._error_status = None
        self._warning_status = None
        self._diag_poll_counter = 9  # poll diagnostics on first update

    # ── Update ────────────────────────────────────────────────────────

    async def async_update(self) -> None:
        """Update the state of the projector."""
        try:
            # Get power status
            power_status = await self._projector.get_power_status()
            if power_status:
                mapped = POWER_STATE_MAP.get(power_status)
                if mapped == "on":
                    self._attr_state = MediaPlayerState.ON
                elif mapped == "startup":
                    # Warming up — show as ON so commands are possible
                    self._attr_state = MediaPlayerState.ON
                elif mapped == "cooling":
                    # Cooling down — show as OFF (projector ignores commands)
                    self._attr_state = MediaPlayerState.OFF
                else:
                    self._attr_state = MediaPlayerState.OFF

            # Get additional info if powered on or starting up
            if self._attr_state == MediaPlayerState.ON:
                await self._poll_picture_settings()
                await self._poll_display_settings()

                # Poll diagnostics every 10th cycle (~5 min)
                self._diag_poll_counter += 1
                if self._diag_poll_counter >= 10:
                    self._diag_poll_counter = 0
                    await self._poll_diagnostics()
            else:
                # Powered off — clear transient values
                self._current_source = None
                self._brightness = None
                self._contrast = None
                self._sharpness = None
                self._color = None
                self._hue = None
                self._light_output = None
                self._picture_mode = None
                self._reality_creation = None
                self._aspect_ratio = None
                self._hdr_mode = None
                self._motionflow = None
                self._color_temp = None
                self._gamma = None
                self._color_space = None
                self._noise_reduction = None
                self._film_mode = None
                self._iris_mode = None
                self._lamp_control = None
                self._light_output_mode = None
                self._signal_info = None

        except Exception as e:
            _LOGGER.error("Error updating projector state: %s", e)
            self._attr_available = False
            return

        self._attr_available = True

    def _is_supported(self, adcp_command: str) -> bool:
        """Check if a command is supported by this projector model."""
        return adcp_command not in self._projector.unsupported_commands

    async def _poll_picture_settings(self) -> None:
        """Poll picture-related settings (called every cycle when ON)."""
        for attr, getter, cmd in [
            ("_current_source", self._projector.get_input, "input"),
            ("_is_blank", self._projector.get_blank_status, "blank"),
            ("_picture_mode", self._projector.get_picture_mode, "picture_mode"),
            ("_reality_creation", self._projector.get_reality_creation, "real_cre"),
        ]:
            if not self._is_supported(cmd):
                continue
            try:
                val = await getter()
                if val is not None:
                    setattr(self, attr, val)
            except Exception as e:
                _LOGGER.debug("Error getting %s: %s", attr, e)

        for attr, param in [
            ("_brightness", "brightness"),
            ("_contrast", "contrast"),
            ("_sharpness", "sharpness"),
            ("_light_output", "light_output_val"),
            ("_color", "color"),
            ("_hue", "hue"),
        ]:
            if not self._is_supported(param):
                continue
            try:
                val = await self._projector.get_numeric_value(param)
                if val is not None:
                    setattr(self, attr, val)
            except Exception as e:
                _LOGGER.debug("Error getting %s: %s", param, e)

    async def _poll_display_settings(self) -> None:
        """Poll display / processing settings (called every cycle when ON)."""
        for attr, getter, cmd in [
            ("_aspect_ratio", self._projector.get_aspect_ratio, "aspect"),
            ("_hdr_mode", self._projector.get_hdr_mode, "hdr"),
            ("_motionflow", self._projector.get_motionflow, "motionflow"),
            ("_color_temp", self._projector.get_color_temp, "color_temp"),
            ("_gamma", self._projector.get_gamma, "gamma_correction"),
            ("_color_space", self._projector.get_color_space, "color_space"),
            ("_noise_reduction", self._projector.get_noise_reduction, "nr"),
            ("_film_mode", self._projector.get_film_mode, "film_mode"),
            ("_iris_mode", self._projector.get_iris_mode, "iris_dyn_cont"),
            ("_lamp_control", self._projector.get_lamp_control, "lamp_control"),
            ("_light_output_mode", self._projector.get_light_output_mode, "light_output_dyn"),
        ]:
            if not self._is_supported(cmd):
                continue
            try:
                val = await getter()
                if val is not None:
                    setattr(self, attr, val)
            except Exception as e:
                _LOGGER.debug("Error getting %s: %s", attr, e)

    async def _poll_diagnostics(self) -> None:
        """Poll diagnostics (called every ~5 min when ON)."""
        # Model / serial (only need once)
        if self._model_name is None:
            try:
                name = await self._projector.get_model_name()
                if name:
                    self._model_name = name
                    # Update device info with real model
                    self._attr_device_info = {
                        "identifiers": {(DOMAIN, self._entry_id)},
                        "name": self._attr_device_info.get("name", "Sony Projector"),
                        "manufacturer": "Sony",
                        "model": name,
                    }
            except Exception as e:
                _LOGGER.debug("Error getting model name: %s", e)

        if self._serial_number is None:
            try:
                sn = await self._projector.get_serial_number()
                if sn:
                    self._serial_number = sn
            except Exception as e:
                _LOGGER.debug("Error getting serial number: %s", e)

        if self._firmware_version is None:
            try:
                fw = await self._projector.get_firmware_version()
                if fw:
                    self._firmware_version = fw
            except Exception as e:
                _LOGGER.debug("Error getting firmware version: %s", e)

        # Timer data
        try:
            timer = await self._projector.get_timer()
            if isinstance(timer, list):
                for entry in timer:
                    if isinstance(entry, dict):
                        if "light_src" in entry:
                            self._light_source_hours = entry["light_src"]
                        if "operation" in entry:
                            self._operation_hours = entry["operation"]
        except Exception as e:
            _LOGGER.debug("Error getting timer data: %s", e)

        # Temperature
        try:
            temp = await self._projector.get_temperature()
            if temp is not None:
                self._temperature = temp
        except Exception as e:
            _LOGGER.debug("Error getting temperature: %s", e)

        # Errors / warnings
        try:
            errs = await self._projector.get_error_status()
            if errs:
                self._error_status = errs
        except Exception as e:
            _LOGGER.debug("Error getting error status: %s", e)

        try:
            warns = await self._projector.get_warning_status()
            if warns:
                self._warning_status = warns
        except Exception as e:
            _LOGGER.debug("Error getting warning status: %s", e)

        # Signal info
        try:
            sig = await self._projector.get_signal_info()
            if sig:
                self._signal_info = sig
        except Exception as e:
            _LOGGER.debug("Error getting signal info: %s", e)

    def _require_supported(self, adcp_command: str, feature_name: str) -> None:
        """Raise HomeAssistantError if command is not supported by this model."""
        if adcp_command in self._projector.unsupported_commands:
            model = self._model_name or "this projector"
            raise HomeAssistantError(
                f"{feature_name} is not supported by {model}"
            )

    # ── Core media player controls ────────────────────────────────────

    async def async_turn_on(self) -> None:
        """Turn the projector on."""
        await self._projector.set_power(True)

    async def async_turn_off(self) -> None:
        """Turn the projector off."""
        await self._projector.set_power(False)

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        source_key = None
        for key, name in INPUT_SOURCES.items():
            if name == source:
                source_key = key
                break

        if source_key:
            if await self._projector.set_input(source_key):
                self._current_source = source_key
                self.async_write_ha_state()

    # ── Key command ───────────────────────────────────────────────────

    async def async_send_key(self, key: str) -> None:
        """Send a remote control key command."""
        await self._projector.send_key(key)

    # ── Picture mode ──────────────────────────────────────────────────

    async def async_set_picture_mode_service(self, mode: str) -> None:
        """Set picture mode via service call."""
        if await self._projector.set_picture_mode(mode):
            self._picture_mode = mode
            self.async_write_ha_state()

    # ── Numeric set (absolute) ────────────────────────────────────────

    async def async_set_brightness(self, value: int) -> None:
        """Set brightness."""
        if await self._projector.set_numeric_value("brightness", value):
            self._brightness = value
            self.async_write_ha_state()

    async def async_set_contrast(self, value: int) -> None:
        """Set contrast."""
        if await self._projector.set_numeric_value("contrast", value):
            self._contrast = value
            self.async_write_ha_state()

    async def async_set_sharpness(self, value: int) -> None:
        """Set sharpness."""
        if await self._projector.set_numeric_value("sharpness", value):
            self._sharpness = value
            self.async_write_ha_state()

    async def async_set_light_output(self, value: int) -> None:
        """Set light output level."""
        if await self._projector.set_numeric_value("light_output_val", value):
            self._light_output = value
            self.async_write_ha_state()

    async def async_set_color(self, value: int) -> None:
        """Set color (saturation)."""
        if await self._projector.set_numeric_value("color", value):
            self._color = value
            self.async_write_ha_state()

    async def async_set_hue(self, value: int) -> None:
        """Set hue."""
        if await self._projector.set_numeric_value("hue", value):
            self._hue = value
            self.async_write_ha_state()

    # ── Numeric adjust (relative via ADCP --rel) ──────────────────────

    async def async_increase_brightness(self) -> None:
        """Increase brightness by 1."""
        await self._projector.adjust_numeric_value("brightness", 1)

    async def async_decrease_brightness(self) -> None:
        """Decrease brightness by 1."""
        await self._projector.adjust_numeric_value("brightness", -1)

    async def async_increase_contrast(self) -> None:
        """Increase contrast by 1."""
        await self._projector.adjust_numeric_value("contrast", 1)

    async def async_decrease_contrast(self) -> None:
        """Decrease contrast by 1."""
        await self._projector.adjust_numeric_value("contrast", -1)

    async def async_increase_sharpness(self) -> None:
        """Increase sharpness by 1."""
        await self._projector.adjust_numeric_value("sharpness", 1)

    async def async_decrease_sharpness(self) -> None:
        """Decrease sharpness by 1."""
        await self._projector.adjust_numeric_value("sharpness", -1)

    async def async_increase_light_output(self) -> None:
        """Increase light output by 1."""
        await self._projector.adjust_numeric_value("light_output_val", 1)

    async def async_decrease_light_output(self) -> None:
        """Decrease light output by 1."""
        await self._projector.adjust_numeric_value("light_output_val", -1)

    # ── Selection-based settings ──────────────────────────────────────

    async def async_set_aspect_ratio(self, mode: str) -> None:
        """Set aspect ratio."""
        if await self._projector.set_aspect_ratio(mode):
            self._aspect_ratio = mode
            self.async_write_ha_state()

    async def async_set_hdr_mode(self, mode: str) -> None:
        """Set HDR mode."""
        if await self._projector.set_hdr_mode(mode):
            self._hdr_mode = mode
            self.async_write_ha_state()

    async def async_set_motionflow(self, mode: str) -> None:
        """Set Motionflow mode."""
        if await self._projector.set_motionflow(mode):
            self._motionflow = mode
            self.async_write_ha_state()

    async def async_set_color_temp(self, mode: str) -> None:
        """Set color temperature."""
        if await self._projector.set_color_temp(mode):
            self._color_temp = mode
            self.async_write_ha_state()

    async def async_set_gamma(self, mode: str) -> None:
        """Set gamma correction."""
        if await self._projector.set_gamma(mode):
            self._gamma = mode
            self.async_write_ha_state()

    async def async_set_color_space(self, mode: str) -> None:
        """Set color space."""
        if await self._projector.set_color_space(mode):
            self._color_space = mode
            self.async_write_ha_state()

    async def async_set_noise_reduction(self, mode: str) -> None:
        """Set noise reduction mode."""
        if await self._projector.set_noise_reduction(mode):
            self._noise_reduction = mode
            self.async_write_ha_state()

    async def async_set_film_mode(self, mode: str) -> None:
        """Set film mode."""
        self._require_supported("film_mode", "Film Mode")
        if await self._projector.set_film_mode(mode):
            self._film_mode = mode
            self.async_write_ha_state()

    async def async_set_iris_mode(self, mode: str) -> None:
        """Set auto iris mode."""
        self._require_supported("iris_dyn_cont", "Iris Mode")
        if await self._projector.set_iris_mode(mode):
            self._iris_mode = mode
            self.async_write_ha_state()

    async def async_set_lamp_control(self, mode: str) -> None:
        """Set lamp/laser control mode."""
        self._require_supported("lamp_control", "Lamp Control")
        if await self._projector.set_lamp_control(mode):
            self._lamp_control = mode
            self.async_write_ha_state()

    async def async_set_light_output_mode(self, mode: str) -> None:
        """Set light source dynamic control mode."""
        if await self._projector.set_light_output_mode(mode):
            self._light_output_mode = mode
            self.async_write_ha_state()

    # ── Reality Creation ──────────────────────────────────────────────

    async def async_set_reality_creation(self, state: str) -> None:
        """Set Reality Creation on or off."""
        if await self._projector.set_reality_creation(state):
            self._reality_creation = state
            self.async_write_ha_state()
        else:
            _LOGGER.error("Failed to set reality creation to %s", state)

    async def async_toggle_reality_creation(self) -> None:
        """Toggle Reality Creation on/off."""
        current = self._reality_creation if self._reality_creation else "off"
        new_state = "off" if current == "on" else "on"
        await self.async_set_reality_creation(new_state)

    # ── Raw command ───────────────────────────────────────────────────

    async def async_send_raw_command(self, command: str) -> None:
        """Send a raw ADCP command to the projector."""
        response = await self._projector.send_command(command)
        if response:
            _LOGGER.info("Raw command '%s' returned: %s", command, response)
        else:
            _LOGGER.error("Raw command '%s' failed", command)

    # ── Properties ────────────────────────────────────────────────────

    @property
    def source(self) -> Optional[str]:
        """Return the current input source."""
        if self._current_source:
            return INPUT_SOURCES.get(self._current_source, self._current_source)
        return None

    @property
    def source_list(self) -> list[str]:
        """List of available input sources."""
        return list(INPUT_SOURCES.values())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs: dict[str, Any] = {}

        # Video muting
        attrs["video_muted"] = self._is_blank

        # Picture settings
        if self._picture_mode:
            attrs["picture_mode"] = PICTURE_MODES.get(self._picture_mode, self._picture_mode)
        if self._brightness is not None:
            attrs["brightness"] = self._brightness
        if self._contrast is not None:
            attrs["contrast"] = self._contrast
        if self._sharpness is not None:
            attrs["sharpness"] = self._sharpness
        if self._color is not None:
            attrs["color"] = self._color
        if self._hue is not None:
            attrs["hue"] = self._hue
        if self._light_output is not None:
            attrs["light_output"] = self._light_output
        if self._reality_creation is not None:
            attrs["reality_creation"] = self._reality_creation

        # Display / processing settings
        if self._aspect_ratio:
            attrs["aspect_ratio"] = ASPECT_RATIOS.get(self._aspect_ratio, self._aspect_ratio)
        if self._hdr_mode:
            attrs["hdr_mode"] = HDR_MODES.get(self._hdr_mode, self._hdr_mode)
        if self._motionflow:
            attrs["motionflow"] = MOTIONFLOW_MODES.get(self._motionflow, self._motionflow)
        if self._color_temp:
            attrs["color_temp"] = COLOR_TEMP_MODES.get(self._color_temp, self._color_temp)
        if self._gamma:
            attrs["gamma"] = GAMMA_MODES.get(self._gamma, self._gamma)
        if self._color_space:
            attrs["color_space"] = COLOR_SPACE_MODES.get(self._color_space, self._color_space)
        if self._noise_reduction:
            attrs["noise_reduction"] = NOISE_REDUCTION_MODES.get(self._noise_reduction, self._noise_reduction)
        if self._film_mode:
            attrs["film_mode"] = FILM_MODES.get(self._film_mode, self._film_mode)
        if self._iris_mode:
            attrs["iris_mode"] = IRIS_MODES.get(self._iris_mode, self._iris_mode)
        if self._lamp_control:
            attrs["lamp_control"] = LAMP_CONTROL_MODES.get(self._lamp_control, self._lamp_control)
        if self._light_output_mode:
            attrs["light_output_mode"] = LIGHT_OUTPUT_DYN_MODES.get(self._light_output_mode, self._light_output_mode)

        # Diagnostics
        if self._model_name:
            attrs["model_name"] = self._model_name
        if self._serial_number:
            attrs["serial_number"] = self._serial_number
        if self._firmware_version:
            attrs["firmware_version"] = self._firmware_version
        if self._signal_info:
            attrs["signal_info"] = self._signal_info
        if self._light_source_hours is not None:
            attrs["light_source_hours"] = self._light_source_hours
        if self._operation_hours is not None:
            attrs["operation_hours"] = self._operation_hours
        if self._temperature is not None:
            attrs["temperature"] = self._temperature
        if self._error_status:
            attrs["error_status"] = self._error_status
        if self._warning_status:
            attrs["warning_status"] = self._warning_status

        # Unsupported features (detected via err_cmd from projector)
        if self._projector.unsupported_commands:
            attrs["unsupported_features"] = sorted(self._projector.unsupported_commands)

        return attrs
