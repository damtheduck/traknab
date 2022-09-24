import time
import toml
from pathlib import Path
from typing import Optional, List
from pydantic import validate_arguments

from pytube import YouTube
from pytube.contrib.search import Search

from moviepy.editor import AudioFileClip

DOWNLOAD_PATH: str = f'{Path(__file__).parents[1]}/downloads'
TRACKS_PATH: str = f'{Path(__file__).parents[1]}/tracks.toml'

TIMEOUT_THRESHOLD: int = 30
TRACKLENGTH_UPPER_THRESHOLD: int = 60 * 15
FILESIZE_LOWER_THRESHOLD: int = 2
SECONDS_TO_SLEEP: int = 0

# Path validation
assert Path(DOWNLOAD_PATH).is_dir(), \
    f'Download path must lead to a directory. Check the path: {Path(DOWNLOAD_PATH).resolve()}'

assert Path(TRACKS_PATH).suffix == '.toml', \
    f'Tracks file must be a TOML. Check the path: {Path(TRACKS_PATH).resolve()}'

assert Path(TRACKS_PATH).is_file(), \
    f'Tracks path must lead to a file. Check the path: {Path(TRACKS_PATH).resolve()}'

# Loading the tracks file
with open(TRACKS_PATH, mode='r') as f:
    tracks = toml.load(f)


class TrackObtainError(Exception):
    """Failure to obtain a correct/valid track."""
    pass

class TrackAlreadyDownloaded(Exception):
    """Selected track for selected genre already exists in target directory."""
    pass


@validate_arguments
def seconds_to_mins(total_seconds: int) -> str:
    seconds_in_a_minute = 60
    minutes = total_seconds // seconds_in_a_minute
    seconds = total_seconds - (minutes * seconds_in_a_minute)

    return f'{minutes}m {seconds}s'


@validate_arguments
def download(artist: str, track_title: str, target_dir: str, search_term: Optional[str] = None) -> None:
    """
    Download an MP3 file for a given track.

    The track title and artist is looked up on YouTube. The corresponding MP4 file is downloaded and it is subsequently
    converted to an MP3.

    :param artist: Track artist
    :param track_title: Track title
    :param target_folder: String path to folder write MP4 file to
    :param search_term: Optional search term to use instead of the default concatenation of artist and track title
    """
    global filename
    filename = f'{artist} - {track_title}.mp4'

    # Validating target directory
    if not (dir_path := Path(f'{DOWNLOAD_PATH}/{target_dir}')).is_dir():
        print(f'Directory {target_dir} does not exist in {DOWNLOAD_PATH}. Creating...')
        dir_path.mkdir()

    # Checking if the track has already been downloaded
    if Path(f'{DOWNLOAD_PATH}/{target_dir}/{filename}').with_suffix('.mp3').is_file():
        raise TrackAlreadyDownloaded(f'Skipping "{target_dir}/{filename}" as it already has been downloaded...')

    if not search_term:
        search_term = f'{artist} {track_title}'

    print(f'Searching for "{artist} - {track_title}"...')

    # Obtain search results
    search_results: List[YouTube] = Search(search_term).results

    # Selecting first result
    yt: YouTube = search_results[0]
    print(f'Obtained result: "{yt.title}"')
    track_length = yt.length

    print(f'Track length: {seconds_to_mins(track_length)}')

    if track_length > TRACKLENGTH_UPPER_THRESHOLD:
        raise TrackObtainError('Unexpectedly long track. Skipping...')

    # Obtaining audio stream
    audio_stream = yt.streams.get_audio_only(subtype='webm')
    file_size: float = round(audio_stream.filesize * 1e-6, 2)

    print(f'File size: {file_size}MB')

    if file_size < FILESIZE_LOWER_THRESHOLD:
        raise TrackObtainError('Unexpectedly small file size. Skipping...')

    # Downloading and writing to mp4 file
    output_path = f'{DOWNLOAD_PATH}/{target_dir}'

    print('Downloading...')
    audio_stream.download(output_path=output_path, filename=filename, timeout=TIMEOUT_THRESHOLD)
    print('Download complete.')

    # Loading the mp4 file and creating AudioFileClip object
    file_path = f'{output_path}/{filename}'

    audio_file = AudioFileClip(file_path)

    # Creating the path object
    original_path = Path(file_path)

    # Creating a new path object and editing the file extension
    new_path = original_path.with_suffix('.mp3')
    output_path = str(new_path)

    # Writing the new file
    audio_file.write_audiofile(output_path)

    audio_file.close()

    # Deleting the original file
    original_path.unlink()


def main():
    print('Download routine initialised.')

    for genre, tracks_dict in tracks.items():
        for artist, list_of_track_titles in tracks_dict.items():
            for track_title in list_of_track_titles:
                try:
                    # Attemping the download
                    download(artist=artist, track_title=track_title, target_dir=genre)

                    # Sleeping to avoid IP ban
                    if SECONDS_TO_SLEEP:
                        print(f'Sleeping for {SECONDS_TO_SLEEP} seconds...')
                        time.sleep(SECONDS_TO_SLEEP)

                except TrackAlreadyDownloaded:
                    continue

                except TrackObtainError as e:
                    print(e)
                    continue

                except (ConnectionResetError, KeyboardInterrupt) as e:
                    Path(f'{DOWNLOAD_PATH}/{genre}/{filename}').unlink(missing_ok=True)
                    print(f'Exception raised: {e}')
                    print('Breaking...')
                    exit()

    print('Download routine complete.')


if __name__ == '__main__':
    main()
