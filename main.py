from twitchAPI.object.api import TwitchUser, Video
from twitchAPI.type import SortMethod, VideoType
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
import asyncio
import re, os
import configparser
from datetime import datetime

import networkx as nx
from pyvis.network import Network #0.3.2

config = configparser.ConfigParser()
config.read('config.ini')

MAX_DEPTH = config.getint(section='DATA', option='max_depth', fallback=7)
MAX_CONNECTIONS = config.getint(section='DATA', option='max_users', fallback=500)
MAX_VOD_DEPTH = config.getint(section='DATA', option='max_vods', fallback=100)
if MAX_VOD_DEPTH > 100:
    MAX_VOD_DEPTH = 100

use_images = config.getboolean(section='DISPLAY', option='use_images', fallback=False)
SHAPE = 'dot'
if use_images:
    SHAPE = "circularImage"

MAX_CHILDREN = config.getint(section='DATA', option='max_children', fallback=75)

PRIMARY_CHANNEL = config.get(section='DISPLAY', option='primary_channel', fallback=None)

if not PRIMARY_CHANNEL:
    print("Please specify a channel")
    quit()
else:
    PRIMARY_CHANNEL = PRIMARY_CHANNEL.lower().strip()


CLIENT_ID = config.get(section='TWITCH', option='client_id', fallback=None)
CLIENT_SECRET = config.get(section='TWITCH', option='client_secret', fallback=None)

if not CLIENT_ID or not CLIENT_SECRET:
    print("Please input your twitch client_id and client_secret")
    quit()

BLACKLISTED = config.get(section='DISPLAY', option='blacklisted_users', fallback="").lower().split(',')
if BLACKLISTED:
    BLACKLISTED = list(map(str.strip, BLACKLISTED))


class Streamer:
    def __init__(self, twitch_user: TwitchUser):
        self.twitch_user = twitch_user

    @property
    def name(self):
        return self.twitch_user.display_name.lower().replace("@", "")

    @property
    def uid(self):
        return self.twitch_user.id


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


async def twitch_run():
    twitch = await Twitch(app_id=CLIENT_ID, app_secret=CLIENT_SECRET)
    users = dict()
    depth = 1

    if "," in PRIMARY_CHANNEL:
        # Multi primary user mode. You may want to increase max number of users if you have higher depths
        primary_channel_names = list(map(str.strip, PRIMARY_CHANNEL.lower().split(',')))
    else:
        primary_channel_names = [PRIMARY_CHANNEL]

    for primary_username in primary_channel_names:

        primary_user = await get_user_by_name(twitch, primary_username)
        if not primary_user:
            continue

        primary = StreamerConnection(primary_user)
        primary.color = "green"

        videos = await get_videos(twitch, primary.twitch_user)

        users[primary.name] = primary

        await find_connections_from_videos(twitch, videos, primary, users)

    if len(users) == 0:
        print("No valid primary channels were found. Please reconfigure the primary_channel(s)")
        return

    print(f"Done loading primary channels: {PRIMARY_CHANNEL}")

    while not all_done(users, depth):
        for user in list(users):
            if not users[user].processed:
                videos = await get_videos(twitch, users[user].twitch_user)
                #print(f"Checking {user} for children")
                await find_connections_from_videos(twitch, videos, users[user], users)
        depth += 1
        print(f"At depth level {depth} with {len(users)} users")

    print(f"Depth: {depth}, Users: {len(users)}")

    G = nx.Graph()
    for u in users:
        user = users[u]
        size = 8+(user.size*3)
        title = f"Go to <a href='https://twitch.tv/{user.name}'>{user.name}</a><br><br>Connections: {user.size}"
        if user.node_color == 'red':
            title += "<br><br>Did not complete processing children nodes<br>"
        G.add_node(node_for_adding=user.name, color=user.node_color, shape=SHAPE,
                   title=title,
                   label=user.name,
                   size=size, image=user.twitch_user.profile_image_url,
                   url=f"https://twitch.tv/{user.name}", channel_name=user.name, connections=len(user.children),
                   border=user.node_color)

    for u in users:
        user = users[u]
        for child in user.children:
            G.add_edge(user.name, child.name)

    net = Network(notebook=False, height="1500px", width="100%",
                  bgcolor="#222222",
                  font_color="white",
                  heading=f"Twitch Collab Network: {PRIMARY_CHANNEL}<br>{datetime.today().strftime('%Y-%m-%d')}<br>Depth: {depth}, Connections: {len(users)}",
                  select_menu=False, filter_menu=True, neighborhood_highlight=True)
    net.from_nx(G)
    options = '{"nodes": {"borderWidth": 5}}'
    #net.show_buttons(filter_=True) # If uncommenting, do not set_options below
    net.set_options(options)

    cwd = os.getcwd()
    net.set_template_dir(os.path.join(cwd, 'templates'), 'template.html')
    net.write_html(name="output.html", notebook=False, local=True, open_browser=False)


def all_done(users: dict, depth: int):
    if len(users) >= MAX_CONNECTIONS or depth >= MAX_DEPTH:
        return True
    for user in users:
        if not users[user].processed:
            return False
    return True


async def find_connections_from_videos(twitch: Twitch, videos: list[Video], user: StreamerConnection,
                                       users: dict):
    #print(f"Finding connections for {user.name}")
    for v in videos:
        if len(users) >= MAX_CONNECTIONS:
            break
        if user.size >= MAX_CHILDREN:
            user.color = 'red'
            break
        if names := re.findall('(@\w+)', v.title):
            for name in names:
                n = name.replace("@", "").lower()
                if n in BLACKLISTED:
                    continue
                if n not in users:
                    u = await get_user_by_name(twitch=twitch, username=n)
                    if u:
                        child = StreamerConnection(u)
                        user.add_child(child)
                        child.add_child(user) #Bidirectional enforcement
                        users[child.name] = child
                elif n not in [x.name for x in user.children]:
                    user.add_child(users[n])
                    if user not in users[n].children: #Bidirectional enforcement
                        users[n].add_child(user) #Bidirectional enforcement
                if len(users) >= MAX_CONNECTIONS:
                    break
                if user.size >= MAX_CHILDREN:
                    user.color = 'red'
                    break
    user.processed = True
    #print(f"Done processing {user.name}. Processed {len(users)} users")


async def get_user_by_name(twitch: Twitch, username: str):
    # TODO: possibly optimize to fetch multiple per depth level at once
    user = await first(twitch.get_users(logins=[username]))
    if user and user.display_name.lower() == username.lower():
        return user
    return None


async def get_videos(twitch: Twitch, user: TwitchUser):
    videos = []
    async for v in twitch.get_videos(user_id=user.id, first=MAX_VOD_DEPTH,
                                     sort=SortMethod.TIME, video_type=VideoType.ARCHIVE):
        if "@" in v.title:
            videos.append(v)
    return videos

asyncio.run(twitch_run())

