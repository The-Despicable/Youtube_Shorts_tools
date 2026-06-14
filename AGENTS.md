# Claude Code - YouTube Shorts Uploader Instructions

This tool automates uploading YouTube Shorts using Playwright with Microsoft Edge.

## Setup

1. Install dependencies:
   ```
   pip install playwright
   python -m playwright install chromium
   ```

2. Login once (opens Edge browser, login manually):
   ```
   python cli.py login
   ```

## Commands

### Upload a single video
```
python cli.py upload "path/to/video.mp4" --title "My Short Title"
```
- Auto-publishes as Public
- Title defaults to filename if not provided
- Description defaults to title
- Tags: #Shorts, #gaming

### Upload from the videos folder
```
python cli.py upload videos/WhatsApp Video 2026-06-14 at 3.22.42 PM.mp4
```

### Batch upload all videos in a folder
```
python cli.py batch videos/
```

### Help
```
python cli.py help
```

## File structure
- `cli.py` - Command-line interface
- `uploader.py` - Upload automation logic
- `auth.py` - Login/auth with persistent Edge profile
- `config.py` - Configuration
- `videos/` - Put your video files here
- `browser_profile/` - Stores Edge session (auto-created)

## How it works
1. Opens Edge (not headless - you see the automation)
2. Goes to studio.youtube.com (uses saved session)
3. Clicks Create → Upload videos
4. Selects the video file
5. Fills title, description, tags
6. Sets to Public
7. Clicks Publish
8. Closes after publishing
