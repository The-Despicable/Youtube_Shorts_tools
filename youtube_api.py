"""YouTube Data API v3 integration for uploading Shorts."""
import os
import json
from pathlib import Path
from typing import Optional, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


# OAuth2 scopes for YouTube
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

# Token file path
TOKEN_FILE = Path(__file__).parent / "token.json"
CLIENT_SECRET_FILE = Path(__file__).parent / "client_secret.json"


class YouTubeAPI:
    """YouTube Data API v3 wrapper."""

    def __init__(self):
        self.service = None
        self.credentials = None

    def authenticate(self) -> bool:
        """Authenticate using OAuth2."""
        creds = None

        # Load existing token
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        # If no valid credentials, run OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing expired token...")
                creds.refresh(Request())
            else:
                if not CLIENT_SECRET_FILE.exists():
                    print(f"ERROR: client_secret.json not found at {CLIENT_SECRET_FILE}")
                    print("Please download it from Google Cloud Console and place it in the tool directory.")
                    return False
                
                print("Starting OAuth2 authentication...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CLIENT_SECRET_FILE), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
            print(f"Token saved to {TOKEN_FILE}")

        self.credentials = creds
        self.service = build("youtube", "v3", credentials=creds)
        print("Authentication successful!")
        return True

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        category_id: str = "22",  # People & Blogs
        privacy_status: str = "public",  # public, private, unlisted
        made_for_kids: bool = False,
        publish_at: Optional[str] = None,  # RFC3339 format for scheduling
    ) -> Optional[str]:
        """Upload a video to YouTube.

        Returns:
            Video ID if successful, None otherwise.
        """
        if not self.service:
            print("ERROR: Not authenticated. Call authenticate() first.")
            return None

        if not os.path.exists(video_path):
            print(f"ERROR: File not found: {video_path}")
            return None

        if tags is None:
            tags = []

        # Ensure #Shorts tag is included
        if "#Shorts" not in tags and "Shorts" not in tags:
            tags.append("#Shorts")

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "madeForKids": made_for_kids,
            },
        }

        if publish_at:
            body["status"]["publishAt"] = publish_at
            body["status"]["privacyStatus"] = "private"  # Required for scheduling

        try:
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype="video/mp4",
            )

            request = self.service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )

            print(f"Uploading: {os.path.basename(video_path)}")
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Progress: {int(status.progress() * 100)}%")

            video_id = response.get("id")
            print(f"Upload complete! Video ID: {video_id}")
            print(f"URL: https://youtu.be/{video_id}")
            return video_id

        except HttpError as e:
            print(f"Upload failed: {e}")
            return None

    def upload_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """Upload a custom thumbnail for a video."""
        if not self.service:
            print("ERROR: Not authenticated.")
            return False

        if not os.path.exists(thumbnail_path):
            print(f"ERROR: Thumbnail not found: {thumbnail_path}")
            return False

        try:
            media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            self.service.thumbnails().set(
                videoId=video_id,
                media_body=media,
            ).execute()
            print(f"Thumbnail uploaded for video {video_id}")
            return True
        except HttpError as e:
            print(f"Thumbnail upload failed: {e}")
            return False

    def get_my_channels(self) -> List[dict]:
        """Get list of authenticated user's channels."""
        if not self.service:
            print("ERROR: Not authenticated.")
            return []

        try:
            response = self.service.channels().list(
                part="snippet,contentDetails,statistics",
                mine=True,
            ).execute()
            return response.get("items", [])
        except HttpError as e:
            print(f"Failed to get channels: {e}")
            return []

    def get_video(self, video_id: str) -> Optional[dict]:
        """Get video details by ID."""
        if not self.service:
            return None

        try:
            response = self.service.videos().list(
                part="snippet,status,statistics",
                id=video_id,
            ).execute()
            items = response.get("items", [])
            return items[0] if items else None
        except HttpError as e:
            print(f"Failed to get video: {e}")
            return None


def upload_short(
    video_path: str,
    title: str,
    description: str = "",
    tags: Optional[List[str]] = None,
    privacy_status: str = "public",
    thumbnail_path: Optional[str] = None,
    schedule_time: Optional[str] = None,
) -> Optional[str]:
    """Convenience function to upload a Short."""
    api = YouTubeAPI()
    if not api.authenticate():
        return None

    video_id = api.upload_video(
        video_path=video_path,
        title=title,
        description=description,
        tags=tags,
        privacy_status=privacy_status,
        made_for_kids=False,
        publish_at=schedule_time,
    )

    if video_id and thumbnail_path:
        api.upload_thumbnail(video_id, thumbnail_path)

    return video_id


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python youtube_api.py <video_path> <title> [description]")
        sys.exit(1)

    video_path = sys.argv[1]
    title = sys.argv[2]
    description = sys.argv[3] if len(sys.argv) > 3 else ""

    upload_short(video_path, title, description)