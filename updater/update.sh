latest=$(curl -s https://api.github.com/repos/WolfwithSword/TwitchCollabNetwork/releases/latest | grep -i "tag_name" | awk -F '"' '{print $4}')
current=$("../twitchcollabnetwork" -v | awk '{print $3}')

echo "Latest Version: $latest"
if [[ -z "$current" ]]; then
  echo "Current Version: Unknown (May be old, dev, or nightly build)"
  echo "Please update manually to an officially released build at https://github.com/WolfwithSword/TwitchCollabNetwork/releases/latest"
  sleep 6
  exit
else
  echo "Current Version: $current"
fi

sleep 2

if [[ "$current" == "$latest" ]]; then
  echo "Already up to date..."
  sleep 2
  exit
fi

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  platform="ubuntu"
elif [[ "$OSTYPE" == "darwin"* ]]; then
  platform="macos"
elif [[ "$OSTYPE" == 'cygwin' || "$OSTYPE" == 'win32' || "$OSTYPE" == 'msys' ]]; then
  platform="windows"
else
  platform="unknown"
fi

if [[ "$platform" == "unknown" ]]; then
  echo "Unknown platform"
  echo "Please update manually to an officially released build at https://github.com/WolfwithSword/TwitchCollabNetwork/releases/latest"
  sleep 6
  exit
fi

sleep 2

if [ -d "./tmp" ]; then
  printf '%s\n' "Removing Lock (./tmp)"
  rm -rf "./tmp"
fi

dl_url="https://github.com/WolfwithSword/TwitchCollabNetwork/releases/download/$latest/twitchcollabnetwork-$platform-$latest.zip"
output="./tmp/twitchcollabnetwork-$platform-$latest.zip"

echo
echo "Downloading..."

mkdir -p ./tmp
curl -L $dl_url > $output

echo
echo "Download complete"

unzip -q $output -d ./tmp -x "twitchcollabnetwork-$latest/config.ini"
echo $pwd

output="./tmp/$(ls ./tmp | grep ".zip")"
if [ -e "$output" ]; then
  rm -rf "$output"
fi
#rm "./tmp/$(ls ./tmp | grep ".zip")"

outfolder="./tmp/$(ls ./tmp | awk '{print $1}')/*"

cp -r $outfolder "../"
sleep 1
echo "Done updating TwitchCollabNetwork to $latest"
echo
echo "Warning: config.ini was not copied over. Please verify at https://github.com/WolfwithSword/TwitchCollabNetwork/ if any new config items are missing from your existing config."
echo
sleep 5
echo "Cleaning up..."
rm -rf ./tmp
sleep 1