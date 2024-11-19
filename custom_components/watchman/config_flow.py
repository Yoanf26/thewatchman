"ConfigFlow definition for watchman"

import os
from types import MappingProxyType
from typing import Dict
import json
from json.decoder import JSONDecodeError
from homeassistant.config_entries import (
    ConfigFlow,
    OptionsFlow,
    ConfigEntry,
    ConfigFlowResult,
)
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, selector
import voluptuous as vol
import anyio
from .utils import (
    is_service,
    get_columns_width,
    async_get_report_path,
    get_val,
    DebugLogger,
)

from .const import (
    CONFIG_ENTRY_MINOR_VERSION,
    CONFIG_ENTRY_VERSION,
    DOMAIN,
    CONF_IGNORED_FILES,
    CONF_HEADER,
    CONF_REPORT_PATH,
    CONF_IGNORED_ITEMS,
    CONF_SERVICE_NAME,
    CONF_SERVICE_DATA2,
    CONF_INCLUDED_FOLDERS,
    CONF_CHECK_LOVELACE,
    CONF_IGNORED_STATES,
    CONF_CHUNK_SIZE,
    CONF_COLUMNS_WIDTH,
    CONF_STARTUP_DELAY,
    CONF_FRIENDLY_NAMES,
    CONF_SECTION_APPEARANCE_LOCATION,
    CONF_SECTION_NOTIFY_ACTION,
    MONITORED_STATES,
    DEFAULT_OPTIONS,
)


INCLUDED_FOLDERS_SCHEMA = vol.Schema(vol.All(cv.ensure_list, [cv.string]))
IGNORED_ITEMS_SCHEMA = vol.Schema(vol.All(cv.ensure_list, [cv.string]))
IGNORED_STATES_SCHEMA = vol.Schema(MONITORED_STATES)
IGNORED_FILES_SCHEMA = vol.Schema(vol.All(cv.ensure_list, [cv.string]))
COLUMNS_WIDTH_SCHEMA = vol.Schema(vol.All(cv.ensure_list, [cv.positive_int]))

_LOGGER = DebugLogger(__name__)


def _get_data_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_INCLUDED_FOLDERS,
            ): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
            vol.Optional(
                CONF_IGNORED_ITEMS,
            ): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
            vol.Optional(
                CONF_IGNORED_STATES,
            ): cv.multi_select(MONITORED_STATES),
            vol.Optional(
                CONF_IGNORED_FILES,
            ): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
            vol.Required(CONF_SECTION_APPEARANCE_LOCATION): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_FRIENDLY_NAMES,
                        ): cv.boolean,
                        vol.Required(
                            CONF_REPORT_PATH,
                        ): cv.string,
                        vol.Optional(
                            CONF_HEADER,
                        ): cv.string,
                        vol.Required(
                            CONF_COLUMNS_WIDTH,
                        ): cv.string,
                    }
                ),
                {"collapsed": True},
            ),
            vol.Required(CONF_SECTION_NOTIFY_ACTION): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_SERVICE_NAME,
                        ): cv.string,
                        vol.Optional(
                            CONF_SERVICE_DATA2,
                        ): selector.TemplateSelector(),
                        vol.Optional(
                            CONF_CHUNK_SIZE,
                        ): cv.positive_int,
                    }
                ),
                {"collapsed": True},
            ),
            vol.Required(
                CONF_STARTUP_DELAY,
            ): cv.positive_int,
            vol.Optional(
                CONF_CHECK_LOVELACE,
            ): cv.boolean,
        }
    )


async def _async_validate_input(
    hass: HomeAssistant,
    user_input,
) -> tuple[MappingProxyType[str, str], MappingProxyType[str, str]]:
    errors: Dict[str, str] = {}
    placeholders: Dict[str, str] = {}
    # check user supplied folders
    if CONF_INCLUDED_FOLDERS in user_input:
        included_folders_list = [
            x.strip() for x in user_input[CONF_INCLUDED_FOLDERS].split(",") if x.strip()
        ]
        for path in included_folders_list:
            if not await anyio.Path(path).exists():
                errors |= {
                    CONF_INCLUDED_FOLDERS: "{} is not a valid path ".format(path)
                }
                placeholders["path"] = path
                break

    columns_width = get_val(
        user_input, CONF_COLUMNS_WIDTH, CONF_SECTION_APPEARANCE_LOCATION
    )
    if columns_width:
        try:
            columns_width = [int(x) for x in columns_width.split(",") if x.strip()]
            if len(columns_width) != 3:
                raise ValueError()
            columns_width = COLUMNS_WIDTH_SCHEMA(columns_width)
            user_input[CONF_COLUMNS_WIDTH] = get_columns_width(columns_width)
        except (ValueError, vol.Invalid):
            errors[CONF_INCLUDED_FOLDERS] = "invalid_columns_width"
            # errors[CONF_COLUMNS_WIDTH] = "invalid_columns_width"

    report_path = get_val(
        user_input, CONF_REPORT_PATH, CONF_SECTION_APPEARANCE_LOCATION
    )
    if report_path:
        folder, _ = os.path.split(report_path)
        if not await anyio.Path(folder).exists():
            errors[CONF_INCLUDED_FOLDERS] = "invalid_report_path"
        # errors[CONF_INCLUDED_FOLDERS] = "invalid_report_path"

    service_data = get_val(user_input, CONF_SERVICE_DATA2, CONF_SECTION_NOTIFY_ACTION)

    if service_data:
        try:
            result = json.loads(service_data)
            if not isinstance(result, dict):
                errors[CONF_INCLUDED_FOLDERS] = "malformed_json"
                # errors[CONF_SERVICE_DATA2] = "malformed_json"
        except JSONDecodeError:
            errors[CONF_INCLUDED_FOLDERS] = "malformed_json"
            # errors[CONF_SERVICE_DATA2] = "malformed_json"

    service_name = get_val(user_input, CONF_SERVICE_NAME, CONF_SECTION_NOTIFY_ACTION)
    if service_name:
        if not is_service(hass, service_name):
            # workaround until error handling for section is fixed
            errors[CONF_INCLUDED_FOLDERS] = "unknown_service"
            # errors[CONF_SERVICE_NAME] = "unknown_service"
            placeholders["service"] = service_name
    return (
        MappingProxyType[str, str](errors),
        MappingProxyType[str, str](placeholders),
    )


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """
    Config flow used to set up new instance of integration
    """

    VERSION = CONFIG_ENTRY_VERSION
    MINOR_VERSION = CONFIG_ENTRY_MINOR_VERSION

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        _LOGGER.debugf("::async_step_user::")
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        options = DEFAULT_OPTIONS
        options[CONF_SECTION_APPEARANCE_LOCATION][
            CONF_REPORT_PATH
        ] = await async_get_report_path(self.hass, None)
        options[CONF_INCLUDED_FOLDERS] = self.hass.config.path()
        return self.async_create_entry(title="Watchman", data=options)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    """
    Options flow used to change configuration (options) of existing instance of integration
    """

    def __init__(self, config_entry: ConfigEntry) -> None:
        _LOGGER.debugf("::OptionsFlowHandler.__init::")
        self.config_entry = config_entry

    async def async_get_key_in_section(self, data, key, section=None):
        if section:
            if section in data:
                return section[data].get(key, None)
        else:
            return data.get(key, None)
        return None

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        """
        Manage the options form. This method is invoked twice:
        1. To populate form with default values (user_input=None)
        2. To validate values entered by user (user_imput = {user_data})
           If no errors found, it should return creates_entry
        """

        _LOGGER.debugf(
            "::OptionsFlowHandler.async_step_init:: with user input %s", user_input
        )

        if user_input is not None:  # we asked to validate values entered by user
            errors, placeholders = await _async_validate_input(self.hass, user_input)
            if not errors:
                # see met.no code, without next line entry.data of EXISTING entry
                # will not be updated with user input, but entry.options will do
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=user_input
                )
                return self.async_create_entry(title="", data=user_input)
            else:
                # in case of errors in user_input, display them in the form
                # use previous user input as suggested values
                _LOGGER.debugf(
                    "::OptionsFlowHandler.async_step_init:: validation results errors:[%s] placehoders:[%s]",
                    errors,
                    placeholders,
                )
                return self.async_show_form(
                    step_id="init",
                    data_schema=self.add_suggested_values_to_schema(
                        _get_data_schema(),
                        user_input,
                    ),
                    errors=dict(errors),
                    description_placeholders=dict(placeholders),
                )
        # we asked to provide default values for the form
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                _get_data_schema(),
                self.config_entry.data,
            ),
        )
