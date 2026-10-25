#!/usr/bin/env python3
"""Submit the verified 8GB MOSS-Image cel workflow to a local ComfyUI."""

import argparse
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE = (
    "A single full-body character illustration in the exact hand-drawn cel style of "
    "Shanghai Animation Film Studio's 1984 series Black Cat Sheriff: bold even black ink "
    "contours, flat gouache color fills, slight film grain, painted scenic background, "
    "1980s Chinese cartoon proportions, large glossy eyes, bipedal anthropomorphic animal "
    "with simple clothing folds, warm clear daylight, blank signs with no writing, no text, "
    "no letters, no logo, no watermark, no photo, no 3D, no modern anime. "
)


def post(url, payload=None, timeout=60):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="http://127.0.0.1:8188")
    parser.add_argument("--prompt", required=True, help="Scene only. Style prefix is added.")
    parser.add_argument("--seed", type=int, default=1101)
    parser.add_argument("--prefix", default="sg_moss/shot")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    wf = json.loads((ROOT / "workflows" / "moss_shangmei_api.json").read_text(encoding="utf-8"))
    wf["4"]["inputs"]["text"] = STYLE + args.prompt
    wf["7"]["inputs"]["seed"] = args.seed
    wf["9"]["inputs"]["filename_prefix"] = args.prefix

    submitted = post(args.host.rstrip("/") + "/prompt", {"prompt": wf, "client_id": "shangmei-moss"})
    if submitted.get("node_errors"):
        raise SystemExit("node_errors: " + json.dumps(submitted["node_errors"], ensure_ascii=False))
    prompt_id = submitted["prompt_id"]
    print("prompt_id", prompt_id)

    deadline = time.time() + args.timeout
    while time.time() < deadline:
        hist = post(args.host.rstrip("/") + "/history/" + prompt_id)
        if prompt_id in hist:
            status = hist[prompt_id].get("status", {}).get("status_str")
            print("status", status)
            print(json.dumps(hist[prompt_id].get("outputs", {}), ensure_ascii=False))
            raise SystemExit(0 if status == "success" else 1)
        time.sleep(10)
    raise SystemExit("timeout waiting for " + prompt_id)


if __name__ == "__main__":
    main()
