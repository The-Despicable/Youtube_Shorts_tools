"""CLI for YouTube Shorts Uploader using Playwright with persistent Edge profile."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from auth import login
from uploader import upload_single, upload_batch


def main():
    print("YouTube Shorts Uploader")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("""Usage:
  python cli.py login                                   - Login to YouTube Studio
  python cli.py upload <video.mp4> [--title TITLE]      - Upload a single video
  python cli.py batch <folder/> [--public]              - Upload all videos in a folder
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

        upload_single(path, title=title, description=desc, tags=tags,
                      visibility=visibility, auto_publish=auto_publish)

    elif command == "batch":
        if len(sys.argv) < 3:
            print("Usage: python cli.py batch <folder/> [--public]")
            sys.exit(1)
        folder = sys.argv[2].strip('"')
        if not os.path.isdir(folder):
            print(f"Not a folder: {folder}")
            sys.exit(1)
        visibility = "public" if "--public" in sys.argv else "public"
        upload_batch(folder, visibility=visibility, auto_publish=True)

    elif command == "help":
        print("""Commands:
  login         - Login to YouTube Studio (saves session permanently)
  upload        - Upload a single video (auto-publishes as public)
  batch         - Upload all videos from a folder

Examples:
  python cli.py login
  python cli.py upload "video.mp4" --title "My Short" --desc "#Shorts"
  python cli.py batch videos/ --public
""")

    else:
        print(f"Unknown: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()