#musicsync: a python class for syncing m3u playlists to Google Music

Provides a utility class around the Google Music API that allows for easy synching of playlists.

##Features

Currently it will look at all the files already in the playlist and:
* Upload any missing files (and add them to the playlist)
* Add any files that are already uploaded but not in the online playlist
* Optionally remove any files from the playlist that are not in the local copy (does not delete
* files!)
* Uploads are done one by one followed by a playlist update for each file (rather than as a
 batch)

It does not remove duplicate entries from playlists or handle multiple entries.

**TODO:** Add optional duplicate remover

##Usage

    from musicsync import MusicSync
    ms = MusicSync()
    # Will prompt for Email and Password - if 2-factor auth is on you'll need to generate a one-
    time password
    ms.sync_playlist("c:/path/to/playlist.m3u")

    ms.delete_song("song_id")


- - -

API used: https://github.com/simon-weber/Unofficial-Google-Music-API
Thanks to: Kevion Kwok and Simon Weber

Use at your own risk - especially for existing playlists

Free to use, reuse, copy, clone, etc
