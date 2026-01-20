"""Historical Sensor using aiohttp helper."""
import logging
from datetime import datetime, timedelta, timezone
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components.recorder.statistics import StatisticData, StatisticMetaData

from homeassistant_historical_sensor import HistoricalSensor, HistoricalState, PollUpdateMixin
from .const import API_BASE_URL, CONF_API_KEY, CONF_ENERGY_ID, CONF_METERING_POINT, CONF_OBIS_CODE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([LenedaHistoricalSensor(hass, entry.data)], True)

class LenedaHistoricalSensor(PollUpdateMixin, HistoricalSensor, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Consumption"
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _poll_interval = timedelta(hours=1)

    def __init__(self, hass, config):
        self.hass = hass
        self._config = config
        self._attr_unique_id = f"{config[CONF_METERING_POINT]}_{config[CONF_OBIS_CODE]}"
        self._attr_historical_states = []

    def get_statistic_metadata(self) -> StatisticMetaData:
        meta = super().get_statistic_metadata()
        meta["has_sum"] = True
        return meta

    async def async_update_historical(self):
        session = async_get_clientsession(self.hass)
        end = datetime.now()
        start = end - timedelta(days=7)
        
        url = f"{API_BASE_URL}/metering-points/{self._config[CONF_METERING_POINT]}/time-series/aggregated"
        params = {
            "startDate": start.strftime("%Y-%m-%d"),
            "endDate": end.strftime("%Y-%m-%d"),
            "obisCode": self._config[CONF_OBIS_CODE],
            "aggregationLevel": "Hour",
            "transformationMode": "Accumulation"
        }
        headers = {"X-API-KEY": self._config[CONF_API_KEY], "X-ENERGY-ID": self._config[CONF_ENERGY_ID]}

        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                self._attr_historical_states = [
                    HistoricalState(state=float(i["value"]), timestamp=datetime.fromisoformat(i["startedAt"].replace("Z", "+00:00")).timestamp())
                    for i in data.get("aggregatedTimeSeries", [])
                ]

    async def async_calculate_statistic_data(self, hist_states, *, latest=None) -> list[StatisticData]:
        stats = []
        hist_states.sort(key=lambda x: x.timestamp)
        running_sum = latest["sum"] if latest and latest.get("sum") else 0.0
        
        for state in hist_states:
            running_sum += state.state
            stats.append(StatisticData(start=datetime.fromtimestamp(state.timestamp, tz=timezone.utc), state=state.state, sum=running_sum))
        return stats
    