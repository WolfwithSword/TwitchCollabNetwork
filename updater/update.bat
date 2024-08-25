@echo off
SET latest=
echo Getting Latest
set latest_cmd="curl -s https://api.github.com/repos/WolfwithSword/TwitchCollabNetwork/releases/latest | FINDSTR \"tag_name\""
FOR /F "delims=" %%a IN ('%latest_cmd%') DO SET raw_latest=%%a
FOR /F "tokens=2" %%a IN ('echo %raw_latest%') DO SET latest=%%a
set latest=%latest:"=%

set current=
cd ../
FOR /F "tokens=3" %%a IN ('"twitchcollabnetwork.exe -v"') DO SET current=%%a
cd ./updater


echo Latest Version: %latest%
IF "%current%"=="" (
  echo Current Version: Unknown. May be old, dev, or nightly build
  echo Please update manually to an officially released build at https://github.com/WolfwithSword/TwitchCollabNetwork/releases/latest
  timeout 6 > NUL
  exit
) ELSE (
  echo Current Version: %current%
)

IF "%current%"=="%latest%" (
  echo "Already up to date..."
  timeout 2 > NUL
  exit
)

if exist ".\tmp\" rd /s /q ".\tmp\"

echo Downloading...
timeout 1 > NUL
SET url="https://github.com/WolfwithSword/TwitchCollabNetwork/releases/download/%latest%/twitchcollabnetwork-windows-%latest%.zip"
SET output="%~dp0tmp\twitchcollabnetwork-%latest%.zip"
echo %output%
mkdir "%~dp0tmp"
bitsadmin /transfer "download-tcn-latest" /download /priority FOREGROUND %url% "%output%"
powershell -command "Expand-Archive -Force '%output%' '%~dp0tmp\'"
del %~dp0tmp\twitchcollabnetwork-%latest%\config.ini
del %~dp0tmp\*.zip
echo:
echo Updating...
echo D|xcopy /s /e /y %~dp0tmp\twitchcollabnetwork-%latest%\ ../
echo:

echo Done updating TwitchCollabNetwork to %latest%
echo:
echo Warning: config.ini was not copied over. Please verify at https://github.com/WolfwithSword/TwitchCollabNetwork/ if any new config items are missing from your existing config.
echo:
timeout 4 > NUL
echo Cleaning up...

if exist ".\tmp\" rd /s /q ".\tmp\"
timeout 2 > NUL
