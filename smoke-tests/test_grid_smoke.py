"""End-to-end smoke tests that prove the Selenium Grid works.

Each test opens a real browser session through the grid's RemoteWebDriver
endpoint and drives it against https://the-internet.herokuapp.com/, a
small public site built for exercising exactly this kind of UI automation.
If these pass, the grid is correctly routing sessions to browser nodes.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

BASE_URL = "https://the-internet.herokuapp.com"


def test_homepage_loads(driver):
    driver.get(BASE_URL)
    assert "The Internet" in driver.title
    heading = driver.find_element(By.CSS_SELECTOR, "h1.heading")
    assert "Welcome to the-internet" in heading.text


def test_login_with_valid_credentials_succeeds(driver):
    driver.get(f"{BASE_URL}/login")
    driver.find_element(By.ID, "username").send_keys("tomsmith")
    driver.find_element(By.ID, "password").send_keys("SuperSecretPassword!")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    flash = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "flash")))
    assert "You logged into a secure area" in flash.text
    assert "/secure" in driver.current_url


def test_login_with_invalid_credentials_shows_error(driver):
    driver.get(f"{BASE_URL}/login")
    driver.find_element(By.ID, "username").send_keys("not-a-real-user")
    driver.find_element(By.ID, "password").send_keys("wrong-password")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    flash = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "flash")))
    assert "Your username is invalid" in flash.text


def test_checkboxes_toggle_state(driver):
    driver.get(f"{BASE_URL}/checkboxes")
    checkboxes = driver.find_elements(By.CSS_SELECTOR, "#checkboxes input[type='checkbox']")
    assert len(checkboxes) == 2

    first_checkbox = checkboxes[0]
    was_checked = first_checkbox.is_selected()
    first_checkbox.click()
    assert first_checkbox.is_selected() is not was_checked


def test_dropdown_select_option(driver):
    driver.get(f"{BASE_URL}/dropdown")
    dropdown = Select(driver.find_element(By.ID, "dropdown"))

    dropdown.select_by_value("2")
    assert dropdown.first_selected_option.text == "Option 2"


def test_dynamic_loading_element_eventually_appears(driver):
    driver.get(f"{BASE_URL}/dynamic_loading/1")
    driver.find_element(By.CSS_SELECTOR, "#start button").click()

    finish_text = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "finish"))
    )
    assert "Hello World!" in finish_text.text
