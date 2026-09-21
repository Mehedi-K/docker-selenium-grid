"""Pytest fixtures for the Selenium Grid smoke-test suite.

These tests don't start a browser themselves - they create a
RemoteWebDriver session against a Selenium Grid hub (the docker-compose
stack in this repo, or any other Grid that speaks the WebDriver wire
protocol). That's the whole point of the suite: prove the grid can
accept sessions and actually drive a browser end-to-end.
"""

import os
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

SELENIUM_REMOTE_URL = os.environ.get("SELENIUM_REMOTE_URL", "http://localhost:4444/wd/hub")
BROWSER = os.environ.get("BROWSER", "chrome").lower()

SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"


def _build_options():
    if BROWSER == "firefox":
        options = FirefoxOptions()
    else:
        options = ChromeOptions()
        options.add_argument("--window-size=1280,1024")

    # Sensible defaults for running headless browser containers in CI.
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return options


@pytest.fixture
def driver():
    options = _build_options()
    remote_driver = webdriver.Remote(command_executor=SELENIUM_REMOTE_URL, options=options)
    remote_driver.implicitly_wait(5)
    yield remote_driver
    remote_driver.quit()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """On failure, save a screenshot from the `driver` fixture for CI artifacts."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        driver_fixture = item.funcargs.get("driver")
        if driver_fixture is not None:
            SCREENSHOTS_DIR.mkdir(exist_ok=True)
            safe_name = item.name.replace("/", "_")
            screenshot_path = SCREENSHOTS_DIR / f"{safe_name}.png"
            try:
                driver_fixture.save_screenshot(str(screenshot_path))
            except Exception:
                pass
