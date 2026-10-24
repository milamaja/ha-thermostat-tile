"""Thermostat Tile: a thermostat tile that shows mode, room and target temperature."""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from aiohttp import web
import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import CONF_ECO_TEMPERATURE, CONF_HEAT_TEMPERATURE, DOMAIN

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

CARD_URL = f"/{DOMAIN}/thermostat-tile.js"
CARD_FILE = Path(__file__).parent / "frontend" / "thermostat-tile.js"

_LOGGER = logging.getLogger(__name__)


class ThermostatTileView(HomeAssistantView):
    """Serve the dashboard card without long-lived browser caching."""

    url = CARD_URL
    name = f"{DOMAIN}:card"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def get(self, request: web.Request) -> web.Response:
        body = await self._hass.async_add_executor_job(CARD_FILE.read_bytes)
        return web.Response(
            body=body,
            content_type="text/javascript",
            headers={"Cache-Control": "no-cache"},
        )


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/settings"})
@callback
def ws_settings(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """The temperatures the card's Heat and Eco buttons set (None: leave the target)."""
    entries = hass.config_entries.async_entries(DOMAIN)
    options = entries[0].options if entries else {}
    connection.send_result(
        msg["id"],
        {
            CONF_HEAT_TEMPERATURE: options.get(CONF_HEAT_TEMPERATURE),
            CONF_ECO_TEMPERATURE: options.get(CONF_ECO_TEMPERATURE),
        },
    )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the card and load it in the frontend."""
    websocket_api.async_register_command(hass, ws_settings)
    body = await hass.async_add_executor_job(CARD_FILE.read_bytes)
    # A new version gets a new URL, so browsers never run a stale copy.
    digest = hashlib.sha1(body).hexdigest()[:10]
    url = f"{CARD_URL}?v={digest}"
    hass.http.register_view(ThermostatTileView(hass))
    # Loaded by the start page in up-to-date browsers. The dashboard resource
    # (added per entry below) covers clients holding a cached start page, such
    # as the companion apps and kiosk apps.
    add_extra_js_url(hass, url)
    hass.data[DOMAIN] = url
    return True


def _storage_resources(hass: HomeAssistant):
    """The dashboard resource collection, or None in YAML resource mode."""
    data = hass.data.get(LOVELACE_DATA)
    # resource_mode exists since Home Assistant 2026.x; older versions use mode.
    mode = getattr(data, "resource_mode", getattr(data, "mode", None)) if data else None
    if data is None or mode != "storage":
        return None
    return data.resources


async def _async_ensure_resource(hass: HomeAssistant, url: str) -> None:
    resources = _storage_resources(hass)
    if resources is None:
        _LOGGER.debug("Dashboard resources are in YAML mode; add %s yourself", url)
        return
    try:
        await resources.async_get_info()  # loads the collection
        for item in resources.async_items():
            if item.get("url", "").split("?")[0] == CARD_URL:
                if item["url"] != url:
                    await resources.async_update_item(
                        item["id"], {"res_type": "module", "url": url}
                    )
                return
        await resources.async_create_item({"res_type": "module", "url": url})
    except Exception as err:  # noqa: BLE001 - the card still loads via the start page
        _LOGGER.warning("Could not register the Thermostat Tile as a dashboard resource: %s", err)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Add the card to the dashboard resources (again, after a removal)."""
    await _async_ensure_resource(hass, hass.data[DOMAIN])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the entry."""
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove the dashboard resource when the integration is deleted."""
    resources = _storage_resources(hass)
    if resources is None:
        return
    try:
        await resources.async_get_info()
        for item in resources.async_items():
            if item.get("url", "").split("?")[0] == CARD_URL:
                await resources.async_delete_item(item["id"])
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not remove the Thermostat Tile dashboard resource: %s", err)
