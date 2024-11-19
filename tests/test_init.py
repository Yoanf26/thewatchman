"""Test setup process."""

from homeassistant.setup import async_setup_component
from homeassistant.core import HomeAssistant
from . import async_init_integration

from custom_components.watchman.const import (
    CONF_IGNORED_ITEMS,
    CONF_IGNORED_STATES,
    DOMAIN,
    CONF_IGNORED_FILES,
    HASS_DATA_MISSING_ENTITIES,
    HASS_DATA_MISSING_SERVICES,
    HASS_DATA_PARSED_ENTITY_LIST,
    HASS_DATA_PARSED_SERVICE_LIST,
)


async def test_async_setup(hass: HomeAssistant):
    """Test a successful setup component."""
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()


async def test_init(hass):
    """test watchman initialization"""
    await async_init_integration(hass)
    assert "watchman_data" in hass.data
    assert hass.services.has_service(DOMAIN, "report")


async def test_missing(hass):
    """test missing entities detection"""
    hass.states.async_set("sensor.test1_unknown", "unknown")
    hass.states.async_set("sensor.test2_missing", "missing")
    hass.states.async_set("sensor.test3_unavail", "unavailable")
    hass.states.async_set("sensor.test4_avail", "42")
    await async_init_integration(hass)
    assert len(hass.data[DOMAIN][HASS_DATA_MISSING_ENTITIES]) == 3
    assert len(hass.data[DOMAIN][HASS_DATA_MISSING_SERVICES]) == 3


async def test_ignored_state(hass):
    """test single ingnored state processing"""
    hass.states.async_set("sensor.test1_unknown", "unknown")
    hass.states.async_set("sensor.test2_missing", "missing")
    hass.states.async_set("sensor.test3_unavail", "unavailable")
    hass.states.async_set("sensor.test4_avail", "42")
    await async_init_integration(hass, add_params={CONF_IGNORED_STATES: ["unknown"]})
    assert len(hass.data[DOMAIN][HASS_DATA_MISSING_ENTITIES]) == 2
    assert len(hass.data[DOMAIN][HASS_DATA_MISSING_SERVICES]) == 3


async def test_multiple_ignored_states(hass):
    """test multiple ingnored states processing"""
    hass.states.async_set("sensor.test1_unknown", "unknown")
    hass.states.async_set("sensor.test2_missing", "missing")
    hass.states.async_set("sensor.test3_unavail", "unavailable")
    hass.states.async_set("sensor.test4_avail", "42")
    await async_init_integration(
        hass, add_params={CONF_IGNORED_STATES: ["unknown", "missing", "unavailable"]}
    )
    assert len(hass.data[DOMAIN][HASS_DATA_MISSING_ENTITIES]) == 0
    assert len(hass.data[DOMAIN][HASS_DATA_MISSING_SERVICES]) == 0


async def test_ignored_files(hass):
    """test ignored files processing"""
    hass.states.async_set("sensor.test1_unknown", "unknown")
    hass.states.async_set("sensor.test2_missing", "missing")
    hass.states.async_set("sensor.test3_unavail", "unavailable")
    hass.states.async_set("sensor.test4_avail", "42")
    await async_init_integration(
        hass, add_params={CONF_IGNORED_FILES: "*/test_services.yaml"}
    )
    assert len(hass.data[DOMAIN][HASS_DATA_MISSING_ENTITIES]) == 3
    assert len(hass.data[DOMAIN][HASS_DATA_MISSING_SERVICES]) == 0


async def test_ignored_items(hass):
    """test ignored files processing"""
    hass.states.async_set("sensor.test1_unknown", "unknown")
    hass.states.async_set("sensor.test2_missing", "missing")
    hass.states.async_set("sensor.test3_unavail", "unavailable")
    hass.states.async_set("sensor.test4_avail", "42")
    await async_init_integration(
        hass, add_params={CONF_IGNORED_ITEMS: "sensor.test1_*, timer.*"}
    )
    assert len(hass.data[DOMAIN][HASS_DATA_PARSED_ENTITY_LIST]) == 3
    assert len(hass.data[DOMAIN][HASS_DATA_PARSED_SERVICE_LIST]) == 2
    assert len(hass.data[DOMAIN][HASS_DATA_MISSING_ENTITIES]) == 2
    assert len(hass.data[DOMAIN][HASS_DATA_MISSING_SERVICES]) == 2
