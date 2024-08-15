# Twitch Collab Network
Visualize the Twitch Collab Network between various streamers.

This application takes in a primary channel to start with and will scan all available VODs (not highlights or clips) for tagged users.

Any user tagged in a VOD title will have their VODs scanned and the process repeats until limits are reached.

This program is still quite experimental and is mainly a proof-of-concept as it is now.

**TODO**: Images

**Long term goal**: Webhosted & run in browser. Maybe optimize it for multithreading.

# Information

- Green nodes indicate the primary channel node and neighbourhood
- Blue nodes indicate all channels that have been *fully* parsed
- Red nodes indicate channel nodes that have been partially parsed, usually by running into limits

You can drag around nodes and hover over them for some more details.

Note: No handling for rate limiting is implemented yet as this is a POC.
Due to time it takes to fetch data and parse, when this is single-threaded it should be fine without hitting rate limits as it is sequentially fetching data.

No errors from Twitch API are handled, or rather, only config input errors are handled. Good luck.

Once you have your config setup, run `main.py` and when it is done (it will log depth progress), a file called `output.html` will be created in the same directory. Open this in a web browser to view the Collab Network.


# Setup

### Environment

This was built using Python 3.10. See `requirements.txt` for dependencies

### Config
You will need to configure the `config.ini` accordingly.

#### [DISPLAY]

use_images: `true` if you want nodes to use profile pictures. `false` for coloured dots.

primary_channel: `channel_name` for your primary channel

blacklisted_users: `twitchname_1,twitchname_2` comma separated list of channels names to ignore in the network generation


#### [DATA]

max_depth: `7` Max number of outward channels to look at before stopping

max_users: `500` Max number of channels/users to look at before stopping

max_vods: `100` Max number of vods on a channel to scan through. Starts at most recent. Hard limit of 100.

max_children: `60` Max number of children a node can have before it stops processing more on *that* node

#### [TWITCH]

See [Twitch Developer Docs](https://dev.twitch.tv/docs/api/get-started/) on how to get your id/secret

client_id: `your_dev_app_client_id`

client_secret: `you_dev_app_client_secret`