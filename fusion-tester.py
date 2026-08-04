"""Local web UI for poking at find-all-recipes.py one fusion at a time.

Run with `python fusion-tester.py`, then open http://localhost:8000

Loads find-all-recipes.py itself (everything above generate_fusion_recipes), so
the results shown are produced by the real test_fusion(), not a reimplementation.
Edit find-all-recipes.py and hit refresh in the browser -- it is reloaded per request.
"""

import json
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(ROOT, "find-all-recipes.py")
PAGE = os.path.join(ROOT, "fusion-tester.html")
PORT = 8000


def load_recipes_module():
    """Exec find-all-recipes.py up to (but not including) the recipe generation."""
    with open(SCRIPT, "r", encoding="utf-8") as f:
        source = f.read()
    cutoff = source.index("def generate_fusion_recipes(")
    namespace = {"__name__": "find_all_recipes"}
    os.chdir(ROOT)  # the script opens dist/fusion-properties.json relative to cwd
    exec(compile(source[:cutoff], SCRIPT, "exec"), namespace)
    return namespace


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload, status=200):
        self._send(status, json.dumps(payload), "application/json; charset=utf-8")

    def do_GET(self):
        url = urlparse(self.path)
        try:
            if url.path in ("/", "/index.html", "/fusion-tester.html"):
                with open(PAGE, "r", encoding="utf-8") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")

            elif url.path == "/api/shards":
                mod = load_recipes_module()
                data = mod["data"]
                self._send_json([
                    {
                        "id": id_,
                        "name": attrs.get("name", ""),
                        "rarity": attrs.get("rarity", ""),
                        "category": attrs.get("category", ""),
                        "family": attrs.get("family", []),
                        "input1": attrs.get("input1"),
                        "input2": attrs.get("input2"),
                        "id_result": attrs.get("id_result"),
                    }
                    for id_, attrs in data.items()
                ])

            elif url.path == "/api/fuse":
                query = parse_qs(url.query)
                input1 = (query.get("input1") or [""])[0]
                input2 = (query.get("input2") or [""])[0]
                mod = load_recipes_module()
                data = mod["data"]
                if input1 not in data or input2 not in data:
                    self._send_json({"error": "unknown shard id"}, 400)
                    return
                results = mod["test_fusion"](input1, input2)
                special = mod["find_special_fusion_results"](input1, input2)
                id_fusion = mod["find_id_fusion_results"](input1, input2)
                chameleon = input1 == "L4" or input2 == "L4"

                # Re-run with the cap lifted to see what the [:results_length] slices
                # threw away. find_chameleon_results *builds* only results_length
                # entries rather than truncating, so there is nothing cut off there.
                cut = []
                if not chameleon:
                    limit = mod["results_length"]
                    mod["results_length"] = len(data)
                    uncapped = mod["test_fusion"](input1, input2)
                    uncapped_special = mod["find_special_fusion_results"](input1, input2)
                    mod["results_length"] = limit
                    kept = {res["id"] for res in results}
                    cut = [res for res in uncapped if res["id"] not in kept]
                    special = uncapped_special

                def describe(res):
                    attrs = data.get(res["id"], {})
                    return {
                        "id": res["id"],
                        "count": res["count"],
                        "name": attrs.get("name", "?"),
                        "rarity": attrs.get("rarity", ""),
                        "category": attrs.get("category", ""),
                        "source": (
                            "chameleon" if chameleon
                            else "special" if res["id"] in special
                            else "id"
                        ),
                    }

                self._send_json({
                    "results": [describe(res) for res in results],
                    "cut": [describe(res) for res in cut],
                    "special": special,
                    "id_fusion": id_fusion,
                    "chameleon": chameleon,
                })

            else:
                self._send(404, "not found", "text/plain; charset=utf-8")

        except Exception as exc:  # surface script errors in the UI instead of a blank page
            import traceback
            traceback.print_exc()
            self._send_json({"error": f"{type(exc).__name__}: {exc}"}, 500)

    def log_message(self, fmt, *args):
        pass  # keep the console quiet


if __name__ == "__main__":
    server = HTTPServer(("localhost", PORT), Handler)
    print(f"Fusion tester running at http://localhost:{PORT}  (Ctrl+C to stop)")
    webbrowser.open(f"http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
