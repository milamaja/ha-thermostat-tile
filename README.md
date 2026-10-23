# Thermostat Tile for Home Assistant

A tile for your thermostat that says at a glance what it is doing: the mode,
the room temperature, the preset and the target temperature, for example
**Heat · 21.8 °C · target 15.8 °C**, with one row of buttons to switch
between **Off**, **Heat** and **Eco**.

It is Home Assistant's own tile card, the size of a one-row tile, so it fits
next to your other tiles. Everything is set up in the user interface, no YAML
needed.

<p>
  <img src="https://raw.githubusercontent.com/milamaja/ha-thermostat-tile/main/images/tiles.png" width="540" alt="Three thermostat tiles: heating, eco and off, each with the Off, Heat and Eco buttons">
</p>

## What you get

- A **Thermostat Tile** card in the dashboard card picker, with a visual
  editor.
- An info line under the name: mode, room temperature, preset (when one is
  active) and target temperature. Each part can be switched off.
- Mode buttons in one row: the thermostat's own modes (off, heat, cool, auto,
  ...) plus a green **Eco** button when the thermostat has an eco preset. The
  current mode is highlighted.
  - **Eco** sets the eco preset, and switches the heating on first when the
    thermostat is off.
  - Another mode ends eco (sets the preset back to none) when the thermostat
    supports that.
- No plus and minus buttons: tap the tile for Home Assistant's full thermostat
  dialog when you want to change the temperature.
- Icon, colours and tap actions are the built-in tile's.

## Installation

### HACS (custom repository)

[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=milamaja&repository=ha-thermostat-tile&category=integration)

The button opens this repository in HACS (it uses [My Home Assistant](https://www.home-assistant.io/integrations/my/), which is on by default). Or add it by hand:

1. In HACS, open the menu (three dots, top right) and choose **Custom repositories**.
2. Add `https://github.com/milamaja/ha-thermostat-tile` with category **Integration**.
3. Install **Thermostat Tile** and restart Home Assistant
   (**Settings, System**, power icon top right, **Restart Home Assistant**).

Don't have HACS yet? See [the HACS installation guide](https://hacs.xyz/docs/use/).

### Manual

1. Copy the folder `custom_components/thermostat_tile` into the `custom_components` folder of your Home Assistant configuration directory.
2. Restart Home Assistant.

## Configuration

[![Open your Home Assistant instance and start setting up Thermostat Tile.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=thermostat_tile)

Or go to **Settings, Devices & services, Add integration** and search for
**Thermostat Tile**. There is nothing to fill in: click **Submit** and the
card is available on all your dashboards.

Reload the dashboard once afterwards (on a wall tablet: reload the kiosk app,
or restart it).

## Adding the card

1. Open your dashboard, click the **pencil** (top right) to edit it.
2. Click **Add card** and search for **Thermostat Tile**.
3. Choose your thermostat, and switch parts of the info line or the mode
   buttons off if you like.
4. Click **Save**.

## Options in YAML

Everything is in the visual editor; this is for those who prefer YAML.

```yaml
type: custom:thermostat-tile
entity: climate.living_room
name: Heating          # optional, like the tile card
show_modes: true       # the row of mode buttons
show_current: true     # room temperature
show_preset: true      # the active preset (eco, away, ...)
show_target: true      # target temperature
hvac_modes:            # optional: only these modes as buttons
  - "off"
  - heat
```

Other options of Home Assistant's tile card (icon, color, tap actions, ...)
work as usual.

## License

MIT, see [LICENSE](LICENSE).
