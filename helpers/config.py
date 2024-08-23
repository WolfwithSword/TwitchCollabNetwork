import configparser


class TCNConfig(configparser.ConfigParser):

    def __init__(self):
        super().__init__()
        self.max_depth: int = 7
        self.max_connections: int = 500
        self.vod_depth: int = 100
        self.max_children: int = 75
        self.concurrency: bool = False
        self.max_concurrency: int = 1

    def setup(self, path: str):
        self.read(path)
        self.max_depth = self.getint(section='DATA', option='max_depth', fallback=7)
        if self.max_depth < 0:
            self.max_depth = 1

        self.max_connections = self.getint(section='DATA', option='max_users', fallback=500)
        if self.max_connections < 0:
            self.max_connections = 500

        self.vod_depth = self.getint(section='DATA', option='max_vods', fallback=100)
        if self.vod_depth < 0:
            self.vod_depth = 100
        elif self.vod_depth > 100:
            self.vod_depth = 100

        self.max_children = self.getint(section='DATA', option='max_children', fallback=75)
        if self.max_children < 1:
            self.max_children = 1

        self.concurrency = self.getboolean(section='CONCURRENCY', option='enabled', fallback=False)
        self.max_concurrency = self.getint(section='CONCURRENCY', option='max_concurrency', fallback=2)
        if not self.concurrency or self.max_concurrency < 0:
            self.max_concurrency = 1

    @property
    def primary_channelnames(self) -> list:
        names = self.get(section='DISPLAY', option='primary_channel', fallback=None)
        if not names:
            return []
        if ',' in names:
            return list(map(str.strip, names.lower().split(',')))
        return [names]

    @property
    def shape(self) -> str:
        use_images = self.getboolean(section='DISPLAY', option='use_images', fallback=False)
        if use_images:
            return 'circularImage'
        return 'dot'

    @property
    def twitch_auth(self) -> tuple[str, str]:
        client_id = self.get(section='TWITCH', option='client_id', fallback=None)
        client_secret = self.get(section='TWITCH', option='client_secret', fallback=None)
        return client_id, client_secret

    @property
    def blacklisted_channelnames(self) -> list:
        blacklisted = self.get(section='DISPLAY', option='blacklisted_users', fallback="").lower().split(',')
        if blacklisted:
            blacklisted = list(map(str.strip, blacklisted))
            return blacklisted
        return []
