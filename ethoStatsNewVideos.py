import os
import gspread
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from oauth2client.service_account import ServiceAccountCredentials
from google.auth.transport.requests import Request
import pickle
import requests
import time
from datetime import datetime, timezone
import calendar
import re

scopes = ["https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/spreadsheets"]

# Function to authenticate with Google API
def authenticate_google_api(client_secrets_file, scopes):
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

# Function to get channel's details
def get_channel_details(youtube, forUsername):
    channel_request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        forUsername=forUsername
    )
    channel_response = channel_request.execute()

    return channel_response

# Function to get the details of the videos in the "Uploads" playlist
def get_videos_details(youtube, uploads_playlist_id, maxResults):
    videos_request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        maxResults=maxResults,
        playlistId=uploads_playlist_id
    )
    videos_response = videos_request.execute()

    return videos_response

# Function to open the Google Sheets document and get the first and second sheets
def open_google_sheets(sheets_filename, sheet_name):
    gc = gspread.service_account(filename=sheets_filename)
    sh = gc.open(sheet_name)

    return sh

# Function to read the search terms and series names from the second sheet
def get_search_terms_and_series_names(series_worksheet):
    search_terms = series_worksheet.col_values(1)
    series_names = series_worksheet.col_values(2)

    return search_terms, series_names

# Function to create a dictionary that maps each search term to the corresponding series name
def create_series_dict(search_terms, series_names):
    series_dict = dict(zip(search_terms, series_names))

    return series_dict

# Function to get the current rows count in the sheet
def get_rows_count(worksheet):
    rows_count = len(worksheet.get_all_values())

    return rows_count

# Function to get the upload time of the first video
def get_upload_time_of_first_video(videos_response):
    raw_date = videos_response['items'][0]['snippet']['publishedAt']
    next_upload_time = datetime.fromisoformat(raw_date.replace('Z', '')).replace(tzinfo=timezone.utc)

    return next_upload_time

####################################################################################################
# Function to format video duration
def format_duration(duration):
    parts = duration.replace('PT', '').replace('S', '').split('H')
    if len(parts) == 2:
        hours = int(parts[0])
        minutes, seconds = map(int, parts[1].split('M'))
    elif 'M' in parts[0]:
        hours = 0
        minutes, seconds = map(int, parts[0].split('M'))
    else:
        hours = 0
        minutes = 0
        seconds = int(parts[0])

    formatted_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return formatted_duration

# Function to get dislikes from ReturnYouTubeDislike API
def get_dislikes_from_return_youtube_dislike_api(video_id):
    r = requests.get(f"https://returnyoutubedislikeapi.com/votes?videoId={video_id}")
    r.raise_for_status()
    dislike_data = r.json()

    return dislike_data.get('dislikes', 0)

# Function to get video's details
def get_video_details(youtube, video_id):
    video_request = youtube.videos().list(part="contentDetails,statistics", id=video_id)
    video_response = video_request.execute()
    video_details = video_response['items'][0]

    return video_details

def parse_and_update_sheet(youtube, videos_response, next_upload_time, series_dict, worksheet):
    for item in videos_response['items']:
        video = item['snippet']
        video_id = video['resourceId']['videoId']
        existing_video_ids = worksheet.col_values(4)
        if video_id in existing_video_ids:
            continue

        raw_date = video['publishedAt']
        published_at = datetime.fromisoformat(raw_date.replace('Z', ''))
        year, month, day, hour, minute, second = published_at.year, published_at.month, published_at.day, published_at.hour, published_at.minute, published_at.second
        weekday = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][published_at.weekday()]
        month_abbr = calendar.month_abbr[month]
        date_num_value = f"{weekday}, {day:02d}-{month_abbr}-{year}; {hour:02d}:{minute:02d}:{second:02d}"

        upload_time = datetime.fromisoformat(raw_date.replace('Z', '')).replace(tzinfo=timezone.utc)
        time_difference_in_seconds = int((next_upload_time - upload_time).total_seconds())
        days, remainder = divmod(time_difference_in_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_since_next_upload_str = f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"

        title, description, url = video['title'], video['description'], f"https://www.youtube.com/watch?v={video_id}"

        video_details = get_video_details(youtube, video_id)
        raw_duration = video_details['contentDetails']['duration']
        formatted_duration = format_duration(raw_duration)
        view_count, likes = int(video_details['statistics']['viewCount']), int(video_details['statistics']['likeCount'])
        matching_series = [series_dict[term] for term in series_dict if term in title]
        
        episode_match = re.search(r'(?:#|episode)\s*(\d+)', title, re.I)
        episode = episode_match.group(1) if episode_match else ''

        dislikes = get_dislikes_from_return_youtube_dislike_api(video_id)

        series = ', '.join(matching_series)
        
        # Episode Info
        # Look for a number that comes immediately after '#' or 'episode' (case-insensitive)
        match = re.search(r'(?:#|episode)\s*(\d+)', title, re.I)
        if match:
            episode = match.group(1)  # The first group contains the number
        else:
            episode = None  # No number found

        # Split the title at the first occurrence of ':'
        parts = title.split(':', 1)

        if len(parts) > 1:
            # There was a ':' in the title, so we take the part after it
            episode_title = parts[1].strip()  # Use strip to remove leading and trailing whitespace
        else:
            # There was no ':' in the title
            episode_title = None
        
        # Calculating ratios
        if likes and dislikes:
            likes_dislikes_ratio = round(likes / dislikes, 2)
        else:
            likes_dislikes_ratio = 'N/A'

        if view_count and likes:
            views_likes_ratio = round(view_count / likes, 2)
        else:
            views_likes_ratio = 'N/A'

        row = [video['publishedAt'], title, description, video_id, year,
            month, day, hour, minute, second, weekday, date_num_value, 
            matching_series[0] if matching_series else 'Other', episode[0] if episode else "N/A", 
            episode_title, url, raw_duration, formatted_duration, view_count, 
            likes, dislikes, likes_dislikes_ratio, views_likes_ratio, time_since_next_upload_str
        ]

        worksheet.insert_row(row, 2)  # Inserts the row at the second line, shifting other rows down

        next_upload_time = upload_time

def main():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "<CLIENT_SECRET_JSON_DIR>"

    creds = authenticate_google_api(client_secrets_file, scopes)

    youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=creds)

    channel_response = get_channel_details(youtube, "EthosLab")
    uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    videos_response = get_videos_details(youtube, uploads_playlist_id, 1)  # Get only the latest video

    sh = open_google_sheets('<SERVICE_ACCOUNT_JSON_DIR>', "<GOOGLE_SHEETS_FILENAME>")
    worksheet = sh.get_worksheet(0)
    series_worksheet = sh.get_worksheet(1)

    search_terms, series_names = get_search_terms_and_series_names(series_worksheet)

    series_dict = create_series_dict(search_terms, series_names)

    # Get the video ID of the latest video in the sheet
    latest_video_id_in_sheet = worksheet.cell(2, 4).value  # Assuming video IDs are in column 4

    # Get the video ID of the latest video on YouTube
    latest_video_id_on_youtube = videos_response['items'][0]['snippet']['resourceId']['videoId']

    # Check if a new video has been uploaded
    if latest_video_id_on_youtube != latest_video_id_in_sheet:
        # A new video has been uploaded, so we insert its details at the top of the sheet
        next_upload_time = get_upload_time_of_first_video(videos_response)
        parse_and_update_sheet(youtube, videos_response, next_upload_time, series_dict, worksheet)
        print("New video added!")
    else:
        print("No new video available.")

if __name__ == "__main__":
    main()