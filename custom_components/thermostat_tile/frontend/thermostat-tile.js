/*
 * Thermostat Tile card, served by the Thermostat Tile integration.
 *
 * Home Assistant's own tile card for a climate entity, with an info line that
 * says what is what: mode, room temperature, preset and target temperature,
 * for example "Heat · 21.8 °C · Eco · target 15.8 °C", and one row of mode
 * buttons that includes Eco: Off | Heat | Eco. Icon, colours and tap actions
 * are the built-in tile's.
 */

const VERSION = "1.0.4";
const CARD_TYPE = "thermostat-tile";
const EDITOR_TYPE = "thermostat-tile-editor";

const TEXT = {
  en: {
    name: "Thermostat Tile",
    description: "Tile for a thermostat showing mode, room temperature, preset and target temperature.",
    target: "target",
    entity: "Thermostat",
    title: "Name",
    show_modes: "Show mode buttons (off, heat, eco, ...)",
    show_current: "Show room temperature",
    show_preset: "Show preset (eco, away, ...)",
    show_target: "Show target temperature",
  },
  nl: {
    name: "Thermostat Tile",
    description: "Tegel voor een thermostaat met modus, kamertemperatuur, voorinstelling en doeltemperatuur.",
    target: "doel",
    entity: "Thermostaat",
    title: "Naam",
    show_modes: "Modusknoppen tonen (uit, verwarmen, eco, ...)",
    show_current: "Kamertemperatuur tonen",
    show_preset: "Voorinstelling tonen (eco, afwezig, ...)",
    show_target: "Doeltemperatuur tonen",
  },
};

const text = (hass, key) => {
  const lang = ((hass && hass.language) || navigator.language || "en").slice(0, 2);
  return (TEXT[lang] || TEXT.en)[key] || TEXT.en[key] || key;
};

// Options of this card; the rest goes to the built-in tile card.
const CARD_KEYS = ["show_modes", "show_current", "show_preset", "show_target", "hvac_modes"];

const MODE_ICONS = {
  off: "mdi:power",
  heat: "mdi:fire",
  cool: "mdi:snowflake",
  heat_cool: "mdi:sun-snowflake-variant",
  auto: "mdi:thermostat-auto",
  dry: "mdi:water-percent",
  fan_only: "mdi:fan",
  eco: "mdi:leaf",
};
// Off first, then the usual order of Home Assistant's mode buttons.
const MODE_ORDER = ["off", "heat", "cool", "heat_cool", "auto", "dry", "fan_only"];
const modeColor = (mode) =>
  mode === "eco"
    ? "var(--green-color, #4caf50)"
    : `var(--state-climate-${mode}-color, var(--state-climate-active-color, var(--primary-color)))`;

// The buttons: the thermostat's modes plus Eco when it has an eco preset.
const modeOptions = (hass, stateObj, config) => {
  const attrs = stateObj.attributes;
  const modes = (config.hvac_modes || attrs.hvac_modes || [])
    .slice()
    .sort((a, b) => (MODE_ORDER.indexOf(a) + 99) % 99 - (MODE_ORDER.indexOf(b) + 99) % 99);
  const options = modes.map((mode) => ({ value: mode, icon: MODE_ICONS[mode] || "mdi:thermostat", label: hass.formatEntityState(stateObj, mode) }));
  if ((attrs.preset_modes || []).includes("eco")) {
    options.push({ value: "eco", icon: MODE_ICONS.eco, label: hass.formatEntityAttributeValue(stateObj, "preset_mode", "eco") });
  }
  return options;
};
const currentMode = (stateObj) => (stateObj.state !== "off" && stateObj.attributes.preset_mode === "eco" ? "eco" : stateObj.state);

// Segmented buttons in the style of Home Assistant's own tile features.
class ThermostatTileModes extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" }).innerHTML = `<style>
      :host { display: flex; align-items: center; }
      .container { position: relative; display: flex; flex: 1; height: var(--feature-height, 42px);
        border-radius: var(--feature-border-radius, 12px); }
      .container::before { content: ""; position: absolute; inset: 0; border-radius: inherit;
        background: var(--disabled-color); opacity: 0.2; }
      button { position: relative; flex: 1; min-width: 0; height: 100%; padding: 0; border: none; background: none;
        border-radius: var(--feature-border-radius, 12px); color: var(--primary-text-color); cursor: pointer;
        display: flex; align-items: center; justify-content: center; -webkit-tap-highlight-color: transparent; }
      button::before { content: ""; position: absolute; inset: 0; border-radius: inherit; background: var(--option-color);
        opacity: 0; transition: opacity 80ms ease-in-out; }
      button:hover::before { opacity: 0.2; }
      button.selected { color: white; }
      button.selected::before { opacity: 1; }
      button:focus-visible { outline: 2px solid var(--option-color); }
      ha-icon { position: relative; display: flex; --mdc-icon-size: 20px; pointer-events: none; }
    </style><div class="container" role="radiogroup"></div>`;
  }

  set options(options) {
    const key = JSON.stringify(options);
    if (key === this._key) return;
    this._key = key;
    const container = this.shadowRoot.querySelector(".container");
    container.innerHTML = "";
    options.forEach((option) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.value = option.value;
      button.title = option.label;
      button.setAttribute("aria-label", option.label);
      button.setAttribute("role", "radio");
      button.style.setProperty("--option-color", modeColor(option.value));
      const icon = document.createElement("ha-icon");
      icon.icon = option.icon;
      icon.setAttribute("icon", option.icon);
      button.appendChild(icon);
      button.addEventListener("click", (ev) => {
        ev.stopPropagation();
        this.dispatchEvent(new CustomEvent("mode-selected", { detail: { value: option.value } }));
      });
      container.appendChild(button);
    });
    this.value = this._value;
  }

  set value(value) {
    this._value = value;
    this.shadowRoot.querySelectorAll("button").forEach((button) => {
      const selected = button.dataset.value === value;
      button.classList.toggle("selected", selected);
      button.setAttribute("aria-checked", String(selected));
    });
  }
}

// The info line, built from Home Assistant's own formatting (language,
// units and number format of the user).
const infoLine = (hass, stateObj, config, ecoButton) => {
  const attrs = stateObj.attributes;
  const attr = (name) => hass.formatEntityAttributeValue(stateObj, name);
  const parts = [hass.formatEntityState(stateObj)];
  if (config.show_current !== false && attrs.current_temperature != null) {
    parts.push(attr("current_temperature"));
  }
  // A green Eco button already says Eco; the line then skips it.
  const presetShown = attrs.preset_mode && attrs.preset_mode !== "none" && !(ecoButton && attrs.preset_mode === "eco");
  if (config.show_preset !== false && presetShown) {
    parts.push(attr("preset_mode"));
  }
  if (config.show_target !== false && stateObj.state !== "off") {
    if (attrs.temperature != null) {
      parts.push(`${text(hass, "target")} ${attr("temperature")}`);
    } else if (attrs.target_temp_low != null && attrs.target_temp_high != null) {
      parts.push(`${text(hass, "target")} ${attr("target_temp_low")} – ${attr("target_temp_high")}`);
    }
  }
  return parts.filter(Boolean).join(" · ");
};

class ThermostatTile extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._tile = undefined;
    this._buildId = 0;
  }

  static getConfigElement() {
    return document.createElement(EDITOR_TYPE);
  }

  static getStubConfig(hass) {
    const entity = Object.keys((hass && hass.states) || {}).find((id) => id.startsWith("climate."));
    return { entity: entity || "climate.thermostat" };
  }

  setConfig(config) {
    if (!config || !config.entity || !String(config.entity).startsWith("climate.")) {
      throw new Error("Choose a climate entity");
    }
    this._config = config;
    const tile = Object.assign({}, config, {
      type: "tile",
      vertical: false,
      hide_state: true,
      features_position: "inline",
      features: [],
    });
    CARD_KEYS.forEach((key) => delete tile[key]);
    this._tileConfig = tile;
    this._build();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._tile) {
      this._tile.hass = hass;
      this._updateInfo();
    }
  }

  get hass() {
    return this._hass;
  }

  set layout(layout) {
    this._layout = layout;
    if (this._tile) this._tile.layout = layout;
  }

  get layout() {
    return this._layout;
  }

  set preview(preview) {
    this._preview = preview;
    if (this._tile) this._tile.preview = preview;
  }

  get preview() {
    return this._preview;
  }

  getCardSize() {
    return this._tile && this._tile.getCardSize ? this._tile.getCardSize() : 1;
  }

  getGridOptions() {
    return this._tile && this._tile.getGridOptions
      ? this._tile.getGridOptions()
      : { columns: 6, rows: 1, min_columns: 6, min_rows: 1 };
  }

  async _build() {
    const buildId = ++this._buildId;
    let tile;
    try {
      const helpers = await window.loadCardHelpers();
      tile = await helpers.createCardElement(this._tileConfig);
    } catch (err) {
      tile = document.createElement("div");
      tile.textContent = `Thermostat Tile: ${err}`;
    }
    if (buildId !== this._buildId) return;
    tile.layout = this._layout;
    tile.preview = this._preview;
    if (this._hass) tile.hass = this._hass;
    tile.addEventListener("ll-rebuild", (ev) => {
      ev.stopPropagation();
      this._build();
    });
    this.shadowRoot.innerHTML = "<style>:host{display:block;height:100%}</style>";
    this.shadowRoot.appendChild(tile);
    this._tile = tile;
    this._updateInfo();
  }

  // The built-in tile shows no state line (hide_state); this card puts its
  // own line in the same place, so it looks and behaves like the tile's.
  async _updateInfo() {
    const tile = this._tile;
    if (!tile || !this._hass || !this._config) return;
    if (tile.updateComplete) await tile.updateComplete;
    const info = tile.shadowRoot && tile.shadowRoot.querySelector("ha-tile-info");
    const stateObj = this._hass.states[this._config.entity];
    if (!info || !stateObj) return;
    // The tile still renders an empty state line; hide it so this one gets the room.
    info.querySelectorAll(':scope > span[slot="secondary"]:not([data-thermostat-tile])').forEach((el) => {
      el.style.display = "none";
    });
    let line = info.querySelector(":scope > span[data-thermostat-tile]");
    if (!line) {
      line = document.createElement("span");
      line.slot = "secondary";
      line.dataset.thermostatTile = "";
      info.appendChild(line);
    }
    const showModes = this._config.show_modes !== false;
    const options = showModes ? modeOptions(this._hass, stateObj, this._config) : [];
    const value = infoLine(this._hass, stateObj, this._config, options.some((o) => o.value === "eco"));
    if (line.textContent !== value) line.textContent = value;

    const container = tile.shadowRoot.querySelector("ha-tile-container");
    if (!container || !showModes) return;
    let modes = container.querySelector(":scope > thermostat-tile-modes");
    if (!modes) {
      modes = document.createElement("thermostat-tile-modes");
      modes.slot = "features-inline";
      modes.addEventListener("mode-selected", (ev) => this._setMode(ev.detail.value));
      container.appendChild(modes);
    }
    // Square buttons, so the info line keeps as much room as possible.
    modes.style.width = `calc(${options.length} * (var(--feature-height, 42px) + 6px))`;
    modes.options = options;
    modes.value = currentMode(stateObj);
  }

  // Off and the other modes end Eco; Eco switches heating on when it was off.
  async _setMode(mode) {
    const hass = this._hass;
    const stateObj = hass.states[this._config.entity];
    if (!stateObj) return;
    const target = { entity_id: this._config.entity };
    const presets = stateObj.attributes.preset_modes || [];
    if (mode === "eco") {
      if (stateObj.state === "off") {
        const on = (stateObj.attributes.hvac_modes || []).find((m) => m !== "off");
        if (on) await hass.callService("climate", "set_hvac_mode", { hvac_mode: on }, target);
      }
      await hass.callService("climate", "set_preset_mode", { preset_mode: "eco" }, target);
      return;
    }
    if (stateObj.state !== mode) {
      await hass.callService("climate", "set_hvac_mode", { hvac_mode: mode }, target);
    }
    if (mode !== "off" && stateObj.attributes.preset_mode === "eco" && presets.includes("none")) {
      await hass.callService("climate", "set_preset_mode", { preset_mode: "none" }, target);
    }
  }
}

class ThermostatTileEditor extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    this._config = config || {};
    this._render();
  }

  _render() {
    if (!this._hass) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (schema) => text(this._hass, schema.name === "name" ? "title" : schema.name);
      this._form.addEventListener("value-changed", (ev) => this._changed(ev));
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.schema = [
      { name: "entity", required: true, selector: { entity: { domain: "climate" } } },
      { name: "name", selector: { text: {} } },
      { name: "show_modes", selector: { boolean: {} } },
      { name: "show_current", selector: { boolean: {} } },
      { name: "show_preset", selector: { boolean: {} } },
      { name: "show_target", selector: { boolean: {} } },
    ];
    const c = this._config;
    this._form.data = {
      entity: c.entity,
      name: c.name,
      show_modes: c.show_modes !== false,
      show_current: c.show_current !== false,
      show_preset: c.show_preset !== false,
      show_target: c.show_target !== false,
    };
  }

  _changed(ev) {
    ev.stopPropagation();
    const value = ev.detail.value;
    const config = Object.assign({}, this._config, { entity: value.entity });
    if (value.name) config.name = value.name;
    else delete config.name;
    ["show_modes", "show_current", "show_preset", "show_target"].forEach((key) => {
      if (value[key] === false) config[key] = false;
      else delete config[key];
    });
    this._config = config;
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
  }
}

const register = () => {
  if (customElements.get(CARD_TYPE)) return;
  customElements.define(CARD_TYPE, ThermostatTile);
  customElements.define(EDITOR_TYPE, ThermostatTileEditor);
  customElements.define("thermostat-tile-modes", ThermostatTileModes);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: CARD_TYPE,
    name: text(undefined, "name"),
    description: text(undefined, "description"),
    preview: true,
    documentationURL: "https://github.com/milamaja/ha-thermostat-tile",
  });
  console.info(
    `%c THERMOSTAT-TILE %c ${VERSION} `,
    "color: white; background: #ff9800; font-weight: 700;",
    "color: #ff9800; background: white; font-weight: 700;"
  );
};

// Home Assistant replaces the browser's custom element registry while it
// starts. A card defined before that lands in the old registry, where
// dashboards cannot find it ("Custom element doesn't exist"). This file can
// load before Home Assistant has started, so register only once Home
// Assistant's own app element is defined, which happens after the swap.
if (customElements.get("home-assistant")) {
  register();
} else {
  customElements.whenDefined("home-assistant").then(register);
}
