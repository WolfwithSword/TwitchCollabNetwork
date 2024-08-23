from twitchAPI.object.api import TwitchUser


class Streamer:
    def __init__(self, twitch_user: TwitchUser):
        self.twitch_user = twitch_user

    @property
    def name(self):
        return self.twitch_user.display_name.lower().replace("@", "")

    @property
    def uid(self):
        return self.twitch_user.id
