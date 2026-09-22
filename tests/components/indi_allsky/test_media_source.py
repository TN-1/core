"""Tests for INDI Allsky media source."""

import pytest

from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSourceError,
    PlayMedia,
    async_browse_media,
    async_resolve_media,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import setup_integration

from tests.common import MockConfigEntry


@pytest.fixture(autouse=True)
async def setup_media_source(hass: HomeAssistant) -> None:
    """Set up media_source component."""
    assert await async_setup_component(hass, "media_source", {})


@pytest.mark.usefixtures("mock_indi_allsky_client")
async def test_browse_media_root(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test browsing root media source."""
    await setup_integration(hass, mock_config_entry)

    media: BrowseMediaSource = await async_browse_media(
        hass, "media-source://indi_allsky"
    )
    assert media.domain == "indi_allsky"
    assert media.identifier == ""
    assert media.title == "INDI Allsky"
    assert len(media.children) == 1
    assert media.children[0].identifier == mock_config_entry.entry_id


@pytest.mark.usefixtures("mock_indi_allsky_client")
async def test_browse_media_entry_items(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test browsing entry level items."""
    await setup_integration(hass, mock_config_entry)

    media: BrowseMediaSource = await async_browse_media(
        hass, f"media-source://indi_allsky/{mock_config_entry.entry_id}"
    )
    assert media.domain == "indi_allsky"
    assert media.identifier == mock_config_entry.entry_id
    assert len(media.children) == 1
    assert media.children[0].title == "Latest Snapshot"


@pytest.mark.usefixtures("mock_indi_allsky_client")
async def test_resolve_media(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test resolving media items."""
    await setup_integration(hass, mock_config_entry)

    play_media: PlayMedia = await async_resolve_media(
        hass,
        f"media-source://indi_allsky/{mock_config_entry.entry_id}#public/latest.jpg",
        None,
    )
    assert play_media.mime_type == "image/jpeg"
    assert "public/latest.jpg" in play_media.url

    play_video: PlayMedia = await async_resolve_media(
        hass,
        f"media-source://indi_allsky/{mock_config_entry.entry_id}#timelapse.mp4",
        None,
    )
    assert play_video.mime_type == "video/mp4"
    assert "timelapse.mp4" in play_video.url


async def test_resolve_media_invalid_entry(
    hass: HomeAssistant,
) -> None:
    """Test resolving media for unknown config entry raises MediaSourceError."""
    with pytest.raises(MediaSourceError):
        await async_resolve_media(
            hass,
            "media-source://indi_allsky/invalid_entry_id#public/latest.jpg",
            None,
        )
