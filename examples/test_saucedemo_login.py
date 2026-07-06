"""Reference Playwright test the agent is taught to imitate.

This is a hand-written "gold standard" against the public demo site
saucedemo.com. It shows the exact style ForgeQA should produce: role/label
locators, web-first expect() assertions, no sleeps.

Run it:
    playwright install chromium      # once
    pytest examples/test_saucedemo_login.py --headed   # watch it, or drop --headed
"""

import re

from playwright.sync_api import Page, expect

BASE_URL = "https://www.saucedemo.com"


def test_valid_login_shows_products(page: Page) -> None:
    """A standard user logs in and lands on the Products page."""
    page.goto(BASE_URL)

    page.get_by_placeholder("Username").fill("standard_user")
    page.get_by_placeholder("Password").fill("secret_sauce")
    page.get_by_role("button", name="Login").click()

    # Web-first assertions: Playwright auto-waits, no sleeps needed.
    expect(page).to_have_url(re.compile(r".*inventory\.html"))
    expect(page.get_by_text("Products")).to_be_visible()


def test_locked_out_user_sees_error(page: Page) -> None:
    """A locked-out user is blocked and shown a clear error message."""
    page.goto(BASE_URL)

    page.get_by_placeholder("Username").fill("locked_out_user")
    page.get_by_placeholder("Password").fill("secret_sauce")
    page.get_by_role("button", name="Login").click()

    expect(page.get_by_text(re.compile("locked out", re.IGNORECASE))).to_be_visible()
