# YouTube Shorts Uploader

Automated YouTube Shorts uploader using Playwright with Microsoft Edge.

## Setup

1. Install dependencies:
   ```bash
   pip install playwright
   python -m playwright install chromium
   ```

2. Login once (opens Edge browser, login manually):
   ```bash
   python cli.py login
   ```

## Usage

### Upload a single video
```bash
python cli.py upload "path/to/video.mp4" --title "My Short Title"
```
- Auto-publishes as Public
- Title defaults to filename if not provided
- Description defaults to title
- Tags: #Shorts, #gaming

### Upload with custom description
```bash
python cli.py upload "video.mp4" --title "My Short" --desc "#Shorts #gaming"
```

### Batch upload all videos in a folder
```bash
python cli.py batch videos/
```

### Show help
```bash
python cli.py help
```

## Project Structure

| File | Description |
|---|---|
| `cli.py` | Command-line interface |
| `uploader.py` | Upload automation logic |
| `auth.py` | Login/auth with persistent Edge profile |
| `config.py` | Configuration |
| `youtube_api.py` | YouTube API integration |
| `videos/` | Put your video files here |
| `browser_profile/` | Stores Edge session (auto-created) |

## How it works

1. Opens Edge (not headless - you see the automation)
2. Goes to studio.youtube.com (uses saved session)
3. Clicks Create → Upload videos
4. Selects the video file
5. Fills title, description, tags
6. Sets to Public
7. Clicks Publish
8. Closes after publishing
