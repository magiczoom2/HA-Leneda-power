import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import UnitOfPower, UnitOfEnergy
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData, StatisticMeanType
from homeassistant.components.recorder.statistics import (
    async_import_statistics,
    get_last_statistics,
    mean
)
from homeassistant.util import slugify, dt as dt_util

from .const import (API_BASE_URL, CONF_API_KEY, CONF_ENERGY_ID,
                    CONF_METERING_POINT, CONF_OBIS_CODE,
                    CONF_INITIAL_SETUP_DAYS_TO_FETCH,
                    API_MAX_DAYS_TO_FETCH, API_MIN_DAYS_TO_FETCH,
                    POLLING_INTERVAL_HOURS)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=POLLING_INTERVAL_HOURS)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Leneda Power and Energy sensors."""
    async_add_entities([
        LenedaPowerSensor(hass, entry.data),
        LenedaEnergySensor(hass, entry.data)
    ], True)

class LenedaBaseSensor(SensorEntity):
    """Common logic for Leneda API sensors."""
    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        self.hass = hass
        self._config = config
        # Unique ID can have dots, but entity_id cannot.
        self._attr_unique_id = f"{config[CONF_METERING_POINT]}_{config[CONF_OBIS_CODE]}_{self.unique_id_suffix}"
        # Use slugify to ensure dots in OBIS codes become underscores in the entity_id
        self.entity_id = f"sensor.{slugify(self._attr_unique_id)}"

    async def get_last_timestamp(self) -> dt_util.dt.datetime | None:
        recorder = get_instance(self.hass)

        last_state_stats = await recorder.async_add_executor_job(
            get_last_statistics, self.hass, 1, self.entity_id, True, {"state"}
        )

        last_time = None
        if last_state_stats and self.entity_id in last_state_stats:
            last_time = last_state_stats[self.entity_id][0]["start"]

        if isinstance(last_time, (int, float)):
            last_time = dt_util.utc_from_timestamp(last_time)

        return last_time

    async def get_days_to_fetch(self) -> int:
        initial_setup_days = self._config[CONF_INITIAL_SETUP_DAYS_TO_FETCH]

        last_timestamp = await self.get_last_timestamp()
        if last_timestamp:
            days_since_last = (dt_util.now(dt_util.UTC) - last_timestamp).days
            days_since_last += 1
            fetch_days = max(days_since_last, API_MIN_DAYS_TO_FETCH)
        else:
            fetch_days = initial_setup_days

        return fetch_days

    async def _fetch_from_api(self, path: str, params: dict[str, Any]) -> dict:
        """Standardized API fetcher."""
        session = async_get_clientsession(self.hass)
        url = f"{API_BASE_URL}/metering-points/{self._config[CONF_METERING_POINT]}/{path}"
        headers = {
            "X-API-KEY": self._config[CONF_API_KEY],
            "X-ENERGY-ID": self._config[CONF_ENERGY_ID]
        }

        try:
            async with session.get(url, params=params, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                _LOGGER.error("Leneda API returned status %s for %s", resp.status, path)
        except Exception as err:
            _LOGGER.error("Error fetching Leneda data from %s: %s", path, err)
        return {}

class LenedaPowerSensor(LenedaBaseSensor):
    """15-minute Power sensor (kW) - Aggregated to Hourly for Statistics."""
    _attr_name = "Power Demand"
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    unique_id_suffix = "pwr_15min"

    async def async_update(self) -> None:
        fetch_days = await self.get_days_to_fetch()
        end_time = dt_util.now(dt_util.UTC)
        start_time = end_time - timedelta(days=fetch_days)

        items = []
        chunk_start = start_time
        while chunk_start < end_time:
            chunk_end = min(chunk_start + timedelta(days=API_MAX_DAYS_TO_FETCH), end_time)
            params = {
                "startDateTime": chunk_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "endDateTime": chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "obisCode": self._config[CONF_OBIS_CODE],
            }
            data = await self._fetch_from_api("time-series", params)
            chunk_start = chunk_end
            chunk_items = data.get("items", [])
            if chunk_items:
                items.extend(chunk_items)

        _LOGGER.info(f"Leneda Power Sensor fetched {len(items)} items")

        if not items:
            return

        # Group 15-min items by Hour (Required by HA Statistics)
        hourly_data: dict[dt_util.dt.datetime, list[float]] = {}
        for ii in items:
            dt = dt_util.parse_datetime(ii["startedAt"])
            if dt is None: 
                continue # Skip invalid dates

            hour_ts = dt.replace(minute=0, second=0, microsecond=0)
            if hour_ts not in hourly_data: 
                hourly_data[hour_ts] = []
            hourly_data[hour_ts].append(float(ii["value"]))

        stats = [
            StatisticData(
                start=ts,
                state=mean(vals), mean=mean(vals),
                min=min(vals), max=max(vals)
            ) for ts, vals in hourly_data.items()
        ]

        metadata = StatisticMetaData(
            mean_type=StatisticMeanType.ARITHMETIC, has_sum=False, name=self._attr_name,
            source="recorder", statistic_id=self.entity_id,
            unit_of_measurement=self._attr_native_unit_of_measurement,
            unit_class="power"
        )
        async_import_statistics(self.hass, metadata, stats)

class LenedaEnergySensor(LenedaBaseSensor):
    """Hourly Aggregated Energy sensor (kWh)."""
    _attr_name = "Energy Consumption"
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    unique_id_suffix = "energy_hourly"

    async def async_update(self) -> None:
        """Fetch hourly aggregated data and import energy statistics."""
        fetch_days = await self.get_days_to_fetch()
        end_time = dt_util.now(dt_util.UTC)
        start_time = end_time - timedelta(days=fetch_days)

        items = []
        chunk_start = start_time
        while chunk_start < end_time:
            chunk_end = min(chunk_start + timedelta(days=API_MAX_DAYS_TO_FETCH), end_time)
            params = {
                "aggregationLevel": "Hour",
                "startDate": chunk_start.strftime("%Y-%m-%d"),
                "endDate": chunk_end.strftime("%Y-%m-%d"),
                "obisCode": self._config[CONF_OBIS_CODE],
                "transformationMode": "Accumulation",
            }
            data = await self._fetch_from_api("time-series/aggregated", params)
            chunk_start = chunk_end
            chunk_items = data.get("aggregatedTimeSeries", [])
            if chunk_items:
                items.extend(chunk_items)

        _LOGGER.info(f"Leneda Power Sensor fetched {len(items)} items")

        if not items:
            return

        # 1. Update live sensor state
        # self._attr_native_value = float(items[-1]["value"])

        # 2. Prepare Statistics
        metadata = StatisticMetaData(
            mean_type=StatisticMeanType.NONE, has_sum=True, name=self._attr_name,
            source="recorder", statistic_id=self.entity_id,
            unit_of_measurement=self._attr_native_unit_of_measurement,
            unit_class="energy"
        )

        # 3. Handle Cumulative Sum (Vital for Energy Dashboard)
        # We fetch the last sum from the DB so we can continue the sequence

        recorder = get_instance(self.hass)

        # --- 1. Get last SUM ---
        last_sum_stats = await recorder.async_add_executor_job(
            get_last_statistics, self.hass, 1, self.entity_id, True, {"sum"}
        )

        running_sum = 0.0
        if last_sum_stats and self.entity_id in last_sum_stats:
            running_sum = last_sum_stats[self.entity_id][0].get("sum") or 0.0

        # --- 2. Get last TIMESTAMP ---
        last_time = await self.get_last_timestamp()

        # --- 3. Build new statistics ---
        stat_data = []

        for item in items:
            item_time = dt_util.parse_datetime(item["startedAt"])
            if item_time is None:
                continue

            # Prevent double-counting
            if last_time and item_time <= last_time:
                continue

            val = float(item["value"])
            running_sum += val

            stat_data.append(
                StatisticData(
                    start=item_time,
                    state=val,
                    sum=running_sum
                )
            )

        if stat_data:
            async_import_statistics(self.hass, metadata, stat_data)
