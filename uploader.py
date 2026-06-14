"""YouTube Shorts upload using Playwright with persistent browser profile."""
import os
import time
import re
from config import YOUTUBE_STUDIO_URL, VIDEO_EXTENSIONS
from auth import get_context, is_logged_in


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
        try:
            self.page.wait_for_selector("button[aria-label*='Create']", timeout=15000)
            self.page.click("button[aria-label*='Create']")
            print("Clicked Create")
            return True
        except Exception as e:
            print(f"Could not click Create: {e}")
            return False

    def _select_upload_option(self):
        try:
            self.page.wait_for_selector("tp-yt-paper-item", timeout=5000)
            self.page.locator("tp-yt-paper-item:has-text('Upload videos')").click()
            print("Selected 'Upload videos'")
            return True
        except:
            try:
                self.page.locator("text=Upload videos").first.click()
                print("Selected 'Upload videos' (text fallback)")
                return True
            except Exception as e:
                print(f"Could not select upload: {e}")
                return False

    def _upload_file(self, video_path):
        try:
            self.page.wait_for_selector("input[type='file']", state="attached", timeout=15000)
            self.page.set_input_files("input[type='file']", video_path, timeout=10000)
            print(f"Upload started: {os.path.basename(video_path)}")
            return True
        except Exception as e:
            print(f"Upload error: {e}")
            try:
                handle = self.page.query_selector("input[type='file']")
                if handle:
                    handle.set_input_files(video_path)
                    print(f"Upload started (alt method): {os.path.basename(video_path)}")
                    return True
            except:
                pass
            return False

    def _fill_form(self, title, description, tags):
        """Fill all form fields with better selector fallbacks."""
        print("Filling video details...")

        # Wait for the upload form to fully load
        time.sleep(5)

        # Title - try multiple selectors
        title_selectors = [
            "#title-textarea",
            "[aria-label*='title' i]",
            "[placeholder*='title' i]",
            "ytcp-video-title textarea",
            "textarea#textbox",
        ]
        for sel in title_selectors:
            try:
                el = self.page.locator(sel)
                if el.is_visible(timeout=2000):
                    el.fill(title)
                    print(f"Title set via: {sel}")
                    break
            except:
                continue

        # Description - try multiple selectors
        desc_selectors = [
            "#description-textarea",
            "[aria-label*='description' i]",
            "[placeholder*='description' i]",
            "textarea#description",
        ]
        for sel in desc_selectors:
            try:
                el = self.page.locator(sel)
                if el.is_visible(timeout=2000):
                    el.fill(description)
                    print(f"Description set via: {sel}")
                    break
            except:
                continue

        # Tags - try to find tag input
        tag_selectors = [
            "#tags-input input",
            "[aria-label*='tag' i] input",
            "ytcp-form-input-container input",
        ]
        for sel in tag_selectors:
            try:
                el = self.page.locator(sel)
                if el.is_visible(timeout=2000):
                    for tag in tags:
                        el.fill(tag)
                        el.press("Enter")
                        time.sleep(0.3)
                    print(f"Tags added via: {sel}")
                    break
            except:
                continue

    def _set_public(self):
        """Set visibility to Public by scrolling and clicking radio."""
        print("Setting visibility to Public...")
        try:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            # Click the Public radio
            self.page.locator("tp-yt-paper-radio-button:has-text('Public')").click()
            print("Set to Public")
            return True
        except Exception as e:
            print(f"Could not set Public: {e}")
            return False

    def _go_through_wizard(self):
        """Click Next buttons until we reach Visibility step, set Public, then Publish."""
        print("Going through upload wizard...")
        for step in range(3):
            try:
                next_btn = self.page.locator("button:has-text('Next')")
                if next_btn.is_visible(timeout=5000):
                    next_btn.click()
                    print(f"Clicked Next (step {step + 1})")
                    time.sleep(2)
            except:
                print("No more Next buttons")
                break

        # Now try to set visibility to Public
        time.sleep(2)
        try:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            self.page.locator("tp-yt-paper-radio-button").filter(has_text="Public").click(timeout=5000)
            print("Set to Public")
            time.sleep(1)
        except:
            print("Could not set Public visibility")

        # Click Publish
        try:
            pub = self.page.locator("button:has-text('Publish')")
            pub.wait_for(timeout=15000)
            pub.click()
            print("Clicked Publish!")
            time.sleep(3)
            return True
        except:
            print("Publish button not found. Video saved as draft.")
            return False

    def _publish(self):
        return self._go_through_wizard()

    def upload_video(self, video_path, title=None, description=None, tags=None, visibility="public", auto_publish=True):
        """Upload a single video.

        Args:
            video_path: Path to video file
            title: Video title (default: filename without extension)
            description: Video description (default: title + hashtags)
            tags: List of tags (default: [#Shorts])
            visibility: public, unlisted, or private
            auto_publish: If True, auto-fill title/desc and publish
        """
        if not os.path.exists(video_path):
            print(f"File not found: {video_path}")
            return False

        name = os.path.basename(video_path)
        name_no_ext = os.path.splitext(name)[0]

        if title is None:
            # Clean up the filename for use as title
            title = name_no_ext.replace("_", " ").replace("-", " ").strip()
            title = re.sub(r'\s+', ' ', title)

        if description is None:
            description = title

        if tags is None:
            tags = ["#Shorts", "#gaming"]

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
            print("Waiting for upload to process...")
            time.sleep(5)

            self._fill_form(title, description, tags)

            print("Publishing...")
            self._publish()

            print(f"Published: {title}")
            time.sleep(5)
        else:
            self._wait_for_publish_button()
            print("\nBrowser is open for you to fill details.")
            for remaining in range(180, 0, -30):
                print(f"Waiting... {remaining}s left")
                time.sleep(30)

        return True

    def _wait_for_publish_button(self):
        print("Waiting for video processing...")
        time.sleep(5)
        try:
            self.page.wait_for_selector("button:has-text('Publish')", timeout=60000)
            print("Publish button available")
            return True
        except:
            print("Publish button not found")
            return False

    def close(self):
        if self.context:
            self.context.close()
            self.context = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None


def upload_single(video_path, title=None, description=None, tags=None, visibility="public", auto_publish=True):
    """Upload a single video."""
    uploader = YouTubeShortsUploader()
    try:
        return uploader.upload_video(video_path, title, description, tags, visibility, auto_publish)
    finally:
        uploader.close()


def upload_batch(folder_path, visibility="public", auto_publish=True):
    """Upload all videos in a folder."""
    if not os.path.isdir(folder_path):
        print(f"Not a directory: {folder_path}")
        return

    videos = [f for f in os.listdir(folder_path) if f.lower().endswith(VIDEO_EXTENSIONS)]
    if not videos:
        print(f"No video files found in: {folder_path}")
        return

    print(f"Found {len(videos)} video(s)")

    for i, fname in enumerate(videos, 1):
        print(f"\n--- [{i}/{len(videos)}] {fname} ---")
        upload_single(os.path.join(folder_path, fname), visibility=visibility, auto_publish=auto_publish)

        if i < len(videos):
            print("Waiting 5 seconds...")
            time.sleep(5)

    print("\nBatch upload complete!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python uploader.py <video.mp4> [--title TITLE] [--desc DESC]")
        sys.exit(1)
    upload_single(sys.argv[1])