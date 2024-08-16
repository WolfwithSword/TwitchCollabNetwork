# Twitch Collab Network
Visualize the Twitch Collab Network between various streamers.

This application takes in a primary channel(s) to start with and will scan all available VODs (not highlights or clips) for tagged users.

Any user tagged in a VOD title will have their VODs scanned and the process repeats until limits are reached.

This program is still quite experimental and is mainly a proof-of-concept as it is now.

**TODO**: Images

# Information

- Green nodes indicate the primary channel(s) node and neighbourhood
- Blue nodes indicate all channels that have been *fully* parsed
- Red nodes indicate channel nodes that have been partially parsed, usually by running into limits

You can drag around nodes and hover over them for some more details.

Note: No handling for rate limiting is implemented yet as this is a POC.
Due to time it takes to fetch data and parse, when this is single-threaded it should be fine without hitting rate limits as it is sequentially fetching data.

No errors from Twitch API are handled, or rather, only config input errors are handled. Good luck.

Once you have your config setup, run `main.py` and when it is done (it will log depth progress), a file called `output.html` and folder `lib` will be created in the same directory. Open this in a web browser to view the Collab Network.

The html file will only work if the `lib` folder is present!


# Setup

### Environment

This was built using Python 3.10. See `requirements.txt` for dependencies

### Config
You will need to configure the `config.ini` accordingly.

#### [DISPLAY]

use_images: `true` if you want nodes to use profile pictures. `false` for coloured dots.

primary_channel: `channel_name` for your primary channel(s). Can be a comma separated list of multiple channels to mark as primaries

blacklisted_users: `twitchname_1,twitchname_2` comma separated list of channels names to ignore in the network generation. Sponsor/Corporate accounts are a good option here as it will help cut down on users!


#### [DATA]

max_depth: `7` Max number of outward channels to look at before stopping

max_users: `500` Max number of channels/users to look at before stopping

max_vods: `100` Max number of vods on a channel to scan through. Starts at most recent. Hard limit of 100.

max_children: `60` Max number of children a node can have before it stops processing more on *that* node

#### [TWITCH]

See [Twitch Developer Docs](https://dev.twitch.tv/docs/api/get-started/) on how to get your id/secret

client_id: `your_dev_app_client_id`

client_secret: `you_dev_app_client_secret`

# FAQ

- It Crashed!
  - Yeah this is a proof of concept still
- It's missing collabs I did recently!
  - This can only grab from users mentioned in twitch vod titles with an `@`. Additionally, Twitch saves this information of your vod title *the moment* you go live. If you edit it in during stream, it will not work as expected. Set up your titles before going live for best results.
- I have a bunch of red nodes!
  - Red nodes mean you hit limits of either users or depth or other during processing. You can expand the values in the config at cost of processing time and load time.
- It's slow!
  - With high depth and especially high user limits, and also with multiple primary channels, it will be slow to both build the connections, and to render the HTML each time. This is expected.  
- Stuck on 0% when I open the HTML file!
  - Make sure the `lib` folder is in the same directory as it!

# Notice


Although it would be nice to have this run in-browser with your own twitch auth, I think I prefer having this be a local-only program.

Reasoning is, it can be used to "measure" people and do speculative connections if anyone had access to it. Leaving it to be just a local/personal-use only program reduces that risk significantly.

With that in mind, please have fun using this tool and do not go after any streamer based on information from this tool. Keep in mind, this tool *only* works off of mentioned users in vod titles (that were set before pressing go-live), so it does not actually cover 100% of collabs.

Also, the license is open to derive this work for your own means, just don't commercialize it, harass anyone with it or a derivative, and if you do a derivative work, keep in mind my concern over having it web-hosted with live data. The intended use of this program is more of a "hey I wonder what it looks like right now" and move on kind of deal.

If you have any questions about well, anything, you can contact me on discord at `@wolfwithsword`, or on Twitter `@_WolfwithSword`, or make a GH issue.