#!/usr/bin/env python3
"""Post-deployment smoke test for FinalTake's static staging site."""

import argparse
import sys
import time
from http.client import HTTPException
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

# OSError covers URLError/HTTPError, SSL errors, timeouts and connection
# resets; HTTPException covers protocol errors such as truncated responses.
RETRYABLE_ERRORS = (RuntimeError, OSError, HTTPException)


def fetch(url):
    request = Request(
        url,
        headers={"User-Agent": "FinalTake-Staging-Smoke-Test/1.0"},
    )
    with urlopen(request, timeout=15) as response:
        if response.status != 200:
            raise RuntimeError(
                f"Unexpected HTTP status {response.status}: {url}"
            )
        return response.read().decode("utf-8", errors="replace")


def verify_site(base_url):
    checks = {
        "index.html": "<title>FinalTake</title>",
        "css/style.css": None,
        "js/app.js": "API_BASE_URL",
    }

    for path, expected_text in checks.items():
        url = urljoin(base_url, path)
        content = fetch(url)

        if not content.strip():
            raise RuntimeError(f"Empty response: {url}")

        if expected_text and expected_text not in content:
            raise RuntimeError(
                f"Expected content not found: {url}"
            )

        print(f"PASS: {url}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        required=True,
        help="GitHub Pages deployment URL",
    )
    args = parser.parse_args()

    parsed = urlparse(args.url)
    if parsed.scheme != "https" or not parsed.netloc:
        parser.error("A valid HTTPS deployment URL is required")

    base_url = args.url.rstrip("/") + "/"

    for attempt in range(1, 7):
        print(f"Staging verification attempt {attempt}/6", flush=True)

        try:
            verify_site(base_url)
            print("Staging smoke test PASSED", flush=True)
            return 0
        except RETRYABLE_ERRORS as exc:
            print(f"Attempt failed: {exc}", flush=True)

        if attempt < 6:
            time.sleep(10)

    print("Staging smoke test FAILED", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
