"""Historical Power Sensor (kW) - Fixed with hourly aggregation for HA Statistics."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfPower
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components.recorder.statistics import StatisticData, StatisticMetaData

from homeassistant_historical_sensor import (
    HistoricalSensor, 
    HistoricalState, 
    PollUpdateMixin
)
from .const import API_BASE_URL, CONF_API_KEY, CONF_ENERGY_ID, CONF_METERING_POINT, CONF_OBIS_CODE, DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    async_add_entities([LenedaHistoricalPowerSensor(hass, entry.data)], True)

class LenedaHistoricalPowerSensor(PollUpdateMixin, HistoricalSensor, SensorEntity):
    """Leneda sensor using high-resolution data aggregated to hourly statistics."""

    _attr_has_entity_name = True
    _attr_name = "Power Demand"
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_device_class = SensorDeviceClass.POWER
    _poll_interval = timedelta(minutes=15)

    def __init__(self, hass, config):
        """Initialize."""
        self.hass = hass
        self._config = config
        self._attr_unique_id = f"{config[CONF_METERING_POINT]}_{config[CONF_OBIS_CODE]}_pwr_hourly"
        self._attr_historical_states = []

    def get_statistic_metadata(self) -> StatisticMetaData:
        """Metadata for Power statistics."""
        meta = super().get_statistic_metadata()
        meta["has_mean"] = True
        meta["has_sum"] = False
        return meta

    async def async_update_historical(self) -> None:
        """Fetch high-resolution data (15-min)."""
        session = async_get_clientsession(self.hass)
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=14)
        
        url = f"{API_BASE_URL}/metering-points/{self._config[CONF_METERING_POINT]}/time-series"
        params = {
            "startDateTime": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endDateTime": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "obisCode": self._config[CONF_OBIS_CODE],
        }
        headers = {"X-API-KEY": self._config[CONF_API_KEY], "X-ENERGY-ID": self._config[CONF_ENERGY_ID]}

        try:
            async with session.get(url, params=params, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    ts_data = data.get("items", [])
                    states = []

                    if not ts_data or len(ts_data) == 0:
                        _LOGGER.warning("No data points returned from Leneda.")

                    for item in ts_data:
                        ts_str = item["startedAt"].replace("Z", "+00:00")
                        dt = datetime.fromisoformat(ts_str)
                        states.append(HistoricalState(state=float(item["value"]), timestamp=dt.timestamp()))
                    
                    self._attr_historical_states = states
                    _LOGGER.info("Fetched %s 15-minute points from Leneda", len(states))
        except Exception as err:
            _LOGGER.error("Failed to fetch data: %s", err)

    async def async_calculate_statistic_data(
        self, 
        hist_states: list[HistoricalState], 
        *, 
        latest: dict[str, Any] | None = None
    ) -> list[StatisticData]:
        """Group 15-min points into hourly averages to satisfy Home Assistant."""

        # Sort chronologically for the Recorder
        sorted_states = sorted(hist_states, key=lambda x: x.timestamp)

        hourly_buckets = {}
        for state in sorted_states:
            # Round the timestamp down to the top of the hour
            dt = datetime.fromtimestamp(state.timestamp, tz=timezone.utc)
            hour_start = dt.replace(minute=0, second=0, microsecond=0)
            
            if hour_start not in hourly_buckets:
                hourly_buckets[hour_start] = []
            hourly_buckets[hour_start].append(state.state)

        stats = []
        for start_time, values in hourly_buckets.items():
            # Calculate the average power (mean) for that specific hour
            stats.append(
                StatisticData(
                    start=start_time,
                    mean=sum(values) / len(values)
                )
            )

        return stats
