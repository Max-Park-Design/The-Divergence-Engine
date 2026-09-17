"""Add one real saved HTML output to the demo folders. No AI calls."""
import argparse
from html.parser import HTMLParser
from html import escape, unescape
import json
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageEnhance


class SavedPage(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.heading, self.sentence, self.timestamp = [], [], []
        self.image_url, self.image_title = None, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "img" and self.image_url is None:
            self.image_url, self.image_title = a.get("src"), a.get("alt", "")
        if tag not in {"img", "br", "meta", "link", "hr", "input"}:
            self.stack.append((tag, a))

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if any(t == "h1" for t, _ in self.stack):
            self.heading.append(data)
        if any("sentence" in a.get("class", "").split() for _, a in self.stack):
            self.sentence.append(data)
        if any("timestamp" in a.get("class", "").split() for _, a in self.stack):
            self.timestamp.append(data)


def add_demo(args):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.id):
        raise ValueError("Use only letters, numbers, _ and - in the id")
    for v in (args.soft_power, args.overton, args.delta):
        if not 0 <= v <= 1:
            raise ValueError("Dial values must be between 0 and 1")
    estimated_tokens = getattr(args, "estimated_tokens", 10000)
    if type(estimated_tokens) is not int or estimated_tokens < 1:
        raise ValueError("Estimated tokens must be a positive whole number")
    root = Path(args.directory).resolve()
    root.mkdir(parents=True, exist_ok=True)
    destination = root / args.id
    if destination.exists():
        raise ValueError("That demo folder already exists; choose a new id")
    source = Path(args.html).resolve()
    page = source.read_text(encoding="utf-8")
    parser = SavedPage()
    parser.feed(page)
    heading = "".join(parser.heading).strip()
    if " — " not in heading:
        raise ValueError("Expected a saved output heading: Topic — Country")
    topic, country = heading.rsplit(" — ", 1)
    text = "".join(parser.sentence).strip()
    title = args.title or parser.image_title
    if not text or not title or not parser.image_url:
        raise ValueError("Saved page needs output text, an image and a nonblank image title")
    staging = Path(tempfile.mkdtemp(prefix="_import-", dir=root))
    try:
        remote = urlparse(parser.image_url)
        if args.image:
            raw = Path(args.image).read_bytes()
        elif remote.scheme in ("http", "https"):
            request = Request(parser.image_url, headers={"User-Agent": "DivergenceEngine/1.0 (demo capture)"})
            with urlopen(request, timeout=30) as response:
                raw = response.read(30 * 1024 * 1024 + 1)
            if len(raw) > 30 * 1024 * 1024:
                raise ValueError("Image exceeds 30 MiB; provide a smaller local copy with --image")
        elif not remote.scheme:
            image_path = Path(parser.image_url)
            raw = (image_path if image_path.is_absolute() else source.parent / image_path).read_bytes()
        else:
            raise ValueError("Supply a local --image for this image URL")
        import io
        with Image.open(io.BytesIO(raw)) as picture:
            suffix = {"JPEG": ".jpg", "PNG": ".png", "GIF": ".gif", "WEBP": ".webp"}.get(picture.format)
            if not suffix:
                raise ValueError("Supported image formats: JPEG, PNG, GIF and WebP")
            image_name = "image" + suffix
            (staging / image_name).write_bytes(raw)
            picture.seek(0)
            thermal = picture.convert("L")
            thermal = thermal.resize((384, max(1, int(384*thermal.height/thermal.width))), Image.Resampling.LANCZOS)
            thermal = ImageEnhance.Contrast(thermal).enhance(1.8)
            thermal = ImageEnhance.Sharpness(thermal).enhance(2.0)
            thermal.convert("1", dither=Image.Dither.FLOYDSTEINBERG).save(staging / "thermal.png")
        # Change only the image src. Its existing source-page link stays intact.
        page, changes = re.subn(r'(<img\b[^>]*\bsrc=)(["\'])(.*?)\2',
                               lambda m: m[1]+m[2]+image_name+m[2], page, count=1, flags=re.I)
        if changes != 1:
            raise ValueError("Could not find the image tag in the saved HTML")
        if args.title:
            old_title = parser.image_title or ""
            page = page.replace(escape(old_title, quote=True), escape(title, quote=True)) if old_title else page
        record = {
            "id": args.id, "enabled": True, "content_filter": args.filter,
            "usb_required": args.usb, "dials": {"soft_power": args.soft_power, "overton": args.overton, "semantic_delta": args.delta},
            "text": text, "topic": topic, "country": country, "image_title": title,
            "image": image_name, "thermal_image": "thermal.png", "summary": "summary.html",
            "estimated_token_count": estimated_tokens,
            "settings_basis": "entered by user during import", "recorded_at": "".join(parser.timestamp).strip(),
            "recorded_bpm": None, "recorded_emotional_state": None, "recorded_token_count": None,
        }
        if args.usb:
            record["usb_title"] = args.usb_title
        (staging / "summary.html").write_text(page, encoding="utf-8")
        (staging / "demo.json").write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        staging.rename(destination)
        return destination
    finally:
        if staging.exists():
            shutil.rmtree(staging)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--html", required=True, help="A genuine saved output HTML file")
    p.add_argument("--id", required=True)
    p.add_argument("--filter", type=int, choices=(1, 2, 3), required=True)
    p.add_argument("--soft-power", type=float, required=True)
    p.add_argument("--overton", type=float, required=True)
    p.add_argument("--delta", type=float, required=True)
    p.add_argument("--estimated-tokens", type=int, default=10000)
    p.add_argument("--image", help="Optional local original image instead of downloading")
    p.add_argument("--title", help="Optional explicit short image title")
    p.add_argument("--usb", action="store_true")
    p.add_argument("--usb-title", default="News from Nowhere")
    p.add_argument("--directory", default=str(Path(__file__).parent / "demos"))
    args = p.parse_args()
    try:
        print("Added:", add_demo(args))
    except Exception as e:
        p.exit(1, f"Demo was not added: {e}\n")
