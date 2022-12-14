import logging
from typing import Dict, List
from spotipy.oauth2 import SpotifyOAuth
from spotipy.client import Spotify

from .. import utils
from ..constants import CONFIG
from ..types.spotipy import MediaTypes
from ..types.singleton import Singleton
from .base.query_service import QueryService

_log = logging.getLogger(__name__)


class SpotifyQueryService(QueryService, Singleton):
    # TODO Lazy initialize
    # TODO Uninitialize after inactivity
    __spotipy: Spotify

    #########################################
    # Constructors
    #########################################
    def __init__(self) -> None:
        # TODO Investigate using SpotifyPKCE for Authorization Code Flow
        # TODO: Need to ensure with auth_manager that higher rate limit is applied (https://spotipy.readthedocs.io/en/2.21.0/#client-credentials-flow)
        # TODO Double check all these properties are needed
        oauth = SpotifyOAuth(
            client_id=CONFIG.SPOTIPY_CLIENT_ID,
            client_secret=CONFIG.SPOTIPY_CLIENT_SECRET,
            redirect_uri=CONFIG.SPOTIPY_REDIRECT_URI,
            scope=CONFIG.SPOTIPY_SCOPE,
            username=CONFIG.SPOTIFY_USERNAME,
            open_browser=True,
        )
        access_token: str = oauth.get_access_token(as_dict=False)
        self.__spotipy = Spotify(auth=access_token)

    #########################################
    # Overrides
    #########################################
    # TODO: Ambitious, but consider creating types for possible returns of super().search()
    def query(self, media: str) -> List[str] | str:
        if utils.is_youtube_link(media):
            raise ValueError()

        if utils.is_spotify_link(media):
            groups = utils.get_spotify_link_identifiers(media)
            media_type = groups[0]
            entity_id = groups[1]
            if media_type == MediaTypes.TRACK.value:
                return self.__get_track(entity_id)
            if media_type == MediaTypes.ALBUM.value:
                return self.__get_album(entity_id)
            return self.__get_playlist(entity_id)

        result: Dict = self.__spotipy.search(media, limit=1)  # type: ignore
        if len(result["tracks"]["items"]) != 0:
            item: Dict = result["tracks"]["items"][0]
            return item["artists"][0]["name"] + " " + item["name"]
        # TODO ???
        return "fail"

    #########################################
    # Private Helper Functions
    #########################################
    def __get_track(self, track_id: str) -> str:
        _log.debug("Loading track {%s}", track_id)
        result: Dict = self.__spotipy.track(track_id)  # type: ignore
        return result["artists"][0]["name"] + " " + result["name"]

    def __get_album(self, album_id: str) -> List[str]:
        _log.debug("Loading album {%s}", album_id)
        results: List[str] = []
        result: Dict = self.__spotipy.album(album_id)  # type: ignore
        artist = result["artists"][0]["name"]
        tracks: List = result["tracks"]["items"]
        for track in tracks:
            results.append(artist + " " + track["name"])
        return results

    def __get_playlist(self, playlist_id: str) -> List[str]:
        _log.debug("Loading playlist {%s}", playlist_id)
        results: List[str] = []
        result: Dict = self.__spotipy.playlist(
            playlist_id,
            fields="tracks",
        )  # type: ignore
        tracks: List = result["tracks"]["items"]
        for track in tracks:
            results.append(
                track["track"]["artists"][0]["name"] + " " + track["track"]["name"]
            )
        return results
