"""CLI for YouTube Shorts Uploader using Playwright with persistent Edge profile."""
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))

from auth import login
from uploader import upload_single, upload_batch


def main():
    print("YouTube Shorts Uploader")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("""Usage:
  python cli.py login                                   - Login to YouTube Studio
  python cli.py upload <video.mp4> [--title TITLE] [--desc DESC] [--tags TAG1,TAG2] [--schedule 2026-06-18T09:00:00]
  python cli.py batch <folder/> [--unlisted]            - Upload all videos in a folder
  python cli.py logs                                    - Show upload history
  python cli.py help                                    - Show this help
""")
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "login":
        login()

    elif command == "upload":
        if len(sys.argv) < 3:
            print("Usage: python cli.py upload <video.mp4> [--title TITLE] [--desc DESC]")
            sys.exit(1)
        path = sys.argv[2].strip('"')
        if not os.path.exists(path):
            print(f"File not found: {path}")
            sys.exit(1)

        title = None
        desc = None
        tags = None
        visibility = "public"
        auto_publish = True

        if "--title" in sys.argv:
            idx = sys.argv.index("--title") + 1
            if idx < len(sys.argv) and not sys.argv[idx].startswith("--"):
                title = sys.argv[idx]
        if "--desc" in sys.argv:
            idx = sys.argv.index("--desc") + 1
            if idx < len(sys.argv) and not sys.argv[idx].startswith("--"):
                desc = sys.argv[idx]
        if "--tags" in sys.argv:
            idx = sys.argv.index("--tags") + 1
            if idx < len(sys.argv) and not sys.argv[idx].startswith("--"):
                tags = [t.strip() for t in sys.argv[idx].split(",")]
        schedule_dt = None
        if "--schedule" in sys.argv:
            idx = sys.argv.index("--schedule") + 1
            if idx < len(sys.argv) and not sys.argv[idx].startswith("--"):
                schedule_dt = datetime.fromisoformat(sys.argv[idx])

        upload_single(path, title=title, description=desc, tags=tags,
                      visibility=visibility, auto_publish=auto_publish,
                      schedule_dt=schedule_dt)

    elif command == "batch":
        if len(sys.argv) < 3:
            print("Usage: python cli.py batch <folder/> [--public]")
            sys.exit(1)
        folder = sys.argv[2].strip('"')
        if not os.path.isdir(folder):
            print(f"Not a folder: {folder}")
            sys.exit(1)
        visibility = "unlisted" if "--unlisted" in sys.argv else "public"
        upload_batch(folder, visibility=visibility, auto_publish=True)

    elif command == "logs":
        from db import init_db, list_uploads
        init_db()
        rows = list_uploads()
        if not rows:
            print("No uploads logged yet.")
        else:
            print(f"\n{'#':<4} {'Filename':<40} {'Title':<30} {'Uploaded At'}")
            print("-" * 90)
            for i, (fname, title, ts) in enumerate(rows, 1):
                print(f"{i:<4} {fname:<40} {(title or ''):<30} {ts}")
        print()

    elif command == "help":
        print("""Commands:
  login         - Login to YouTube Studio (saves session permanently)
  upload        - Upload a single video (auto-publishes as public)
  batch         - Upload all videos from a folder
  logs          - Show upload history

Examples:
  python cli.py login
  python cli.py upload "video.mp4" --title "My Short" --desc "#Shorts" --tags "#Shorts,#gaming"
  python cli.py upload "video.mp4" --schedule "2026-06-18T09:00:00"
  python cli.py batch videos/ --unlisted
""")

    else:
        print(f"Unknown: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()