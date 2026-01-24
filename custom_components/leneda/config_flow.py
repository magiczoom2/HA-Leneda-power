"""Config flow for Leneda Power."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from .const import (DOMAIN, 
                    CONF_API_KEY, CONF_ENERGY_ID, CONF_METERING_POINT, 
                    CONF_OBIS_CODE, DEFAULT_OBIS_CODE, 
                    CONF_INITIAL_SETUP_DAYS_TO_FETCH, DEFAULT_INITIAL_SETUP_DAYS_TO_FETCH)

class LenedaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_METERING_POINT])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=f"Leneda {user_input[CONF_METERING_POINT]}", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_ENERGY_ID): cv.string,
                vol.Required(CONF_METERING_POINT): cv.string,
                vol.Required(CONF_OBIS_CODE, default=DEFAULT_OBIS_CODE): cv.string,
                vol.Required(CONF_INITIAL_SETUP_DAYS_TO_FETCH, 
                             default=DEFAULT_INITIAL_SETUP_DAYS_TO_FETCH): cv.positive_int,
            })
        )
