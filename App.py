from flask import Flask, render_template, request, flash
from googleapiclient.discovery import build
from datetime import timedelta
import re
from typing import Optional
from urllib.parse import parse_qs, urlparse

app = Flask(__name__)
app.secret_key = 'generate-a-random-secret-key'  # Change this to a random string
if __name__ == '__main__':
    app.run()  # Remove debug=True for production
class YouTubePlaylistAnalyzer:
    def __init__(self, api_key: str):
        try:
            self.youtube = build('youtube', 'v3', developerKey=api_key)
        except Exception as e:
            raise Exception(f"Failed to initialize YouTube API client: {str(e)}")

    def get_video_duration(self, playlist_id: str) -> int:
        video_duration = 0
        next_page_token = None
        videos_count = 0

        try:
            while True:
                playlist_response = self._get_playlist_page(playlist_id, next_page_token)

                if not playlist_response.get('items'):
                    if 'error' in playlist_response:
                        raise Exception(f"Playlist Error: {playlist_response['error']['message']}")
                    break

                for item in playlist_response['items']:
                    try:
                        video_id = item['contentDetails']['videoId']
                        duration = self._get_video_duration(video_id)
                        if duration:
                            video_duration += duration
                            videos_count += 1
                    except Exception as e:
                        continue

                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break

            return video_duration, videos_count

        except Exception as e:
            raise Exception(f"Failed to get playlist duration: {str(e)}")

    def _get_playlist_page(self, playlist_id: str, page_token: Optional[str] = None) -> dict:
        return self.youtube.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=page_token
        ).execute()

    def _get_video_duration(self, video_id: str) -> Optional[int]:
        video_response = self.youtube.videos().list(
            part='contentDetails',
            id=video_id
        ).execute()

        if not video_response.get('items'):
            return None

        duration = video_response['items'][0]['contentDetails']['duration']
        return self._convert_duration_to_seconds(duration)

    @staticmethod
    def _convert_duration_to_seconds(duration: str) -> int:
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds

def format_duration(seconds: int) -> str:
    return str(timedelta(seconds=seconds))

def extract_playlist_id(url: str) -> str:
    parsed_url = urlparse(url)
    if 'youtube.com' in parsed_url.netloc:
        query_params = parse_qs(parsed_url.query)
        if 'list' in query_params:
            return query_params['list'][0]
    raise ValueError("Invalid YouTube playlist URL")

API_KEY = 'AIzaSyCZrfvAEqhnKaPrlwa5kVy5Axg5PrXo0zw'
analyzer = YouTubePlaylistAnalyzer(API_KEY)

@app.route('/', methods=['GET', 'POST'])
def index():
    duration_str = None
    total_seconds = None
    videos_count = None
    error_message = None

    if request.method == 'POST':
        playlist_url = request.form.get('playlist_url', '').strip()
        try:
            playlist_id = extract_playlist_id(playlist_url)
            total_seconds, videos_count = analyzer.get_video_duration(playlist_id)
            duration_str = format_duration(total_seconds)
        except Exception as e:
            error_message = str(e)
            flash(f"Error: {error_message}", 'error')

    return render_template('index.html',
                         duration=duration_str,
                         seconds=total_seconds,
                         videos_count=videos_count,
                         error=error_message)

if __name__ == '__main__':
    app.run(debug=True)