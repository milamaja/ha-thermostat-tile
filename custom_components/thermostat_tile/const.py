"""Constants for Thermostat Tile."""

DOMAIN = "thermostat_tile"
NAME = "Thermostat Tile"

# Settings (options of the config entry): the target temperature the Heat and
# Eco buttons set. Empty means the button leaves the target as it is.
CONF_HEAT_TEMPERATURE = "heat_temperature"
CONF_ECO_TEMPERATURE = "eco_temperature"

# Optional evening Heat temperature, used between the evening start and end
# (the end may be after midnight). Empty means Heat always uses the one above.
CONF_EVENING_HEAT_TEMPERATURE = "evening_heat_temperature"
CONF_EVENING_START = "evening_start"
CONF_EVENING_END = "evening_end"
DEFAULT_EVENING_START = "18:00:00"
DEFAULT_EVENING_END = "00:30:00"
