"""The Sony Projector ADCP integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_USE_AUTH, DEFAULT_PASSWORD, DEFAULT_USE_AUTH, DOMAIN
from .protocol import SonyProjectorADCP

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.MEDIA_PLAYER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sony Projector ADCP from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    # Options set via the Configure dialog take precedence over the values
    # captured at initial setup; fall back to data, then to the defaults.
    password = entry.options.get(
        CONF_PASSWORD, entry.data.get(CONF_PASSWORD, DEFAULT_PASSWORD)
    )
    use_auth = entry.options.get(
        CONF_USE_AUTH, entry.data.get(CONF_USE_AUTH, DEFAULT_USE_AUTH)
    )

    projector = SonyProjectorADCP(host, port, password, use_auth)

    # Test connection
    if not await projector.connect():
        _LOGGER.error("Failed to connect to projector at %s:%s", host, port)
        return False

    await projector.disconnect()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = projector

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload the entry when options change so new auth/password are applied.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when its options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        projector = hass.data[DOMAIN].pop(entry.entry_id)
        await projector.disconnect()

    return unload_ok
