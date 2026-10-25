"""Thermostat Tile: a thermostat tile that shows mode, room and target temperature."""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import asyncio
import inspect

from aiohttp import web

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_extract_entity_ids
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from . import actions
from .const import (
    CONF_ECO_TEMPERATURE,
    CONF_EVENING_END,
    CONF_EVENING_HEAT_TEMPERATURE,
    CONF_EVENING_START,
    CONF_HEAT_TEMPERATURE,
    DEFAULT_EVENING_END,
    DEFAULT_EVENING_START,
    DOMAIN,
)

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


def _options(hass: HomeAssistant) -> dict:
    entries = hass.config_entries.async_entries(DOMAIN)
    return dict(entries[0].options) if entries else {}


async def _async_heat_or_eco(hass: HomeAssistant, call: ServiceCall) -> None:
    """The Heat and Eco actions: what the tile's buttons do, for automations too."""
    # Newer Home Assistant versions take only the call, older ones hass first.
    if next(iter(inspect.signature(async_extract_entity_ids).parameters)) == "hass":
        entity_ids = async_extract_entity_ids(hass, call)
    else:
        entity_ids = async_extract_entity_ids(call)
    if inspect.isawaitable(entity_ids):  # a coroutine in some versions
        entity_ids = await entity_ids
    run = actions.heat if call.service == "heat" else actions.eco
    options = _options(hass)
    if call.service == "heat":
        temperature = actions.heat_temperature(
            options.get(CONF_HEAT_TEMPERATURE),
            options.get(CONF_EVENING_HEAT_TEMPERATURE),
            options.get(CONF_EVENING_START) or DEFAULT_EVENING_START,
            options.get(CONF_EVENING_END) or DEFAULT_EVENING_END,
            dt_util.now().time(),
        )
    else:
        temperature = options.get(CONF_ECO_TEMPERATURE)
    for entity_id in sorted(entity_ids):
        state = hass.states.get(entity_id)
        if state is None or not entity_id.startswith("climate."):
            continue

        async def climate(service: str, data: dict, entity_id: str = entity_id) -> None:
            await hass.services.async_call("climate", service, {"entity_id": entity_id, **data}, blocking=True)

        await run((state.state, dict(state.attributes)), climate, asyncio.sleep, temperature)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the card, load it in the frontend, and offer the Heat and Eco actions."""

    async def handle(call: ServiceCall) -> None:
        await _async_heat_or_eco(hass, call)

    for service in ("heat", "eco"):
        hass.services.async_register(DOMAIN, service, handle, schema=cv.make_entity_service_schema({}))
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
