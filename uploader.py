"""YouTube Shorts upload using Playwright with persistent browser profile."""

import os
import time
import re
import json
from datetime import datetime
from config import YOUTUBE_STUDIO_URL, VIDEO_EXTENSIONS
from auth import get_context, is_logged_in
from db import init_db, already_uploaded, log_upload


class YouTubeShortsUploader:
    """Automates YouTube Shorts uploads via Playwright with persistent Edge profile."""

    def __init__(self):
        self.context = None
        self.page = None
        self._playwright = None

    def _ensure_logged_in(self):
        """Ensure we have a logged-in session."""
        self.context, self._playwright = get_context()
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.goto(YOUTUBE_STUDIO_URL, wait_until="domcontentloaded")

        if is_logged_in(self.page):
            print("Already logged in.")
            return True

        print("Need to log in. You have 120 seconds.")
        for _ in range(12):
            time.sleep(10)
            if is_logged_in(self.page):
                print("Login detected!")
                return True

        print("Login not detected. Run 'python cli.py login' first.")
        return False

    def _click_create(self):
        """Click the Create button in YouTube Studio."""
        create_selectors = [
            "ytcp-button#create-icon",
            "#create-icon",
            "button[aria-label*='Create']",
            "ytcp-button[aria-label*='Create']",
        ]
        for sel in create_selectors:
            try:
                el = self.page.locator(sel).first
                el.wait_for(state="visible", timeout=10000)
                el.click()
                print(f"Clicked Create via: {sel}")
                return True
            except Exception:
                continue
        print("Could not click Create button.")
        return False

    def _select_upload_option(self):
        """Select 'Upload videos' from the Create dropdown."""
        upload_selectors = [
            "tp-yt-paper-item:has-text('Upload videos')",
            "ytcp-paper-item:has-text('Upload videos')",
            "text=Upload videos",
        ]
        for sel in upload_selectors:
            try:
                el = self.page.locator(sel).first
                el.wait_for(state="visible", timeout=5000)
                el.click()
                print(f"Selected 'Upload videos' via: {sel}")
                return True
            except Exception:
                continue
        print("Could not select 'Upload videos'.")
        return False

    def _upload_file(self, video_path):
        """Set the file input to the video path."""
        try:
            self.page.wait_for_selector("input[type='file']", state="attached", timeout=15000)
            self.page.set_input_files("input[type='file']", video_path)
            print(f"Upload started: {os.path.basename(video_path)}")
            return True
        except Exception as e:
            print(f"Upload error: {e}")
            return False

    def _wait_for_form(self):
        """Wait for the upload dialog/form to appear after file selection."""
        dialog_selectors = [
            "ytcp-uploads-dialog",
            "ytcp-video-metadata-editor",
            "#textbox[contenteditable='true']",
        ]
        for sel in dialog_selectors:
            try:
                self.page.wait_for_selector(sel, timeout=20000)
                print(f"Upload form ready (matched: {sel})")
                return True
            except Exception:
                continue
        print("Warning: Upload form may not have fully loaded.")
        return False

    def _fill_title(self, title):
        """Fill the video title field (contenteditable div, not textarea)."""
        title_selectors = [
            "ytcp-video-metadata-editor #title-textarea #textbox",
            "#title-textarea #textbox",
            "ytcp-video-metadata-editor div[contenteditable='true']",
            "[aria-label*='title' i][contenteditable='true']",
        ]
        for sel in title_selectors:
            try:
                el = self.page.locator(sel).first
                el.wait_for(state="visible", timeout=5000)
                el.triple_click()
                el.fill(title)
                print(f"Title set via: {sel}")
                return True
            except Exception:
                continue
        print("Warning: Could not set title.")
        return False

    def _fill_description(self, description):
        """Fill the video description field."""
        desc_selectors = [
            "ytcp-video-metadata-editor #description-textarea #textbox",
            "#description-textarea #textbox",
            "[aria-label*='description' i][contenteditable='true']",
        ]
        for sel in desc_selectors:
            try:
                el = self.page.locator(sel).first
                el.wait_for(state="visible", timeout=5000)
                el.triple_click()
                el.fill(description)
                print(f"Description set via: {sel}")
                return True
            except Exception:
                continue
        print("Warning: Could not set description.")
        return False

    def _fill_tags(self, tags):
        """Add hashtag tags to the video (optional)."""
        if not tags:
            return
        tag_selectors = [
            "ytcp-free-text-chip-bar input",
            "#tags-input input",
            "[aria-label*='tag' i] input",
        ]
        for sel in tag_selectors:
            try:
                el = self.page.locator(sel).first
                el.wait_for(state="visible", timeout=5000)
                for tag in tags:
                    el.fill(tag)
                    el.press("Enter")
                    time.sleep(0.3)
                print(f"Tags added via: {sel}")
                return
            except Exception:
                continue
        print("Note: Could not add tags — include hashtags in description as fallback.")

    def _fill_form(self, title, description, tags):
        """Wait for the form then fill all fields."""
        self._wait_for_form()
        print("Filling video details...")
        self._fill_title(title)
        self._fill_description(description)
        self._fill_tags(tags)

    def _go_through_wizard(self, schedule_dt=None):
        """Navigate the upload wizard steps, set visibility/schedule, then Publish."""
        print("Navigating upload wizard...")

        for step in range(4):
            try:
                if self.page.locator(
                    "ytcp-button:has-text('Publish'), button:has-text('Publish')"
                ).is_visible():
                    print("Reached Publish step.")
                    break

                next_btn = self.page.locator(
                    "ytcp-button:has-text('Next'), button:has-text('Next')"
                ).first
                next_btn.wait_for(state="visible", timeout=8000)
                next_btn.click()
                print(f"Clicked Next (step {step + 1})")
                time.sleep(1)
                self.page.wait_for_function(
                    "() => !document.querySelector('ytcp-button[disabled]:has-text(\"Next\")')",
                    timeout=10000
                )
            except Exception:
                print(f"No Next at step {step + 1}, moving on.")
                break

        time.sleep(1)
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(0.5)

        if schedule_dt:
            try:
                sched_radio = self.page.locator(
                    "tp-yt-paper-radio-button, ytcp-radio-button"
                ).filter(has_text="Schedule").first
                sched_radio.wait_for(state="visible", timeout=8000)
                sched_radio.click()
                print("Selected Schedule")
                time.sleep(1)

                date_str = schedule_dt.strftime("%m/%d/%Y")
                time_str = schedule_dt.strftime("%I:%M %p")

                date_input = self.page.locator(
                    "input[placeholder*='date' i], input[aria-label*='date' i]"
                ).first
                date_input.fill(date_str)
                date_input.press("Tab")

                time_input = self.page.locator(
                    "input[placeholder*='time' i], input[aria-label*='time' i]"
                ).first
                time_input.fill(time_str)
                time_input.press("Tab")
                time.sleep(1)

                sched_btn = self.page.locator(
                    "ytcp-button:has-text('Schedule'), button:has-text('Schedule')"
                ).first
                sched_btn.wait_for(state="visible", timeout=15000)

                self.page.wait_for_function(
                    """() => {
                        const byTag = [...document.querySelectorAll('ytcp-button')].find(
                            b => b.innerText && b.innerText.trim().startsWith('Schedule')
                        );
                        if (byTag) return byTag.getAttribute('disabled') === null;
                        const btn = document.querySelector('button[aria-label*=\"Schedule\"]');
                        return btn ? !btn.disabled : false;
                    }""",
                    timeout=300000
                )

                sched_btn.click()
                print(f"Scheduled for: {schedule_dt}")
                time.sleep(3)
                return True
            except Exception as e:
                print(f"Scheduling failed: {e} — falling back to Public")

        try:
            public_radio = self.page.locator(
                "tp-yt-paper-radio-button[name='PUBLIC'], "
                "ytcp-radio-button[value='PUBLIC'], "
                "tp-yt-paper-radio-button"
            ).filter(has_text="Public").first
            public_radio.wait_for(state="visible", timeout=8000)
            public_radio.click()
            print("Set to Public")
            time.sleep(1)
        except Exception as e:
            print(f"Could not set Public visibility: {e}")

        try:
            pub_btn = self.page.locator(
                "ytcp-button:has-text('Publish'), button:has-text('Publish')"
            ).first
            pub_btn.wait_for(state="visible", timeout=20000)

            print("Waiting for upload to finish (Publish button to become enabled)...")
            self.page.wait_for_function(
                """() => {
                    const byTag = [...document.querySelectorAll('ytcp-button')].find(
                        b => b.innerText && b.innerText.trim().startsWith('Publish')
                    );
                    if (byTag) return byTag.getAttribute('disabled') === null;
                    const btn = document.querySelector('button[aria-label*=\"Publish\"]');
                    return btn ? !btn.disabled : false;
                }""",
                timeout=300000
            )

            pub_btn.click()
            print("Clicked Publish!")
            time.sleep(3)
            return True

        except Exception as e:
            print(f"Publish failed: {e}")
            print("Video may be saved as draft. Check YouTube Studio.")
            return False

    def _publish(self, schedule_dt=None):
        return self._go_through_wizard(schedule_dt)

    def upload_video(self, video_path, title=None, description=None,
                     tags=None, visibility="public", auto_publish=True):
        """Upload a single video.

        Args:
            video_path: Path to video file
            title: Video title (default: cleaned-up filename or sidecar)
            description: Video description (default: title or sidecar)
            tags: List of tags (default: ['#Shorts', '#gaming'] or sidecar)
            visibility: 'public', 'unlisted', or 'private'
            auto_publish: If True, fills form automatically and publishes
        """
        init_db()

        if not os.path.exists(video_path):
            print(f"File not found: {video_path}")
            return False

        name = os.path.basename(video_path)
        name_no_ext = os.path.splitext(name)[0]

        if already_uploaded(name):
            print(f"Skipping (already uploaded): {name}")
            return True

        sidecar = load_sidecar(video_path)

        if title is None:
            title = sidecar.get("title") or re.sub(r'\s+', ' ', name_no_ext.replace("_", " ").replace("-", " ").strip())
        if description is None:
            description = sidecar.get("description") or title
        if tags is None:
            tags = sidecar.get("tags") or ["#Shorts", "#gaming"]

        schedule_str = sidecar.get("schedule")
        schedule_dt = datetime.fromisoformat(schedule_str) if schedule_str else None

        print(f"\nUploading: {name}")

        if not self._ensure_logged_in():
            return False

        time.sleep(2)

        if not self._click_create():
            return False

        time.sleep(1)

        if not self._select_upload_option():
            return False

        time.sleep(2)

        if not self._upload_file(video_path):
            return False

        if auto_publish:
            self._fill_form(title, description, tags)
            print("Publishing...")
            success = self._publish(schedule_dt)
            if success:
                log_upload(name, title)
            print(f"Done: {title}")
            time.sleep(3)
        else:
            self._wait_for_publish_button()
            print("\nBrowser is open for you to fill details.")
            for remaining in range(180, 0, -30):
                print(f"Waiting... {remaining}s left")
                time.sleep(30)

        return True

    def _wait_for_publish_button(self):
        print("Waiting for video processing...")
        try:
            self.page.wait_for_selector(
                "ytcp-button:has-text('Publish'), button:has-text('Publish')",
                timeout=60000
            )
            print("Publish button available")
            return True
        except Exception:
            print("Publish button not found within timeout.")
            return False

    def close(self):
        if self.context:
            self.context.close()
            self.context = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None


def load_sidecar(video_path: str) -> dict:
    """Load video.json sidecar next to the video file, if it exists."""
    sidecar = os.path.splitext(video_path)[0] + ".json"
    if os.path.exists(sidecar):
        with open(sidecar) as f:
            data = json.load(f)
        print(f"Loaded sidecar: {os.path.basename(sidecar)}")
        return data
    return {}


def upload_single(video_path, title=None, description=None,
                  tags=None, visibility="public", auto_publish=True):
    """Upload a single video."""
    uploader = YouTubeShortsUploader()
    try:
        return uploader.upload_video(video_path, title, description, tags, visibility, auto_publish)
    finally:
        uploader.close()


MAX_RETRIES = 3


def upload_batch(folder_path, visibility="public", auto_publish=True):
    """Upload all videos in a folder using a single browser session."""
    init_db()

    if not os.path.isdir(folder_path):
        print(f"Not a directory: {folder_path}")
        return

    videos = [f for f in os.listdir(folder_path) if f.lower().endswith(VIDEO_EXTENSIONS)]
    if not videos:
        print(f"No video files found in: {folder_path}")
        return

    print(f"Found {len(videos)} video(s)")

    uploader = YouTubeShortsUploader()
    try:
        for i, fname in enumerate(videos, 1):
            if already_uploaded(fname):
                print(f"\n--- [{i}/{len(videos)}] Skipping (already uploaded): {fname} ---")
                continue

            for attempt in range(1, MAX_RETRIES + 1):
                print(f"\n--- [{i}/{len(videos)}] {fname} (attempt {attempt}/{MAX_RETRIES}) ---")
                success = uploader.upload_video(
                    os.path.join(folder_path, fname),
                    visibility=visibility,
                    auto_publish=auto_publish,
                )
                if success:
                    break
                wait = 2 ** attempt
                print(f"Retrying in {wait}s...")
                time.sleep(wait)

            if i < len(videos):
                print("Waiting 5 seconds before next upload...")
                time.sleep(5)
    finally:
        uploader.close()

    print("\nBatch upload complete!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python uploader.py <video.mp4> [--title TITLE] [--desc DESC]")
        sys.exit(1)
    upload_single(sys.argv[1])
