"""FinalTake console demo.

Shows, live in the console and in order:
  1. A feature / use case  - rate, review, favorite and comment on a movie.
  2. A test                - real unit tests, streamed line by line.
  3. A CI/CD feature       - the CI pipeline (.github/workflows/ci.yml) executed
                             step by step locally, with real commands.

Run from the repository root:
    python demo\\console_demo.py                (pauses between sections)
    python demo\\console_demo.py --no-pause
    python demo\\console_demo.py --full         (also runs the ~40s backend suite)
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.comment import Comment  # noqa: E402
from backend.favorite import Favorites  # noqa: E402
from backend.rating import Rating  # noqa: E402
from backend.review import Review  # noqa: E402

PAUSE = "--no-pause" not in sys.argv and sys.stdin is not None and sys.stdin.isatty()
FULL = "--full" in sys.argv
BEAT = 0.4 if PAUSE else 0.1


def banner(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70, flush=True)


def step(text):
    time.sleep(BEAT)
    print(f"\n>> {text}", flush=True)


def pause(message="\n[Press Enter to continue]"):
    global PAUSE
    if PAUSE:
        try:
            input(message)
        except EOFError:
            PAUSE = False


def expect_error(label, action):
    try:
        action()
    except (ValueError, PermissionError) as error:
        print(f"   REJECTED  {label}: {error}", flush=True)
    else:
        print(f"   !! {label} was unexpectedly accepted", flush=True)


def run_command(command, cwd=ROOT, env=None):
    """Run a command, streaming its output live. Returns True on success."""
    print(f"   $ {' '.join(command)}", flush=True)
    started = time.time()
    process = subprocess.Popen(
        command, cwd=cwd, env={**os.environ, **(env or {})},
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    for line in process.stdout:
        print(f"     | {line.rstrip()}", flush=True)
    ok = process.wait() == 0
    print(f"   {'PASS' if ok else 'FAIL'} ({time.time() - started:.1f}s)", flush=True)
    return ok


def demo_feature():
    banner("PART 1 - USE CASE: Rate, review, favorite and comment on media")
    print("Requirement: a signed-in user can rate media (0.5-5.0 stars), write a")
    print("review, save favorites and discuss reviews; only owners can edit them.")

    alice, bob, media_id, title = 1, 2, 101, "Interstellar"

    step(f"Alice rates '{title}'")
    rating = Rating(alice, media_id)
    rating.set_rating(4.5)
    print(f"   Rating saved: {rating.value}/5.0")
    expect_error("rating 3.7 (not a half-star step)", lambda: rating.set_rating(3.7))
    expect_error("rating 5.5 (above maximum)", lambda: rating.set_rating(5.5))

    step("Alice writes a review")
    review = Review(alice, media_id, rating.value,
                    "  Stunning visuals and a great score.  ")
    print(f"   Review: {review.to_dict()}")
    expect_error("empty review", lambda: Review(alice, media_id, 4.5, "   "))

    step("Alice adds the movie to her favorites")
    favorites = Favorites(alice)
    print(f"   Added: {favorites.add_favorite(media_id)}")
    print(f"   Added again (duplicate): {favorites.add_favorite(media_id)}")
    print(f"   Favorites: {favorites.get_favorites()}")

    step("Bob comments on Alice's review")
    comment = Comment(bob, review_id=1, text="Totally agree, the soundtrack is amazing!")
    print(f"   Comment: {comment.to_dict()}")

    step("Authorization: only owners can modify their content")
    expect_error("Bob editing Alice's review",
                 lambda: review.edit_review(bob, "Hacked"))
    expect_error("Alice editing Bob's comment",
                 lambda: comment.edit_comment(alice, "Hacked"))
    review.edit_review(alice, "Stunning visuals, great score, emotional story.")
    print(f"   Alice edited her own review: {review.text!r}")

    step("Cleanup: owners delete their content")
    comment.delete_comment(bob)
    review.delete_review(alice)
    rating.delete_rating()
    print(f"   comment={comment.to_dict()}  review={review.to_dict()}  rating={rating.value}")


def demo_tests():
    banner("PART 2 - TEST: Running the unit tests live")
    step("Rating, review, favorite and comment unit tests")
    return run_command([
        sys.executable, "-m", "unittest", "-v",
        "tests.test_rating", "tests.test_review",
        "tests.test_favorite", "tests.test_comment",
    ])


def git_output(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def package_application(build_version):
    excluded = ("backend/venv/", "backend/__pycache__/", ".DS_Store")
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / f"{build_version}.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in ("backend", "frontend", "README.md"):
                path = ROOT / item
                for file in ([path] if path.is_file() else sorted(path.rglob("*"))):
                    rel = file.relative_to(ROOT).as_posix()
                    if file.is_file() and not any(x in rel for x in excluded):
                        print(f"     | adding: {rel}", flush=True)
                        zf.write(file, rel)
        print(f"   Created {archive.name} ({archive.stat().st_size / 1024:.1f} KB)")
    print("   Uploading artifact (in CI: actions/upload-artifact@v4) -> "
          f"{build_version}")
    return True


def validate_frontend_files():
    ok = True
    for name in ("index.html", "pages/login.html", "pages/signup.html",
                 "css/style.css", "js/app.js"):
        exists = (ROOT / "frontend" / name).is_file()
        ok &= exists
        print(f"     | {'found  ' if exists else 'MISSING'} frontend/{name}", flush=True)
    return ok


def node_step(args):
    if not shutil.which("node"):
        print("   SKIPPED: node is not installed on this machine "
              f"(CI runs: node {' '.join(args)})")
        return None
    return run_command(["node", *args])


def demo_cicd():
    banner("PART 3 - CI/CD: Running the pipeline from .github/workflows/ci.yml")
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    branches = ", ".join(sorted(set(re.findall(r"branches: \[(.*?)\]", workflow))))
    print(f"Trigger: push / pull request on '{branches}' (simulated locally)")

    results = []
    build = {}

    def run_step(index, total, name, action):
        step(f"[{index}/{total}] {name}")
        ok = action()
        results.append((name, ok))
        return ok

    def checkout():
        print(f"   Commit {git_output('rev-parse', '--short', 'HEAD')} on branch "
              f"{git_output('rev-parse', '--abbrev-ref', 'HEAD')}")
        return True

    def build_version():
        sha = git_output("rev-parse", "HEAD")[:7]
        build["version"] = f"build-1-{sha}"
        print(f"   Build version: {build['version']}  (build-<run number>-<short sha>)")
        return True

    backend_steps = [
        ("Check out repository", checkout),
        ("Set up Python", lambda: run_command([sys.executable, "--version"])),
        ("Generate build version", build_version),
        ("Install dependencies", lambda: run_command(
            [sys.executable, "-m", "pip", "install", "-q",
             "--disable-pip-version-check", "-r", "backend/requirements.txt"])),
        ("Run backend tests", lambda: run_command(
            [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p",
             "test_*.py"], cwd=ROOT / "backend") if FULL else
            print("   SKIPPED for speed (~40s); use --full to run")),
        ("Run repository tests", lambda: run_command(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p",
             "test_*.py"])),
        ("Package application", lambda: package_application(build["version"])),
    ]

    print("\n--- JOB: backend-tests ---")
    for i, (name, action) in enumerate(backend_steps, 1):
        run_step(i, len(backend_steps), name, action)

    frontend_steps = [
        ("Validate frontend files", validate_frontend_files),
        ("Validate search JavaScript syntax",
         lambda: node_step(["--check", "frontend/js/app.js"])),
        ("Run frontend API recovery integration test",
         lambda: node_step(["--test", "tests/search_integration.test.mjs"])),
        ("Run media details regression tests",
         lambda: node_step(["--test", "tests/media_details.test.mjs"])),
    ]

    print("\n--- JOB: frontend-validation ---")
    for i, (name, action) in enumerate(frontend_steps, 1):
        run_step(i, len(frontend_steps), name, action)

    step("Pipeline summary")
    for name, ok in results:
        status = "SKIP" if ok is None else "PASS" if ok else "FAIL"
        print(f"   [{status}] {name}")
    return all(ok is not False for _, ok in results)


def main():
    print("FinalTake - Console Demo")
    demo_feature()
    pause()
    tests_ok = demo_tests()
    pause()
    ci_ok = demo_cicd()
    banner("DEMO COMPLETE: use case shown, tests run, CI/CD pipeline run")
    pause("\n[Press Enter to close]")
    return 0 if tests_ok and ci_ok else 1


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
