"""Folder-based demo loading, nearest selection and local receipt archives.

No hardware initialisation, AI calls or network retrieval during replay.
"""
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile
from html.parser import HTMLParser
from urllib.parse import quote, urlparse

from PIL import Image

DIALS = ("soft_power", "overton", "semantic_delta")


class _OutputText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth, self.parts = 0, []

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            if self.depth:
                self.depth += 1
            elif "sentence" in dict(attrs).get("class", "").split():
                self.depth = 1
        elif tag == "br" and self.depth:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag == "div" and self.depth:
            self.depth -= 1

    def handle_data(self, text):
        if self.depth:
            self.parts.append(text)


def dial_value(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Dial value must be finite")
    return max(0.0, min(1.0, value))


def _asset(folder, name):
    if not isinstance(name, str) or not name:
        raise ValueError("Missing asset filename")
    path = (folder / name).resolve()
    if path.parent != folder.resolve() or path.is_symlink():
        raise ValueError("Assets must be files directly inside their demo folder")
    if not path.is_file():
        raise ValueError(f"Missing asset: {name}")
    return path.read_bytes()


def load_catalog(directory):
    """Reload folders each crank. Invalid/disabled records cannot be selected."""
    records, errors = [], []
    directory = Path(directory)
    for path in sorted(directory.glob("*/demo.json")):
        if path.parent.name.startswith((".", "_")):
            continue
        try:
            if path.parent.is_symlink() or path.is_symlink():
                raise ValueError("Demo folders must not be symlinks")
            d = json.loads(path.read_text(encoding="utf-8"))
            if d.get("enabled") is False:
                continue
            if d.get("enabled") is not True:
                raise ValueError("enabled must be true or false")
            if not re.fullmatch(r"[A-Za-z0-9_-]+", d.get("id", "")) or d["id"] != path.parent.name:
                raise ValueError("id must match the folder name (letters, numbers, _ or -)")
            if type(d.get("content_filter")) is not int or d["content_filter"] not in (1, 2, 3):
                raise ValueError("content_filter must be 1, 2 or 3")
            if type(d.get("usb_required")) is not bool:
                raise ValueError("usb_required must be true or false")
            for key in ("text", "country", "topic", "image_title"):
                if not isinstance(d.get(key), str) or not d[key].strip():
                    raise ValueError(f"Missing/non-text {key}")
            if (type(d.get("estimated_token_count")) is not int
                    or not 1 <= d["estimated_token_count"] <= 1_000_000):
                raise ValueError("estimated_token_count must be a positive whole number")
            if not isinstance(d.get("dials"), dict):
                raise ValueError("Missing dials")
            d["dials"] = {key: dial_value(d["dials"][key]) for key in DIALS}
            if len({d[k] for k in ("image", "thermal_image", "summary")}) != 3:
                raise ValueError("Original image, thermal image and summary need distinct filenames")
            assets = {key: _asset(path.parent, d[key]) for key in ("image", "thermal_image", "summary")}
            for key in ("image", "thermal_image"):
                with Image.open(io.BytesIO(assets[key])) as picture:
                    picture.verify()
            page = assets["summary"].decode("utf-8")
            if not page.strip() or "<html" not in page.lower():
                raise ValueError("Summary must be a nonempty HTML page")
            output = _OutputText()
            output.feed(page)
            if "".join(output.parts).strip() != d["text"].strip():
                raise ValueError("Receipt text does not match the summary's output; update both together")
            # The supplied pages use relative assets; archiving retains these names.
            image_refs = re.findall(r'<img\b[^>]*\bsrc=["\']([^"\']+)', page, re.I)
            if not image_refs or any(ref != d["image"] for ref in image_refs):
                raise ValueError("Summary image src must equal the local image filename")
            d["_assets"] = assets  # snapshot before removable folders can change
            records.append(d)
        except (OSError, ValueError, TypeError, KeyError) as e:
            errors.append(f"{path.parent.name}: {e}")
    return records, errors


def distance(record, hardware):
    # Equal weights; squaring avoids an unnecessary square root.
    return sum((record["dials"][key] - dial_value(hardware[key])) ** 2 for key in DIALS)


def select_demo(records, hardware, content_filter, usb_present):
    exact = [d for d in records if d["content_filter"] == content_filter
             and d["usb_required"] == bool(usb_present)]
    # Fallback ignores USB requirements but NEVER promotes an adult record.
    pool = exact or [d for d in records if d["content_filter"] == 1]
    if not pool:
        raise ValueError("No eligible demo or valid enabled green fallback. Restore at least one green demo folder.")
    return min(pool, key=lambda d: (distance(d, hardware), d["id"])), not bool(exact)


def archive_demo(record, project_dir, base_url):
    """Create a content-addressed snapshot; printed links survive demo removal."""
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Invalid demo server address")
    digest = hashlib.sha256()
    digest.update(record["id"].encode())
    for key in ("summary", "image", "thermal_image"):
        digest.update(record[key].encode())
        digest.update(record["_assets"][key])
    name = record["id"] + "-" + digest.hexdigest()[:16]
    parent = Path(project_dir) / "summaries" / "demos"
    parent.mkdir(parents=True, exist_ok=True)
    destination = parent / name
    # Validate existing snapshots before reuse; rebuild any damaged one.
    ready = destination.is_dir() and all(
        (destination / record[key]).is_file()
        and (destination / record[key]).read_bytes() == record["_assets"][key]
        for key in ("summary", "image", "thermal_image"))
    if not ready:
        temporary = Path(tempfile.mkdtemp(prefix=".archive-", dir=parent))
        try:
            for key in ("summary", "image", "thermal_image"):
                (temporary / record[key]).write_bytes(record["_assets"][key])
            if destination.exists():
                # Existing page content is restored to its original bytes.
                for item in temporary.iterdir():
                    os.replace(item, destination / item.name)
            else:
                os.replace(temporary, destination)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
    url = base_url.rstrip("/") + "/summaries/demos/" + quote(name) + "/" + quote(record["summary"])
    return {"qr_url": url, "image_path": str(destination / record["thermal_image"])}


def start_local_server(directory, port=8765):
    import http.server
    import socket
    import threading
    from functools import partial
    root = Path(directory).resolve()
    configured = os.environ.get("DIVERGENCE_BASE_URL", "").strip().rstrip("/")
    if configured:
        p = urlparse(configured)
        if (p.scheme not in ("http", "https") or not p.hostname
                or p.hostname in ("localhost", "127.0.0.1", "::1") or p.path not in ("", "/")):
            raise ValueError("DIVERGENCE_BASE_URL must be the Jetson's phone-reachable base address")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        try:
            probe.connect(("8.8.8.8", 80))
            local_ip = probe.getsockname()[0]
        except OSError:
            try:
                local_ip = socket.gethostbyname(socket.gethostname())
            except OSError:
                local_ip = "127.0.0.1"
    class Handler(http.server.SimpleHTTPRequestHandler):
        def send_head(self):
            target = Path(self.translate_path(self.path)).resolve()
            try:
                relative = target.relative_to(root)
            except ValueError:
                self.send_error(404)
                return None
            if (not relative.parts or relative.parts[0] not in {"summaries", "images", "thermal", "qrcodes", "demos"}
                    or target.suffix.lower() not in {".html", ".png", ".jpg", ".jpeg", ".gif", ".webp"}
                    or not target.is_file()):
                self.send_error(404)
                return None
            return super().send_head()
    server = http.server.ThreadingHTTPServer(("", port), partial(Handler, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = configured or f"http://{local_ip}:{port}"
    if not configured and local_ip.startswith("127."):
        print("Set DIVERGENCE_BASE_URL to the Jetson's network address before phone QR testing")
    return base


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Check demo folders without starting hardware or making API calls")
    parser.add_argument("directory", nargs="?", default=str(Path(__file__).parent / "demos"))
    args = parser.parse_args()
    records, errors = load_catalog(args.directory)
    for d in records:
        print(f"{d['id']}: filter={d['content_filter']} USB={d['usb_required']} dials={d['dials']}")
    for error in errors:
        print("INVALID:", error)
    green = [d for d in records if d["content_filter"] == 1]
    if not green:
        print("ERROR: keep at least one valid enabled green demo for fallback")
    raise SystemExit(1 if errors or not green else 0)
