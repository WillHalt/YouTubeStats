# YouTubeStats

## Description

This script fetches the details of videos uploaded by a YouTube channel and updates a Google Sheets document with the video information. It retrieves video details such as title, description, upload time, duration, view count, likes, dislikes, and more.

## Prerequisites

- Python 3.x installed
- Google account
- Google Sheets API enabled
- YouTube Data API enabled

## Installation

1. Clone or download the project repository.

2. Install the required Python packages by running the following command:

    ```pip install -r requirements.txt```


3. Set up Google API credentials:

- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project or select an existing project.
- Enable the YouTube Data API and Google Sheets API for the project.
- Create OAuth 2.0 credentials (type: Desktop app) and download the JSON file.
- Save the downloaded JSON file to a secure location.

4. Share the target Google Sheets document with the email address present in the JSON file you downloaded in the previous step. Give the email address edit access to the document.

## Usage

1. Open the code file (`youtube_video_tracker.py`) in a text editor.

2. Replace the `<CLIENT_SECRET_JSON>` placeholder in the `main` function with the path to the JSON file you downloaded in step 3 of the installation.

3. Replace `<Channel Name>` in the `main` function with the name of the YouTube channel for which you want to track the videos.

4. Replace `<SERVICE_ACCOUNT_JSON>` in the `main` function with the path to the JSON file of the service account credentials for accessing the Google Sheets document.

5. Replace `<GOOGLE_SHEETS_FILENAME>` in the `main` function with the name of the Google Sheets document you want to update.

6. Run the script by executing the following command:

```python youtube_video_tracker.py```


The script will authenticate with the Google API and fetch the video details. It will update the Google Sheets document with the video information.

7. Check the Google Sheets document to verify that the video details have been recorded.

## Customization

- You can customize the video details to be recorded in the `parse_and_update_sheet` function. Modify the `row` list to include the desired fields.

- Additional customization can be made based on your specific requirements.

## Notes

- The script will append new video details to the Google Sheets document. If you want to start with a fresh sheet, create a new Google Sheets document and specify its name in the `main` function.

- The script will update the Google Sheets document with videos that have not been recorded before. It uses the video ID to check for duplicates. If you want to force updating all videos, you can clear the Google Sheets document before running the script.

- Make sure to handle any API quota limits and rate limits to avoid interruptions or errors.

- This script can be scheduled to run periodically using task schedulers or cron jobs to keep the Google Sheets document up to date.

- For more information on using the Google Sheets API and YouTube Data API, refer to the official API documentation.


