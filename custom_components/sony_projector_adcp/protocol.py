"""Sony ADCP Protocol Handler."""
import asyncio
import hashlib
import json
import logging
from typing import Any, Optional

_LOGGER = logging.getLogger(__name__)

NEWLINE = "\r\n"
ENCODING = "ascii"
TIMEOUT = 10


class SonyProjectorADCP:
    """Handle ADCP protocol communication with Sony projector."""

    def __init__(self, host: str, port: int, password: str = "", use_auth: bool = True):
        """Initialize the ADCP connection."""
        self.host = host
        self.port = port
        self.password = password
        self.use_auth = use_auth
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        """Connect to the projector and authenticate if needed."""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=TIMEOUT
            )

            # Read authentication challenge
            auth_response = await self._read_line()

            if auth_response == "NOKEY":
                _LOGGER.debug("Authentication disabled on projector")
                return True

            # Authentication enabled — handle random number
            if self.use_auth and auth_response:
                random_num = auth_response.strip()

                if random_num:
                    # Create hash: SHA256(random_number + password)
                    hash_input = f"{random_num}{self.password}"
                    hash_result = hashlib.sha256(hash_input.encode()).hexdigest()

                    # Send hash
                    await self._write_line(hash_result)

                    # Read authentication result
                    auth_result = await self._read_line()

                    if auth_result != "OK" and auth_result != "ok":
                        _LOGGER.error("Authentication failed: %s", auth_result)
                        await self.disconnect()
                        return False

            _LOGGER.info("Connected to Sony projector at %s:%s", self.host, self.port)
            return True

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout connecting to projector")
            return False
        except Exception as e:
            _LOGGER.error("Error connecting to projector: %s", e)
            return False

    async def disconnect(self):
        """Disconnect from the projector."""
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception as e:
                _LOGGER.debug("Error closing connection: %s", e)
            finally:
                self._writer = None
                self._reader = None

    async def _read_line(self) -> str:
        """Read a line from the projector."""
        if not self._reader:
            raise ConnectionError("Not connected")

        try:
            data = await asyncio.wait_for(
                self._reader.readuntil(NEWLINE.encode(ENCODING)),
                timeout=TIMEOUT
            )
            return data.decode(ENCODING).strip()
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout reading from projector")
            raise
        except Exception as e:
            _LOGGER.error("Error reading from projector: %s", e)
            raise

    async def _write_line(self, data: str):
        """Write a line to the projector."""
        if not self._writer:
            raise ConnectionError("Not connected")

        try:
            self._writer.write(f"{data}{NEWLINE}".encode(ENCODING))
            await self._writer.drain()
        except Exception as e:
            _LOGGER.error("Error writing to projector: %s", e)
            raise

    async def send_command(self, command: str) -> Optional[str]:
        """Send a command and return the response."""
        async with self._lock:
            # Ensure we're connected
            if not self._writer or not self._reader:
                if not await self.connect():
                    return None

            try:
                # Send command
                await self._write_line(command)
                _LOGGER.debug("Sent command: %s", command)

                # Read response
                response = await self._read_line()
                _LOGGER.debug("Received response: %s", response)

                # Check for errors
                if response.startswith("err_"):
                    _LOGGER.error("Command error: %s for command: %s", response, command)
                    return None

                return response

            except Exception as e:
                _LOGGER.error("Error sending command %s: %s", command, e)
                await self.disconnect()
                return None

    # ── Generic helpers ───────────────────────────────────────────────

    async def get_setting(self, command: str) -> Optional[str]:
        """Get a string (menu_sel) setting — returns the unquoted value."""
        response = await self.send_command(f"{command} ?")
        if response and response.startswith('"') and response.endswith('"'):
            return response.strip('"')
        return None

    async def set_setting(self, command: str, value: str) -> bool:
        """Set a string (menu_sel) setting."""
        response = await self.send_command(f'{command} "{value}"')
        return response == "ok"

    async def get_numeric_value(self, parameter: str) -> Optional[int]:
        """Get a numeric parameter value."""
        response = await self.send_command(f"{parameter} ?")
        if not response:
            return None
        # Handle both positive and negative numbers
        stripped = response.lstrip('-')
        if stripped.isdigit():
            return int(response)
        return None

    async def set_numeric_value(self, parameter: str, value: int) -> bool:
        """Set a numeric parameter value."""
        command = f"{parameter} {value}"
        response = await self.send_command(command)
        return response == "ok"

    async def adjust_numeric_value(self, parameter: str, delta: int) -> bool:
        """Adjust a numeric parameter by a relative amount using ADCP --rel."""
        command = f"{parameter} --rel {delta}"
        response = await self.send_command(command)
        return response == "ok"

    async def get_json_status(self, command: str) -> Any:
        """Get a status response that returns JSON (arrays, objects)."""
        response = await self.send_command(f"{command} ?")
        if not response:
            return None
        try:
            return json.loads(response)
        except (json.JSONDecodeError, ValueError):
            _LOGGER.debug("Non-JSON response for %s: %s", command, response)
            return response

    # ── Power ─────────────────────────────────────────────────────────

    async def get_power_status(self) -> Optional[str]:
        """Get the current power status."""
        return await self.get_setting("power_status")

    async def set_power(self, state: bool) -> bool:
        """Set power on or off."""
        return await self.set_setting("power", "on" if state else "off")

    # ── Input / Muting ────────────────────────────────────────────────

    async def get_input(self) -> Optional[str]:
        """Get current input source."""
        return await self.get_setting("input")

    async def set_input(self, source: str) -> bool:
        """Set input source."""
        return await self.set_setting("input", source)

    async def get_blank_status(self) -> Optional[bool]:
        """Get video muting status."""
        value = await self.get_setting("blank")
        if value is not None:
            return value == "on"
        return None

    async def set_blank(self, state: bool) -> bool:
        """Set video muting."""
        return await self.set_setting("blank", "on" if state else "off")

    # ── Picture modes / quality ───────────────────────────────────────

    async def get_picture_mode(self) -> Optional[str]:
        """Get current picture mode."""
        return await self.get_setting("picture_mode")

    async def set_picture_mode(self, mode: str) -> bool:
        """Set picture mode."""
        return await self.set_setting("picture_mode", mode)

    async def get_aspect_ratio(self) -> Optional[str]:
        """Get current aspect ratio."""
        return await self.get_setting("aspect")

    async def set_aspect_ratio(self, mode: str) -> bool:
        """Set aspect ratio."""
        return await self.set_setting("aspect", mode)

    async def get_hdr_mode(self) -> Optional[str]:
        """Get current HDR mode."""
        return await self.get_setting("hdr")

    async def set_hdr_mode(self, mode: str) -> bool:
        """Set HDR mode."""
        return await self.set_setting("hdr", mode)

    async def get_motionflow(self) -> Optional[str]:
        """Get current Motionflow mode."""
        return await self.get_setting("motionflow")

    async def set_motionflow(self, mode: str) -> bool:
        """Set Motionflow mode."""
        return await self.set_setting("motionflow", mode)

    async def get_color_temp(self) -> Optional[str]:
        """Get current color temperature preset."""
        return await self.get_setting("color_temp")

    async def set_color_temp(self, mode: str) -> bool:
        """Set color temperature preset."""
        return await self.set_setting("color_temp", mode)

    async def get_gamma(self) -> Optional[str]:
        """Get current gamma correction."""
        return await self.get_setting("gamma_correction")

    async def set_gamma(self, mode: str) -> bool:
        """Set gamma correction."""
        return await self.set_setting("gamma_correction", mode)

    async def get_color_space(self) -> Optional[str]:
        """Get current color space."""
        return await self.get_setting("color_space")

    async def set_color_space(self, mode: str) -> bool:
        """Set color space."""
        return await self.set_setting("color_space", mode)

    async def get_noise_reduction(self) -> Optional[str]:
        """Get current noise reduction mode."""
        return await self.get_setting("nr")

    async def set_noise_reduction(self, mode: str) -> bool:
        """Set noise reduction mode."""
        return await self.set_setting("nr", mode)

    async def get_film_mode(self) -> Optional[str]:
        """Get current film mode."""
        return await self.get_setting("film_mode")

    async def set_film_mode(self, mode: str) -> bool:
        """Set film mode."""
        return await self.set_setting("film_mode", mode)

    async def get_iris_mode(self) -> Optional[str]:
        """Get current auto iris mode."""
        return await self.get_setting("iris_dyn_cont")

    async def set_iris_mode(self, mode: str) -> bool:
        """Set auto iris mode."""
        return await self.set_setting("iris_dyn_cont", mode)

    async def get_lamp_control(self) -> Optional[str]:
        """Get lamp/laser control mode."""
        return await self.get_setting("lamp_control")

    async def set_lamp_control(self, mode: str) -> bool:
        """Set lamp/laser control mode."""
        return await self.set_setting("lamp_control", mode)

    async def get_light_output_mode(self) -> Optional[str]:
        """Get light source dynamic control mode."""
        return await self.get_setting("light_output_dyn")

    async def set_light_output_mode(self, mode: str) -> bool:
        """Set light source dynamic control mode."""
        return await self.set_setting("light_output_dyn", mode)

    # ── Reality Creation ──────────────────────────────────────────────

    async def get_reality_creation(self) -> Optional[str]:
        """Get Reality Creation status."""
        return await self.get_setting("real_cre")

    async def set_reality_creation(self, state: str) -> bool:
        """Set Reality Creation on/off."""
        return await self.set_setting("real_cre", state)

    # ── Remote keys ───────────────────────────────────────────────────

    async def send_key(self, key: str) -> bool:
        """Send a remote control key command."""
        return await self.set_setting("key", key)

    # ── Diagnostics (read-only) ───────────────────────────────────────

    async def get_timer(self) -> Any:
        """Get operation/light-source timer data (JSON array)."""
        return await self.get_json_status("timer")

    async def get_temperature(self) -> Optional[float]:
        """Get internal temperature."""
        response = await self.send_command("temperature ?")
        if response:
            try:
                return float(response)
            except ValueError:
                return None
        return None

    async def get_error_status(self) -> Any:
        """Get error status (JSON array of error strings)."""
        return await self.get_json_status("error")

    async def get_warning_status(self) -> Any:
        """Get warning status (JSON array of warning strings)."""
        return await self.get_json_status("warning")

    async def get_model_name(self) -> Optional[str]:
        """Get the projector model name."""
        return await self.get_setting("modelname")

    async def get_serial_number(self) -> Optional[str]:
        """Get the projector serial number."""
        return await self.get_setting("serialnum")

    async def get_firmware_version(self) -> Any:
        """Get firmware version info (JSON array)."""
        return await self.get_json_status("version")

    async def get_signal_info(self) -> Optional[str]:
        """Get input signal information."""
        return await self.get_setting("signal")

    async def get_mac_address(self) -> Optional[str]:
        """Get the MAC address."""
        return await self.get_setting("mac_address")

    async def get_filter_status(self) -> Optional[str]:
        """Get filter status (normal/clean/replace)."""
        return await self.get_setting("filter_status")
