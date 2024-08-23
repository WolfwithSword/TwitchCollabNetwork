from twitchAPI.object.api import TwitchUser

from data.streamer import Streamer


class StreamerConnection(Streamer):
    def __init__(self, twitch_user: TwitchUser):
        super().__init__(twitch_user)
        self.children = []
        self.processed = False
        self.color = "blue"

    def add_child(self, child: Streamer):
        if child not in self.children:
            self.children.append(child)

    @property
    def size(self):
        return len(self.children)

    @property
    def done(self):
        return self.processed

    @property
    def node_color(self):
        if self.processed:
            return self.color
        return "red"