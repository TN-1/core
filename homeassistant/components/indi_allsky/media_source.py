"""INDI Allsky Media Source Implementation."""

from typing import override

from homeassistant.components.media_player import MediaClass, MediaType
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceError,
    MediaSourceItem,
    PlayMedia,
    Unresolvable,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .coordinator import IndiAllSkyConfigEntry


async def async_get_media_source(hass: HomeAssistant) -> IndiAllSkyMediaSource:
    """Set up INDI Allsky media source."""
    return IndiAllSkyMediaSource(hass)


class IndiAllSkyMediaSource(MediaSource):
    """Provide INDI Allsky media items as a media source."""

    name: str = "INDI Allsky"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize IndiAllSkyMediaSource."""
        super().__init__(DOMAIN)
        self.hass = hass

    @override
    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve media item to a URL."""
        entry_id, relative_path = self._parse_identifier(item.identifier)

        if not entry_id or not relative_path:
            raise Unresolvable(
                translation_domain=DOMAIN,
                translation_key="incomplete_media_identifier",
            )

        entry = self._get_config_entry_or_raise(entry_id)
        url = entry.runtime_data.client.get_image_url(relative_path)
        mime_type = (
            "video/mp4"
            if relative_path.endswith((".mp4", ".mkv", ".avi"))
            else "image/jpeg"
        )
        return PlayMedia(url, mime_type)

    @override
    async def async_browse_media(
        self,
        item: MediaSourceItem,
    ) -> BrowseMediaSource:
        """Return media items for browsing."""
        if item.identifier:
            entry_id, relative_path = self._parse_identifier(item.identifier)
            if entry_id and not relative_path:
                entry = self._get_config_entry_or_raise(entry_id)
                return self._build_media_entry_items(entry)

        return self._build_media_configs()

    @callback
    def _parse_identifier(self, identifier: str) -> tuple[str | None, str | None]:
        """Parse entry_id and relative_path from identifier."""
        if "#" in identifier:
            entry_id, relative_path = identifier.split("#", 1)
            return entry_id, relative_path
        return identifier, None

    def _get_config_entry_or_raise(self, entry_id: str) -> IndiAllSkyConfigEntry:
        """Get config entry or raise MediaSourceError."""
        entry = self.hass.config_entries.async_get_entry(entry_id)
        if not entry or entry.state is not ConfigEntryState.LOADED:
            raise MediaSourceError(
                translation_domain=DOMAIN,
                translation_key="config_entry_not_found",
            )
        return entry

    def _build_media_configs(self) -> BrowseMediaSource:
        """Build root media sources for config entries."""
        entries = self.hass.config_entries.async_entries(DOMAIN)
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier="",
            media_class=MediaClass.DIRECTORY,
            media_content_type="",
            title=self.name,
            can_play=False,
            can_expand=True,
            children=[
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=entry.entry_id,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type="",
                    title=entry.title,
                    can_play=False,
                    can_expand=True,
                    children_media_class=MediaClass.IMAGE,
                )
                for entry in entries
            ],
            children_media_class=MediaClass.DIRECTORY,
        )

    def _build_media_entry_items(
        self, entry: IndiAllSkyConfigEntry
    ) -> BrowseMediaSource:
        """Build media items for a specific config entry."""
        children: list[BrowseMediaSource] = [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier=f"{entry.entry_id}#public/latest.jpg",
                media_class=MediaClass.IMAGE,
                media_content_type=MediaType.IMAGE,
                title="Latest Snapshot",
                can_play=False,
                can_expand=False,
            )
        ]

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=entry.entry_id,
            media_class=MediaClass.DIRECTORY,
            media_content_type="",
            title=entry.title,
            can_play=False,
            can_expand=True,
            children=children,
            children_media_class=MediaClass.IMAGE,
        )
