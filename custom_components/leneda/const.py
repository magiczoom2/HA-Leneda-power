"""Constants for the Leneda Power integration."""
DOMAIN = "leneda"
CONF_METERING_POINT = "metering_point"
CONF_ENERGY_ID = "energy_id"
CONF_API_KEY = "api_key"
CONF_OBIS_CODE = "obis_code"
CONF_INITIAL_SETUP_DAYS_TO_FETCH = "days_to_fetch_during_initial_setup"


API_BASE_URL = "https://api.leneda.eu/api"
DEFAULT_OBIS_CODE = "1-1:1.29.0"
DEFAULT_INITIAL_SETUP_DAYS_TO_FETCH = 180
POLLING_INTERVAL_HOURS = 2
API_MAX_DAYS_TO_FETCH = 30  # Fetch data in chunks of 30 days to not hit API limits
API_MIN_DAYS_TO_FETCH = 2 # Minimum days to fetch even if last statistics was recent
