"""What Heat and Eco do: for the tile's buttons and the Thermostat Tile actions.

No Home Assistant imports, so it can be tested on its own. `state` is the
climate entity's (state, attributes), `call(service, data)` calls a climate
service on that entity and `sleep(seconds)` waits.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

TARGET_TEMPERATURE = 1  # ClimateEntityFeature.TARGET_TEMPERATURE
# Some thermostats (Nest) drop a command that follows another too quickly.
SETTLE_SECONDS = 1.5

Call = Callable[[str, dict[str, Any]], Awaitable[None]]
Sleep = Callable[[float], Awaitable[None]]


def _can_target(attrs: dict[str, Any]) -> bool:
    return bool(int(attrs.get("supported_features") or 0) & TARGET_TEMPERATURE)


async def heat(state: tuple[str, dict[str, Any]], call: Call, sleep: Sleep, temperature: float | None) -> None:
    """Heating on, eco off, and the target up to `temperature` when it is lower."""
    hvac, attrs = state
    changed = False
    if hvac != "heat":
        await call("set_hvac_mode", {"hvac_mode": "heat"})
        changed = True
    if attrs.get("preset_mode") == "eco" and "none" in (attrs.get("preset_modes") or []):
        if changed:
            await sleep(SETTLE_SECONDS)
        await call("set_preset_mode", {"preset_mode": "none"})
        changed = True
    target = attrs.get("temperature")
    reached = isinstance(target, (int, float)) and temperature is not None and target >= temperature
    if temperature is not None and _can_target(attrs) and not reached:
        if changed:
            await sleep(SETTLE_SECONDS)
        await call("set_temperature", {"temperature": temperature})


async def eco(state: tuple[str, dict[str, Any]], call: Call, sleep: Sleep, temperature: float | None) -> None:
    """Heating on when it was off, the target to `temperature`, then the eco preset.

    The target goes first: many thermostats (Nest) take no new target while in eco.
    """
    hvac, attrs = state
    has_eco = "eco" in (attrs.get("preset_modes") or [])
    if hvac != "off" and attrs.get("preset_mode") == "eco":
        return
    changed = False
    if hvac == "off":
        modes = [m for m in attrs.get("hvac_modes") or [] if m != "off"]
        on = "heat" if "heat" in modes else (modes[0] if modes else None)
        if on:
            await call("set_hvac_mode", {"hvac_mode": on})
            changed = True
    if temperature is not None and _can_target(attrs):
        if changed:
            await sleep(SETTLE_SECONDS)
        await call("set_temperature", {"temperature": temperature})
        changed = True
    if has_eco:
        if changed:
            await sleep(SETTLE_SECONDS)
        await call("set_preset_mode", {"preset_mode": "eco"})
