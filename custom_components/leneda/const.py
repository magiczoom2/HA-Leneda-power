from homeassistant.const import UnitOfPower, UnitOfEnergy, UnitOfVolume, UnitOfReactivePower, UnitOfReactiveEnergy
from homeassistant.components.sensor import SensorDeviceClass

"""Constants for the Leneda integration."""
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

# Home Assistant OBIS Mapping
OBIS_HA_MAP = {
    # --- Standard Electricity (Power) ---
    "1-1:1.29.0": {
        "name": "Active Power Consumption",
        "unit": UnitOfPower.KILO_WATT,
        "service_type": "Consumption",
        "device_class": SensorDeviceClass.POWER,
        "description": "Measured active consumption",
        "aggregated_name": "Active Energy Consumption",
        "aggregation_unit": UnitOfEnergy.KILO_WATT_HOUR,
        "aggregation_device_class": SensorDeviceClass.ENERGY
    },
    "1-1:2.29.0": {
        "name": "Active Power Production",
        "unit": UnitOfPower.KILO_WATT,
        "service_type": "Production",
        "device_class": SensorDeviceClass.POWER,
        "description": "Measured active production",
        "aggregated_name": "Active Energy Production",
        "aggregation_unit": UnitOfEnergy.KILO_WATT_HOUR,
        "aggregation_device_class": SensorDeviceClass.ENERGY
    },
    "1-1:3.29.0": {
        "name": "Reactive Power Consumption",
        "unit": UnitOfReactivePower.KILO_VOLT_AMPERE_REACTIVE,
        "service_type": "Consumption",
        "device_class": SensorDeviceClass.REACTIVE_POWER,
        "aggregated_name": "Reactive Energy Consumption",
        "description": "Measured reactive consumption",
        "aggregation_unit": UnitOfReactiveEnergy.KILO_VOLT_AMPERE_REACTIVE_HOUR,
        "aggregation_device_class": SensorDeviceClass.REACTIVE_ENERGY
    },
    "1-1:4.29.0": {
        "name": "Reactive Power Production",
        "unit": UnitOfReactivePower.KILO_VOLT_AMPERE_REACTIVE,
        "service_type": "Consumption",
        "device_class": SensorDeviceClass.REACTIVE_POWER,
        "description": "Measured reactive production",
        "aggregated_name": "Reactive Energy Production",
        "aggregation_unit": UnitOfReactiveEnergy.KILO_VOLT_AMPERE_REACTIVE_HOUR,
        "aggregation_device_class": SensorDeviceClass.REACTIVE_ENERGY
    },

    # --- Sharing Groups (Consumption) ---
    "1-65:1.29.1": {
        "name": "Shared Power Consumption L1 (AIR)",
        "unit": UnitOfPower.KILO_WATT,
        "service_type": "Consumption",
        "device_class": SensorDeviceClass.POWER,
        "description": "Consumption covered by production of layer 1 sharing Group (AIR)",
        "aggregated_name": "Shared Energy Consumption L1 (AIR)",
        "aggregation_unit": UnitOfEnergy.KILO_WATT_HOUR,
        "aggregation_device_class": SensorDeviceClass.ENERGY
    },
    "1-65:1.29.3": {
        "name": "Shared Power Consumption L2 (ACR/ACF)",
        "unit": UnitOfPower.KILO_WATT,
        "service_type": "Consumption",
        "device_class": SensorDeviceClass.POWER,
        "description": "Consumption covered by production of layer 2 sharing Group (ACR/ACF/AC1)",
        "aggregated_name": "Shared Energy Consumption L2 (ACR/ACF)",
        "aggregation_unit": UnitOfEnergy.KILO_WATT_HOUR,
        "aggregation_device_class": SensorDeviceClass.ENERGY
    },
    "1-65:1.29.2": {
        "name": "Shared Power Consumption L3 (CEL)",
        "unit": UnitOfPower.KILO_WATT,
        "service_type": "Consumption",
        "device_class": SensorDeviceClass.POWER,
        "description": "Consumption covered by production of layer 3 sharing Group (CEL)",
        "aggregated_name": "Shared Energy Consumption L3 (CEL)",
        "aggregation_unit": UnitOfEnergy.KILO_WATT_HOUR,
        "aggregation_device_class": SensorDeviceClass.ENERGY
    },
    "1-65:1.29.4": {
        "name": "Shared Power Consumption L4 (APS/CER)",
        "unit": UnitOfPower.KILO_WATT,
        "service_type": "Consumption",
        "device_class": SensorDeviceClass.POWER,
        "description": "Consumption covered by production of layer 4 sharing Group (APS/CER/CEN)",
        "aggregated_name": "Shared Energy Consumption L4 (APS/CER)",
        "aggregation_unit": UnitOfEnergy.KILO_WATT_HOUR,
        "aggregation_device_class": SensorDeviceClass.ENERGY
    },
    "1-65:1.29.9": {
        "name": "Grid Power Consumption (Remaining)",
        "unit": UnitOfPower.KILO_WATT,
        "service_type": "Consumption",
        "device_class": SensorDeviceClass.POWER,
        "description": "Remaining consumption after sharing invoiced by supplier",
        "aggregated_name": "Grid Energy Consumption (Remaining)",
        "aggregation_unit": UnitOfEnergy.KILO_WATT_HOUR,
        "aggregation_device_class": SensorDeviceClass.ENERGY
    },

    # --- Sharing Groups (Production) ---
    "1-65:2.29.1": {
        "name": "Shared Power Production L1 (AIR)",
        "unit": UnitOfPower.KILO_WATT,
        "service_type": "Production",
        "device_class": SensorDeviceClass.POWER,
        "description": "Production shared within layer 1 sharing Group (AIR)",
        "aggregated_name": "Shared Energy Production L1 (AIR)",
        "aggregation_unit": UnitOfEnergy.KILO_WATT_HOUR,
        "aggregation_device_class": SensorDeviceClass.ENERGY
    },
    "1-65:2.29.3": {
        "name": "Shared Power Production L2 (ACR/ACF)",
        "unit": UnitOfPower.KILO_WATT,
        "service_type": "Production",
        "device_class": SensorDeviceClass.POWER,
        "description": "Production shared within layer 2 sharing Group (ACR/ACF/AC1)",
        "aggregated_name": "Shared Energy Production L2 (ACR/ACF)",
        "aggregation_unit": UnitOfEnergy.KILO_WATT_HOUR,
        "aggregation_device_class": SensorDeviceClass.ENERGY
    },
    "1-65:2.29.2": {
        "name": "Shared Power Production L3 (CEL)",
        "unit": UnitOfPower.KILO_WATT,
        "service_type": "Production",
        "device_class": SensorDeviceClass.POWER,
        "description": "Production shared within layer 3 sharing Group (CEL)",
        "aggregated_name": "Shared Energy Production L3 (CEL)",
        "aggregation_unit": UnitOfEnergy.KILO_WATT_HOUR,
        "aggregation_device_class": SensorDeviceClass.ENERGY
    },
    "1-65:2.29.4": {
        "name": "Shared Power Production L4 (APS/CER)",
        "unit": UnitOfPower.KILO_WATT,
        "service_type": "Production",
        "device_class": SensorDeviceClass.POWER,
        "description": "Production shared within layer 4 sharing Group (APS/CER/CEN)",
        "aggregated_name": "Shared Energy Production L4 (APS/CER)",
        "aggregation_unit": UnitOfEnergy.KILO_WATT_HOUR,
        "aggregation_device_class": SensorDeviceClass.ENERGY
    },
    "1-65:2.29.9": {
        "name": "Grid Power Production (Remaining)",
        "unit": UnitOfPower.KILO_WATT,
        "service_type": "Production",
        "device_class": SensorDeviceClass.POWER,
        "description": "Remaining production after sharing sold to market",
        "aggregated_name": "Grid Energy Production (Remaining)",
        "aggregation_unit": UnitOfEnergy.KILO_WATT_HOUR,
        "aggregation_device_class": SensorDeviceClass.ENERGY
    },

    # --- Gas & Energy ---
    "7-1:99.23.15": {
        "name": "Gas Volume",
        "unit": UnitOfVolume.CUBIC_METERS,
        "service_type": "Consumption",
        "device_class": SensorDeviceClass.GAS,
        "description": "Measured consumed volume",
        "aggregated_name": "Aggregated Gas Volume",
        "aggregation_unit": UnitOfVolume.CUBIC_METERS,
        "aggregation_device_class": SensorDeviceClass.GAS
    },
    "7-1:99.23.17": {
        "name": "Gas Standard Volume",
        "unit": UnitOfVolume.CUBIC_METERS,
        "service_type": "Consumption",
        "device_class": SensorDeviceClass.GAS,
        "description": "Measured consumed standard volume (Nm³)",
        "aggregated_name": "Aggregated Gas Standard Volume",
        "aggregation_unit": UnitOfVolume.CUBIC_METERS,
        "aggregation_device_class": SensorDeviceClass.GAS
    },
    "7-20:99.33.17": {
        "name": "Gas Energy",
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "service_type": "Consumption",
        "device_class": SensorDeviceClass.ENERGY,
        "description": "Measured consumed energy",
        "aggregated_name": "Aggregated Gas Energy",
        "aggregation_unit": UnitOfEnergy.KILO_WATT_HOUR,
        "aggregation_device_class": SensorDeviceClass.ENERGY
    }
}
