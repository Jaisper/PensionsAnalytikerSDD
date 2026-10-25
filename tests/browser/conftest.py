"""Browsertests af den byggede side (feature 005). Kræver `scripts/byg_side.py` og Playwright.

Køres med `uv run pytest -m browser`. Uden _site/ eller browser springes de over.
"""
import functools
import http.server
import threading
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[2] / "_site"


@pytest.fixture(scope="session")
def base_url():
    if not (SITE / "index.html").exists():
        pytest.skip("Byg siden først: uv run python scripts/byg_side.py")
    class Stille(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    handler = functools.partial(Stille, directory=str(SITE))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/"
    server.shutdown()


@pytest.fixture(scope="session")
def browser():
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome")  # lokalt: installeret Chrome
        except Exception:
            try:
                b = p.chromium.launch()  # CI: playwright install chromium
            except Exception as e:
                pytest.skip(f"Ingen browser: {e}")
        yield b
        b.close()


@pytest.fixture
def side(browser, base_url):
    """Siden indlæst med motoren klar. Alle requests (også fra workeren) logges i side.requests."""
    ctx = browser.new_context(locale="da-DK")
    page = ctx.new_page()
    page.requests = []
    page.fejl = []
    ctx.on("request", lambda r: page.requests.append((r.method, r.url)))
    page.on("pageerror", lambda e: page.fejl.append(str(e)))
    page.goto(base_url)
    page.evaluate("motorKlar")
    yield page
    ctx.close()


@pytest.fixture
def ny_side(browser, base_url):
    """En tom side, som testen selv indlæser (fx med forsinket eller blokeret motor)."""
    ctx = browser.new_context(locale="da-DK")
    page = ctx.new_page()
    page.fejl = []
    page.on("pageerror", lambda e: page.fejl.append(str(e)))
    page.base_url = base_url
    yield page
    ctx.close()
