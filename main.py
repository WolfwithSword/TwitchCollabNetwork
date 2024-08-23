import asyncio
import time
import os

from datetime import datetime
import logging

from twitchAPI.twitch import Twitch

import networkx as nx
from pyvis.network import Network  # 0.3.2

from helpers.config import TCNConfig
from helpers.twitch_utils import TwitchUtils
from helpers.utils import chunkify, time_since

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tcn-main")

config = TCNConfig()
cwd = os.getcwd()
config_path = os.path.join(cwd, 'config.ini')
config.setup(path=config_path)

if not config.primary_channelnames:
    logger.error("Please specify a channel")
    quit()

CLIENT_ID, CLIENT_SECRET = config.twitch_auth
if not CLIENT_ID or not CLIENT_SECRET:
    logger.error("Please input your twitch client_id and client_secret")
    quit()

BLACKLISTED = config.blacklisted_channelnames


# Each user lookup is always two api requests. First is for user check, second is for video archives check.
# So N=500 users, means 1000 API requests


async def twitch_run():

    start_time = time.time()
    twitch = await Twitch(app_id=CLIENT_ID, app_secret=CLIENT_SECRET)
    cache_dir = os.path.join(cwd, '.tcn-cache/')
    twitch_utils = TwitchUtils(config=config, twitch=twitch, cache_dir=cache_dir)
    users = dict()
    depth = 1

    # Load primary users to start with
    if config.concurrency and len(config.primary_channelnames) > 1:
        chunks = list(chunkify(config.primary_channelnames, config.max_concurrency))
        for chunk in chunks:
            if chunk:
                chunked_users = [twitch_utils.init_primary_user(username=user_n, users=users)
                                 for user_n in chunk]
                await asyncio.gather(*chunked_users)
    else:
        for primary_username in config.primary_channelnames:
            await twitch_utils.init_primary_user(username=primary_username, users=users)

    if len(users) == 0:
        logger.error("No valid primary channels were found. Please reconfigure the primary_channel(s)")
        return

    logger.info(f"Done loading primary channels: {','.join(config.primary_channelnames)}")

    # Loop 'recursively' until we hit a limit
    while not all_done(users, depth):
        non_processed_users = list([_u.strip() for _u in list(users) if not users[_u.strip()].processed])
        if config.concurrency and len(non_processed_users) > 1:
            chunks = list(chunkify(non_processed_users, config.max_concurrency))
            for chunk in chunks:
                if chunk:
                    chunked_users = [twitch_utils.scan_user(user=users[_u.strip()], users=users)
                                     for _u in chunk]
                    await asyncio.gather(*chunked_users)
        else:
            for user in non_processed_users:
                await twitch_utils.scan_user(user=users[user.strip()], users=users)
        depth += 1
        progress_time = "{:.2f}".format(time_since(start_time=start_time))
        logger.info(f"At depth level {depth} with {len(users)} users. {progress_time}s...")

    logger.info(f"Depth: {depth}, Users: {len(users)}")

    ###############
    # Build Graph #
    ###############

    G = nx.Graph()
    for u in users:
        user = users[u]
        size = 8 + (user.size * 3)
        title = f"Go to <a href='https://twitch.tv/{user.name}'>{user.name}</a><br><br>Connections: {user.size}"
        if user.node_color == 'red':
            title += "<br><br>Did not complete processing children nodes<br>"
        G.add_node(node_for_adding=user.name, color=user.node_color, shape=config.shape,
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
                  heading=f"Twitch Collab Network: {','.join(config.primary_channelnames)}<br>{datetime.today().strftime('%Y-%m-%d')}<br>Depth: {depth}, Connections: {len(users)}",
                  select_menu=False, filter_menu=True, neighborhood_highlight=True)
    net.from_nx(G)
    options = '{"nodes": {"borderWidth": 5}}'
    # net.show_buttons(filter_=True) # If uncommenting, do not set_options below
    net.set_options(options)

    net.set_template_dir(os.path.join(cwd, 'templates'), 'template.html')
    net.write_html(name="output.html", notebook=False, local=True, open_browser=False)

    logger.info("Completed in {:.2f} seconds".format(time_since(start_time=start_time)))

    if twitch_utils.cache:
        twitch_utils.cache.expire()
        twitch_utils.cache.close()


def all_done(users: dict, depth: int):
    if len(users) >= config.max_connections or depth >= config.max_depth:
        return True
    for user in users:
        if not users[user].processed:
            return False
    return True


asyncio.run(twitch_run())
