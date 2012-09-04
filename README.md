Provides a utility class around the Google Music API that allows for easy syncing of m3u playlists.

##Features
Choose a local playlist (m3u) to sync and it will:
* Create or modify an existing Google Music playlist
* Upload missing files
* Handles unicode filenames or paths
* Add uploaded (or files already online) to playlist
* Optionally remove files not in local playlist (will not delete those files from the cloud)
* Adds each file to playlist individually as soon as the file is online (instead of as a batch at
the end)
* Makes a best effort not to upload duplicate files by searching and comparing some basic info (this
might fail if you modify id3 tags causing a duplicate to be uploaded)

It does not:
* Remove duplicate entries from playlists
* Support duplicate copies of a file in a playlist (this actually may work - but is untested)
* Re-order playlists (only ensures they contain the same files)

Todo:
* Add option to remove duplicates from playlist
* Allow and handle duplicates
* Option to re-order playlists

##Usage

    from musicsync import MusicSync
    ms = MusicSync()
    # Will prompt for Email and Password - if 2-factor auth is on you'll need to generate a one-time password

    # To sync a playlist
    ms.sync_playlist("c:/path/to/playlist.m3u")

    # To sync a playlist including removing files that are no longer listed locally
    ms.sync_playlist("/path/to/playlist.m3u", remove_missing=True)

    # To delete a song from the cloud (provided only as convenience - must know the song ID)
    ms.delete_song("song_id")


##Requirements
Requires:
* gmusicapi (can use: pip install gmusicapi - or get it from https://github.com/simon-weber/Unofficial-Google-Music-API)

- - -

API used: https://github.com/simon-weber/Unofficial-Google-Music-API

Thanks to: Kevin Kwok and Simon Weber

Use at your own risk - especially for existing playlists

Free to use, reuse, copy, clone, etc
