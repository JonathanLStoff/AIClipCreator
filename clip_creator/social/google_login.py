import traceback

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from clip_creator.conf import GOOGLE_ACCOUNT_NAME, LOGGER


def login_with_google_account(driver, element_goog):
    """Logs in to a website using a pre-logged-in Google account."""

    try:
        LOGGER.info(f"Logging in with Google account: {GOOGLE_ACCOUNT_NAME}")
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    (
                        "//div[@style='font-size: 15px;'][contains(text(), 'Continue"
                        " with Google')]"
                    ),
                )
            )
        )
        parent_element = element.find_element(By.XPATH, "..")
        LOGGER.info(f"Parent element: {parent_element.tag_name}")
        parent_element.click()

        LOGGER.info("Clicked the 'Sign in with Google' button.")
        screens = driver.window_handles
        LOGGER.info(f"Number of screens: {len(screens)}")
        original_window = driver.current_window_handle
        for screen in screens:
            driver.switch_to.window(screen)
            LOGGER.info(f"Screen title: {driver.title}")
            if "google" in str(driver.title).lower():
                break
            elif "tiktok" in str(driver.title).lower():
                original_window = screen
        div_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//div[@data-identifier='{GOOGLE_ACCOUNT_NAME}']")
            )
        )
        div_element.click()
        # time.sleep(15)
        continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[jsname='LgbsSe'] span[jsname='V67aGc']")
            )
        )
        continue_button.click()
        # time.sleep(15)
        LOGGER.info(f"Selected Google account: {GOOGLE_ACCOUNT_NAME}")
        driver.switch_to.window(original_window)
    except TimeoutException:
        LOGGER.error("Login timed out. %s", traceback.format_exc())
    except Exception as e:
        LOGGER.error(f"Error logging in with Google account: {e}")
        LOGGER.error(traceback.format_exc())
