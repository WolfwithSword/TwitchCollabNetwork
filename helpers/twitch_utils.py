import logging
import re

from twitchAPI.helper import first
from twitchAPI.object.api import TwitchUser, Video
from twitchAPI.twitch import Twitch
from twitchAPI.type import SortMethod, VideoType

from data.streamer_connection import StreamerConnection
from helpers.config import TCNConfig


class TwitchUtils:

    def __init__(self, config: TCNConfig, twitch: Twitch):
        self.logger = logging.getLogger(__name__)
        self.config: TCNConfig = config
        self.twitch: Twitch = twitch
        self.blacklisted_channelnames = self.config.blacklisted_channelnames

    async def init_primary_user(self, username: str, users: dict):
        primary_user = await self.get_user_by_name(username)
        if not primary_user:
            return

        primary = StreamerConnection(primary_user)
        primary.color = "green"

        users[primary.name] = primary
        await self.scan_user(user=primary, users=users)

    async def scan_user(self, user: StreamerConnection, users: dict):
        videos = await self.get_videos(user.twitch_user, self.config.vod_depth)
        await self.find_connections_from_videos(videos, user, users)

    async def get_videos(self, user: TwitchUser, vod_depth: int):
        videos = []
        async for v in self.twitch.get_videos(user_id=user.id, first=vod_depth,
                                              sort=SortMethod.TIME, video_type=VideoType.ARCHIVE):
            if v and v.title and "@" in v.title:
                videos.append(v)
        return videos

    async def get_user_by_name(self, username: str):
        try:
            user = await first(self.twitch.get_users(logins=[username]))
        except Exception as e:
            self.logger.warning(f"Exception with username {username}, {e}")
            user = None
        if user and user.display_name.lower() == username.lower():
            return user
        return None

    async def find_connections_from_videos(self, videos: list[Video],
                                           user: StreamerConnection, users: dict):
        self.logger.debug(f"Finding connections for {user.name}")
        for v in videos:
            if len(users) >= self.config.max_connections:
                break
            if user.size >= self.config.max_children:
                user.color = 'red'
                break
            if names := re.findall('(@\w+)', v.title):
                for name in names:
                    n = name.replace("@", "").lower()
                    if not (4 <= len(n) <= 25) or n in self.blacklisted_channelnames:
                        continue
                    if n not in users:
                        u = await self.get_user_by_name(username=n)
                        if u:
                            child = StreamerConnection(u)
                            user.add_child(child)
                            child.add_child(user)  # Bidirectional enforcement
                            users[child.name] = child
                    elif n not in [x.name for x in user.children]:
                        user.add_child(users[n])
                        if user not in users[n].children:  # Bidirectional enforcement
                            users[n].add_child(user)  # Bidirectional enforcement
                    if len(users) >= self.config.max_connections:
                        break
                    if user.size >= self.config.max_children:
                        user.color = 'red'
                        break
        user.processed = True
        self.logger.debug(f"Done processing {user.name}. Processed {len(users)} users")
