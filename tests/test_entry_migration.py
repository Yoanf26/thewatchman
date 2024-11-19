"""Test setup process."""

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from . import from_list

from custom_components.watchman.const import (
    CONF_CHECK_LOVELACE,
    CONF_CHUNK_SIZE,
    CONF_COLUMNS_WIDTH,
    CONF_FRIENDLY_NAMES,
    CONF_HEADER,
    CONF_IGNORED_ITEMS,
    CONF_IGNORED_STATES,
    CONF_INCLUDED_FOLDERS,
    CONF_REPORT_PATH,
    CONF_SECTION_APPEARANCE_LOCATION,
    CONF_SECTION_NOTIFY_ACTION,
    CONF_SERVICE_DATA2,
    CONF_SERVICE_NAME,
    CONF_STARTUP_DELAY,
    DOMAIN,
    CONF_IGNORED_FILES,
)

# configuration for version 1

old_config = {
    CONF_SERVICE_NAME: "notify.dima_telegram",
    CONF_SERVICE_DATA2: '{"aaa":"bbb"}',
    CONF_INCLUDED_FOLDERS: ["/config"],
    CONF_HEADER: "header",
    CONF_REPORT_PATH: "report.txt",
    CONF_IGNORED_STATES: ["missing"],
    CONF_CHUNK_SIZE: 3500,
    CONF_COLUMNS_WIDTH: [33, 7, 66],
    CONF_STARTUP_DELAY: 66,
    CONF_FRIENDLY_NAMES: True,
    CONF_CHECK_LOVELACE: True,
    CONF_IGNORED_ITEMS: ["item1", "item2"],
    CONF_IGNORED_FILES: ["file1", "file2"],
}


async def test_entry_migration(hass):
    """test watchman initialization"""
    # await async_init_integration(hass)

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="WM",
        unique_id="unique_id",
        entry_id="watchman_entry",
        version=1,
        minor_version=1,
        options=old_config,
    )

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert "watchman_data" in hass.data
    assert hass.services.has_service(DOMAIN, "report")

    assert config_entry.data[CONF_INCLUDED_FOLDERS] == from_list(
        old_config[CONF_INCLUDED_FOLDERS]
    )
    assert config_entry.data[CONF_IGNORED_ITEMS] == from_list(
        old_config[CONF_IGNORED_ITEMS]
    )
    assert config_entry.data[CONF_IGNORED_FILES] == from_list(
        old_config[CONF_IGNORED_FILES]
    )

    assert config_entry.data[CONF_STARTUP_DELAY] == old_config[CONF_STARTUP_DELAY]

    assert config_entry.data[CONF_IGNORED_STATES] == old_config[CONF_IGNORED_STATES]
    assert config_entry.data[CONF_CHECK_LOVELACE] == old_config[CONF_CHECK_LOVELACE]
    # === appearance_and_location section ===
    assert config_entry.data[CONF_SECTION_APPEARANCE_LOCATION][CONF_FRIENDLY_NAMES]
    assert (
        config_entry.data[CONF_SECTION_APPEARANCE_LOCATION][CONF_HEADER]
        == old_config[CONF_HEADER]
    )
    assert (
        config_entry.data[CONF_SECTION_APPEARANCE_LOCATION][CONF_REPORT_PATH]
        == old_config[CONF_REPORT_PATH]
    )

    assert config_entry.data[CONF_SECTION_APPEARANCE_LOCATION][
        CONF_COLUMNS_WIDTH
    ] == from_list(old_config[CONF_COLUMNS_WIDTH])

    # === nofity_action section ===
    assert (
        config_entry.data[CONF_SECTION_NOTIFY_ACTION][CONF_SERVICE_NAME]
        == old_config[CONF_SERVICE_NAME]
    )
    assert (
        config_entry.data[CONF_SECTION_NOTIFY_ACTION][CONF_SERVICE_DATA2]
        == old_config[CONF_SERVICE_DATA2]
    )
    assert (
        config_entry.data[CONF_SECTION_NOTIFY_ACTION][CONF_CHUNK_SIZE]
        == old_config[CONF_CHUNK_SIZE]
    )
