import contextlib
import functools
import http.client
import importlib.util
import io
import ssl
import sys
import tempfile
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"

spec = importlib.util.spec_from_file_location(
    "check_staging", ROOT / "scripts" / "check_staging.py"
)
check_staging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_staging)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


class TruncatingHandler(QuietHandler):
    """Promises a long body, sends a few bytes, then drops the connection."""

    def do_GET(self):
        if self.server.truncations_left > 0:
            self.server.truncations_left -= 1
            self.send_response(200)
            self.send_header("Content-Length", "500")
            self.end_headers()
            self.wfile.write(b"<html>")
            return

        super().do_GET()


@contextlib.contextmanager
def serve(directory, handler_class=QuietHandler, **server_attributes):
    handler = functools.partial(handler_class, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)

    for name, value in server_attributes.items():
        setattr(server, name, value)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def write_site(directory, index, css, js):
    """Write a fake site; a value of None leaves that file missing."""
    directory = Path(directory)

    for relative_path, content in (
        ("index.html", index),
        ("css/style.css", css),
        ("js/app.js", js),
    ):
        if content is None:
            continue

        target = directory / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


GOOD_INDEX = "<html><head><title>FinalTake</title></head></html>"
GOOD_CSS = "body { margin: 0; }"
GOOD_JS = "const API_BASE_URL = '';"


class VerifySiteTests(unittest.TestCase):

    def test_passes_against_the_real_frontend(self):
        output = io.StringIO()

        with serve(FRONTEND) as base_url:
            with contextlib.redirect_stdout(output):
                check_staging.verify_site(base_url)

        for path in ("index.html", "css/style.css", "js/app.js"):
            with self.subTest(path=path):
                self.assertIn(f"PASS: {base_url}{path}", output.getvalue())

    def test_missing_file_raises_http_error(self):
        with tempfile.TemporaryDirectory() as directory:
            write_site(directory, GOOD_INDEX, None, GOOD_JS)

            with serve(directory) as base_url:
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(HTTPError) as context:
                        check_staging.verify_site(base_url)

        self.assertEqual(context.exception.code, 404)

    def test_wrong_homepage_content_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            write_site(directory, "<title>Other</title>", GOOD_CSS, GOOD_JS)

            with serve(directory) as base_url:
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(
                        RuntimeError, "Expected content not found"
                    ):
                        check_staging.verify_site(base_url)

    def test_wrong_javascript_content_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            write_site(directory, GOOD_INDEX, GOOD_CSS, "console.log(1);")

            with serve(directory) as base_url:
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(
                        RuntimeError, "Expected content not found"
                    ):
                        check_staging.verify_site(base_url)

    def test_empty_stylesheet_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            write_site(directory, GOOD_INDEX, "  \n", GOOD_JS)

            with serve(directory) as base_url:
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(
                        RuntimeError, "Empty response"
                    ):
                        check_staging.verify_site(base_url)


class MainTests(unittest.TestCase):

    def run_main(self, *arguments):
        stdout = io.StringIO()
        stderr = io.StringIO()

        with patch.object(sys, "argv", ["check_staging.py", *arguments]):
            with contextlib.redirect_stdout(stdout):
                with contextlib.redirect_stderr(stderr):
                    result = check_staging.main()

        return result, stdout.getvalue(), stderr.getvalue()

    def test_url_argument_is_required(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with patch.object(sys, "argv", ["check_staging.py"]):
                with self.assertRaises(SystemExit) as context:
                    check_staging.main()

        self.assertEqual(context.exception.code, 2)

    def test_non_https_url_is_rejected(self):
        for url in ("http://example.com/", "example.com", "https://"):
            with self.subTest(url=url):
                with patch.object(check_staging, "verify_site") as verify:
                    with contextlib.redirect_stderr(io.StringIO()):
                        with patch.object(
                            sys, "argv", ["check_staging.py", "--url", url]
                        ):
                            with self.assertRaises(SystemExit) as context:
                                check_staging.main()

                self.assertEqual(context.exception.code, 2)
                verify.assert_not_called()

    def test_success_does_not_retry(self):
        with patch.object(check_staging, "verify_site") as verify:
            with patch.object(check_staging.time, "sleep") as sleep:
                result, stdout, _ = self.run_main(
                    "--url", "https://example.github.io/FinalTake"
                )

        self.assertEqual(result, 0)
        self.assertIn("Staging smoke test PASSED", stdout)
        verify.assert_called_once_with(
            "https://example.github.io/FinalTake/"
        )
        sleep.assert_not_called()

    def test_transient_failures_are_retried_until_success(self):
        failures = [
            HTTPError("https://x/", 404, "Not Found", {}, None),
            URLError("temporary failure"),
            TimeoutError("timed out"),
            RuntimeError("Expected content not found"),
            None,
        ]

        with patch.object(
            check_staging, "verify_site", side_effect=failures
        ) as verify:
            with patch.object(check_staging.time, "sleep") as sleep:
                result, stdout, _ = self.run_main(
                    "--url", "https://example.github.io/FinalTake/"
                )

        self.assertEqual(result, 0)
        self.assertEqual(verify.call_count, 5)
        self.assertEqual(sleep.call_count, 4)
        sleep.assert_called_with(10)
        self.assertIn("Staging smoke test PASSED", stdout)

    def test_persistent_failure_fails_after_six_attempts(self):
        with patch.object(
            check_staging,
            "verify_site",
            side_effect=RuntimeError("still failing"),
        ) as verify:
            with patch.object(check_staging.time, "sleep") as sleep:
                result, stdout, stderr = self.run_main(
                    "--url", "https://example.github.io/FinalTake/"
                )

        self.assertEqual(result, 1)
        self.assertEqual(verify.call_count, 6)
        self.assertEqual(sleep.call_count, 5)
        self.assertIn("Staging verification attempt 6/6", stdout)
        self.assertIn("Attempt failed: still failing", stdout)
        self.assertIn("Staging smoke test FAILED", stderr)


class FakeResponse:
    status = 200

    def __init__(self, body=b"", error=None):
        self.body = body
        self.error = error

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def read(self):
        if self.error is not None:
            raise self.error

        return self.body


STAGING_URL = "https://staging.example.test/FinalTake/"

NETWORK_ERRORS = (
    ConnectionResetError("connection reset by peer"),
    ConnectionAbortedError("connection aborted"),
    BrokenPipeError("broken pipe"),
    ssl.SSLError("tls failure"),
    ssl.SSLEOFError("unexpected eof"),
    http.client.IncompleteRead(b"<html>", 494),
    http.client.RemoteDisconnected("remote end closed connection"),
    http.client.BadStatusLine("garbage"),
    http.client.HTTPException("protocol error"),
    OSError("generic network failure"),
)


class NetworkErrorHandlingTests(unittest.TestCase):

    def run_main(self, url=STAGING_URL):
        stdout = io.StringIO()
        stderr = io.StringIO()

        with patch.object(sys, "argv", ["check_staging.py", "--url", url]):
            with contextlib.redirect_stdout(stdout):
                with contextlib.redirect_stderr(stderr):
                    result = check_staging.main()

        return result, stdout.getvalue(), stderr.getvalue()

    def test_each_network_error_triggers_a_retry(self):
        for error in NETWORK_ERRORS:
            with self.subTest(error=type(error).__name__):
                with patch.object(
                    check_staging, "verify_site", side_effect=[error, None]
                ) as verify:
                    with patch.object(check_staging.time, "sleep") as sleep:
                        result, stdout, _ = self.run_main()

                self.assertEqual(result, 0)
                self.assertEqual(verify.call_count, 2)
                sleep.assert_called_once_with(10)
                self.assertIn("Attempt failed:", stdout)
                self.assertIn("Staging smoke test PASSED", stdout)

    def test_persistent_network_errors_fail_after_six_attempts(self):
        for error in (
            ConnectionResetError("connection reset by peer"),
            ssl.SSLError("tls failure"),
            http.client.IncompleteRead(b"<html>", 494),
        ):
            with self.subTest(error=type(error).__name__):
                with patch.object(
                    check_staging, "verify_site", side_effect=error
                ) as verify:
                    with patch.object(check_staging.time, "sleep") as sleep:
                        result, _, stderr = self.run_main()

                self.assertEqual(result, 1)
                self.assertEqual(verify.call_count, 6)
                self.assertEqual(sleep.call_count, 5)
                self.assertIn("Staging smoke test FAILED", stderr)

    def test_connection_reset_while_reading_body_is_retried(self):
        bodies = {
            "index.html": GOOD_INDEX,
            "css/style.css": GOOD_CSS,
            "js/app.js": GOOD_JS,
        }
        calls = []

        def fake_urlopen(request, timeout):
            calls.append(request.full_url)

            if len(calls) == 1:
                return FakeResponse(
                    error=ConnectionResetError("reset while reading")
                )

            for path, body in bodies.items():
                if request.full_url.endswith(path):
                    return FakeResponse(body.encode("utf-8"))

            raise AssertionError(f"Unexpected URL: {request.full_url}")

        with patch.object(check_staging, "urlopen", fake_urlopen):
            with patch.object(check_staging.time, "sleep") as sleep:
                result, stdout, _ = self.run_main()

        self.assertEqual(result, 0)
        self.assertEqual(len(calls), 4)
        sleep.assert_called_once_with(10)
        self.assertIn("Attempt failed: reset while reading", stdout)
        self.assertIn("Staging smoke test PASSED", stdout)

    def test_tls_failure_on_every_request_fails_the_smoke_test(self):
        with patch.object(
            check_staging, "urlopen", side_effect=ssl.SSLError("tls failure")
        ) as fake_urlopen:
            with patch.object(check_staging.time, "sleep") as sleep:
                result, _, stderr = self.run_main()

        self.assertEqual(result, 1)
        self.assertEqual(fake_urlopen.call_count, 6)
        self.assertEqual(sleep.call_count, 5)
        self.assertIn("Staging smoke test FAILED", stderr)

    def test_truncated_response_from_a_real_server_is_retried(self):
        with serve(
            FRONTEND, TruncatingHandler, truncations_left=1
        ) as local_url:

            def route_to_local_server(request, timeout):
                local_request = Request(
                    request.full_url.replace(STAGING_URL, local_url),
                    headers=dict(request.header_items()),
                )
                return urlopen(local_request, timeout=timeout)

            with patch.object(check_staging, "urlopen", route_to_local_server):
                with patch.object(check_staging.time, "sleep") as sleep:
                    result, stdout, _ = self.run_main()

        self.assertEqual(result, 0)
        sleep.assert_called_once_with(10)
        self.assertIn("Attempt failed: IncompleteRead", stdout)
        self.assertIn("Staging smoke test PASSED", stdout)

    def test_unexpected_programming_errors_are_not_swallowed(self):
        with patch.object(
            check_staging, "verify_site", side_effect=ValueError("bug")
        ):
            with patch.object(check_staging.time, "sleep") as sleep:
                with self.assertRaises(ValueError):
                    self.run_main()

        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
