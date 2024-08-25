import os
import argparse
import sys
import shutil

import asyncio
import time

from datetime import datetime
import logging

from twitchAPI.twitch import Twitch

import networkx as nx
from pyvis.network import Network  # 0.3.2

from helpers.config import TCNConfig
from helpers.twitch_utils import TwitchUtils
from helpers.utils import chunkify, time_since

from _version import __version__

#########
# Setup #
#########

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tcn-main")

cwd = os.getcwd()
config_path = os.path.join(cwd, 'config.ini')
OUTPUT_FILE = "output.html"
custom_output = False

argv = sys.argv
conf_parser = argparse.ArgumentParser(
    description=__doc__,  # -h/--help
    formatter_class=argparse.RawDescriptionHelpFormatter,
    add_help=False
)
conf_parser.add_argument("-c", "--conf_file", help="Specify config file", metavar="FILE")
conf_parser.add_argument('-o', '--output_file', help="Specify the output file", metavar="FILE")
conf_parser.add_argument('-v', '--version', action='version', version=f'TwitchCollabNetwork Version: {__version__}')

args, remaining_argv = conf_parser.parse_known_args()

logger.info(f"TwitchCollabNetwork"
            f"\nVersion: {__version__}"
            f"\nBy: WolfwithSword"
            f"\nhttps://github.com/WolfwithSword/TwitchCollabNetwork"
            f"\n")

if args.conf_file:
    if os.path.isfile(args.conf_file):
        logger.info(f"Using config file: {args.conf_file}")
        config_path = args.conf_file
    else:
        logger.warning(f"Could not use config path `{args.conf_file}`. Using default file and values")

if not os.path.isfile(config_path):
    logger.error("No valid config file was found. Please setup a valid config file")
    quit()

config = TCNConfig()
config.setup(path=config_path)

if not config.primary_channelnames:
    logger.error("Please specify a channel")
    quit()

CLIENT_ID, CLIENT_SECRET = config.twitch_auth
if not CLIENT_ID or not CLIENT_SECRET:
    logger.error("Please input your twitch client_id and client_secret")
    quit()

if args.output_file:
    if not str(args.output_file).endswith(".html"):
        logger.error(f"Custom output file `{args.output_file}` is invalid. Must be an HTML file")
        quit()
    OUTPUT_FILE = args.output_file
    logger.info(f"Output will go to: {OUTPUT_FILE}")
    custom_output = True

################
# End of Setup #
################

# Each user lookup is always two api requests. First is for user check, second is for video archives check.
# So N=500 users, means 1000 API requests. Mitigated if using disk cache.


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

    weighted_edges = config.weighted_edges
    for u in users:
        user = users[u]
        for child in user.children:
            if user.name == child.name:
                title = (f"<b>{user.name}</b> tagged themselves {user.collab_counts.get(child.name, 0)} "
                         f"time{'s' if user.collab_counts.get(child.name, 0) != 1 else ''}")
                weight = 1
            else:
                user_tag_child_count = user.collab_counts.get(child.name, 0)
                child_tag_user_count = child.collab_counts.get(user.name, 0)
                title = (f"<b>{user.name}</b> tagged <b>{child.name}</b> {user_tag_child_count} "
                         f"time{'s' if user_tag_child_count != 1 else ''}"
                         f"<br><b>{child.name}</b> tagged <b>{user.name}</b> {child_tag_user_count} "
                         f"time{'s' if child_tag_user_count != 1 else ''}")
                weight = min(max(1,
                                 max(user.collab_counts.get(child.name, 1), child.collab_counts.get(user.name, 1))
                                 * 0.6), 10)
            if not weighted_edges:
                weight = 1
            G.add_edge(user.name, child.name, title=title, weight=weight, parent=user.name, child=child.name)

    net = Network(notebook=False, height="1500px", width="100%",
                  bgcolor="#222222",
                  font_color="white",
                  heading=f"Twitch Collab Network: {','.join(config.primary_channelnames)}"
                          f"<br>{datetime.today().strftime('%Y-%m-%d')}"
                          f"<br>Depth: {depth}, Connections: {len(users)}",
                  select_menu=False, filter_menu=True, neighborhood_highlight=True)
    net.from_nx(G)
    options = '{"nodes": {"borderWidth": 5}}'
    # net.show_buttons(filter_=True) # If uncommenting, do not set_options below
    net.set_options(options)

    net.set_template_dir(os.path.join(cwd, 'templates'), 'template.html')

    output_dir = os.path.dirname(OUTPUT_FILE)

    if custom_output and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    net.write_html(name=OUTPUT_FILE, notebook=False, local=True, open_browser=False)

    if custom_output and not os.path.exists(os.path.join(output_dir, 'lib')) and os.path.exists('lib'):
        shutil.copytree("lib", os.path.join(output_dir, "lib"))

    logger.info("Completed in {:.2f} seconds".format(time_since(start_time=start_time)))
    logger.info(f"Output: {os.path.abspath(OUTPUT_FILE)}")

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
