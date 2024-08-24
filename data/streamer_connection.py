from twitchAPI.object.api import TwitchUser

from data.streamer import Streamer


class StreamerConnection(Streamer):
    def __init__(self, twitch_user: TwitchUser):
        super().__init__(twitch_user)
        self.children = []
        self.processed = False
        self.color = "blue"
        self.collab_counts = dict()

    def add_child(self, child: Streamer):
        if child not in self.children:
            self.children.append(child)

    def add_collab(self, collaborator: Streamer, was_tagged=True):
        val = 1
        if not was_tagged:
            val = 0
        if collaborator.name not in self.collab_counts:
            self.collab_counts[collaborator.name] = val
        else:
            self.collab_counts[collaborator.name] += val
        if was_tagged:
            self.add_child(collaborator)

    @property
    def size(self):
        return len(self.collab_counts)

    @property
    def done(self):
        return self.processed

    @property
    def node_color(self):
        if self.processed:
            return self.color
        return "red"
