"""Serve the demo with byte-range support for scroll-controlled video."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent.parent


class RangeHTTPRequestHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        self.byte_range = None
        path = Path(self.translate_path(self.path))
        if path.suffix.lower() != ".mp4":
            return super().send_head()

        try:
            file = path.open("rb")
        except OSError:
            self.send_error(404, "File not found")
            return None

        size = path.stat().st_size
        request_range = self.headers.get("Range")
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", request_range or "")
        if request_range and not match:
            file.close()
            self.send_error(416, "Unsupported byte range")
            return None

        if match:
            first, last = match.groups()
            if not first and not last:
                file.close()
                self.send_error(416, "Empty byte range")
                return None
            start = int(first) if first else max(0, size - int(last))
            end = min(size - 1, int(last)) if first and last else size - 1
            if start > end or start >= size:
                file.close()
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return None
            self.byte_range = (start, end)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            length = end - start + 1
        else:
            self.send_response(200)
            length = size

        self.send_header("Content-Type", "video/mp4")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        self.send_header("Last-Modified", self.date_time_string(path.stat().st_mtime))
        self.end_headers()
        return file

    def copyfile(self, source, outputfile):
        if self.byte_range is None:
            return super().copyfile(source, outputfile)
        start, end = self.byte_range
        source.seek(start)
        remaining = end - start + 1
        while remaining:
            chunk = source.read(min(64 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5188
    handler = partial(RangeHTTPRequestHandler, directory=str(ROOT))
    with ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"Open http://127.0.0.1:{port}/", flush=True)
        server.serve_forever()
