# traknab
Python package for downloading MP3 tracks from YouTube.

## Usage
Clone the repo and run in the command line.
```
py -m tracknab
```

### Path Configuration
The `DOWNLOAD_PATH` and `TRACKS_PATH` may need to be configured in `__main__.py` - they are defaulted to `downloads/` and `tracks.toml` respectively in the **repo directory** (these will need to be manually created).

### `tracks.toml`
The TOML configuration file should contian all track metadata to be looked up. The file `example_tracks.toml` shows how this should be layed out.
