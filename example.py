from musicsync import MusicSync

ms = MusicSync("example@gmail.com","password")
# I use two-factor auth, so the password in my case is a generated "one-time" password

ms.sync_playlist("C:/Path/To/Combi.m3u")
ms.sync_playlist("C:/Path/To/Other Playlist.m3u")