# Twitch Collab Network

<img src="https://github.com/WolfwithSword/TwitchCollabNetwork/blob/88a91f741a224cb82ca3ddaa1620d86205bd6f7e/images/logo.png" width="192px" height="192px">

Visualize the Twitch Collab Network between various streamers.

This application takes in a primary channel(s) to start with and will scan all available VODs (not highlights or clips) for tagged users.

Any user tagged in a VOD title will have their VODs scanned and the process repeats until limits are reached.

This program is still quite experimental and is mainly a proof-of-concept as it is now.

<img src="https://github.com/WolfwithSword/TwitchCollabNetwork/blob/88a91f741a224cb82ca3ddaa1620d86205bd6f7e/images/example.png" width="440px" height="318px">

# Information

- Green nodes indicate the primary channel(s) node and neighbourhood
- Blue nodes indicate all channels that have been *fully* parsed
- Red nodes indicate channel nodes that have been partially parsed, usually by running into limits
- Size of node is dictated by number of connections
- If configured, thickness of edges are dictated by number of collabs between two streamers

You can drag around nodes and edges, and hover over them for some more details.

Not all errors from Twitch API are handled. Good luck.

Once you have your config setup, run `main.py` and when it is done (it will log depth progress), a file called `output.html` and folder `lib` will be created in the same directory. Open this in a web browser to view the Collab Network.

The html file will only work if the `lib` folder is present!

> But I don't want to run NERD code >:(

In that case, you can download a portable executable of this program.

Check on the right side of the screen for [versioned releases](https://github.com/WolfwithSword/TwitchCollabNetwork/releases/latest)!
Alternatively, click on the [latest action here](https://github.com/WolfwithSword/TwitchCollabNetwork/actions/workflows/build.yml?query=branch%3Amain+is%3Asuccess) for the latest dev/nightly release!

Extract the zip to its own folder and make sure it has the executable, templates folder and config.ini. 

Configure the config.ini as per below and you're good to go.

For updating, either download a new version from here when a new release is available (overwrite templates and updater folder, and executable. Do not overwrite config.ini), or run an updater script found in the `updater` folder.

For the config, view the latest template here to see if you need to manually migrate or add new settings.


# Setup

### Environment

This was built using Python 3.10. See `requirements.txt` for dependencies

### Config
You will need to configure the `config.ini` accordingly. Alternatively, you can make multiple and use the CLI parameters to run different configs.


#### [DISPLAY]

| Setting           |        Type/Default         | Description                                                                                                       |
|-------------------|:---------------------------:|-------------------------------------------------------------------------------------------------------------------|
| use_images        |      boolean (`true`)       | `true` for nodes to use profile pictures. <br/>`false` for coloured dots                                          |
| primary_channel   | string(s) (comma-separated) | One or more channel names to use as primary starting channels                                                     |
| blacklisted_users | string(s) (comma-separated) | Comma separated list of channels to ignore completely.<br/>Useful to add sponsor/corporate/company accounts here. |
| weighted_edges    |      boolean (`false`)      | Whether or not to thicken lines/edges between users, based on number of times they've collaborated                |


#### [DATA]

| Setting      | Type/Default | Description                                                                               |
|--------------|:------------:|-------------------------------------------------------------------------------------------|
| max_depth    |  int (`7`)   | Max number for depth of outward channels to look at before stopping                       |
| max_users    | int (`500`)  | Max number of channels/users to look at before stopping                                   |
| max_vods     | int (`100`)  | Max number of public vods on a channel to scan. Starts at latest first. Hard limit of 100 |
| max_children |  int (`60`)  | Max number of children a node can have before it stops processing more for *that* node    |


#### [TWITCH]

See [Twitch Developer Docs](https://dev.twitch.tv/docs/api/get-started/) on how to get your id/secret

| Setting       | Type/Default | Description                  |
|---------------|:------------:|------------------------------|
| client_id     |    string    | Twitch Dev App client id     |
| client_secret |    string    | Twitch Dev App client secret |


#### [CONCURRENCY]

This program supports parallelism / concurrency for user processing either in API requests or cache fetching.

| Setting         |   Type/Default   | Description                                                                                                                                      |
|-----------------|:----------------:|--------------------------------------------------------------------------------------------------------------------------------------------------|
| enabled         | boolean (`true`) | Enable/Disable parallel processing for API calls to Twitch                                                                                       |
| max_concurrency |    int (`12`)    | Max number of concurrent processes. Recommend 5-20.<br/>If you hit Twitch's rate limits, it will wait until your limit resets before continuing. |

#### [CACHE]

This program supports file/disk based caching. Since this program is used to generate an output after running and is not run as a live service, a disk based cache is more useful than in-memory cache, as now API results can persist in between sessions.

| Setting          |   Type/Default   | Description                                                                                                                                                                                                  |
|------------------|:----------------:|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| enabled          | boolean (`true`) | Enable/Disable local disk caching for Twitch API results                                                                                                                                                     |
| user_expiry_s    |   int (`3600`)   | Number of Seconds to cache API results for Twitch Users.<br/>This is generally okay to have really high, as User data almost never changes.                                                                  |
| vodlist_expiry_s |   int (`600`)    | Number of seconds to cache API results for Twitch Vod titles.<br/>Recommend not too long, as if a streamer goes live before this expires, it will not get the newest vod title until the expiry time lapses. |

### CLI Parameters

- **-c \<filepath>** | **--conf_file \<filepath>**
  - Accepts a filepath for a config file to use instead of the default `config.ini` found next to the program
- **-o \<filepath>** | **--output_file \<filepath**
  - A filepath to output the generated html to. Must end with '.html'.
  - Can be in a different directory and will automatically copy the lib folder to it if not present. 
- **-v | --version**
  - Display the current version of TwitchCollabNetwork
- ** -h | --help**
  - Display help message for the program usage 

*Examples*

`./twitchcollabnetwork.exe -c configs/streamer1.config.ini -o output/streamer1/output.html`

`./twitchcollabnetwork.exe -c configs/streamer1.config.ini -o output/streamer1.html`

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