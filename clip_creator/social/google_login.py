from clip_creator.conf import LOGGER, GOOGLE_ACCOUNT_NAME
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def login_with_google_account(driver):
    """Logs in to a website using a pre-logged-in Google account."""

    try:
        LOGGER.info(f"Logging in with Google account: {GOOGLE_ACCOUNT_NAME}")
        # Click the "Sign in with Google" button (adjust selector as needed)
        elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'google')]")

        if elements:
            LOGGER.info("Elements containing 'google':")
            for element in elements:
                LOGGER.info(f"- {element.text}")
        google_signin_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@data-e2e='channel-item' and .//div[contains(text(), 'Continue with Google')]]"))
        )
        google_signin_button.click()
        
        LOGGER.info("Clicked the 'Sign in with Google' button.")
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2)) #Wait for 2 windows to be present
        LOGGER.info("Waiting for Google account selection screen...")
        original_window = driver.current_window_handle
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break
        # Wait for the Google account selection screen
        # account_selection = WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located((By.ID, "identifierId")) #or another unique element on the account selection page
        # )
        
        # Find and click the desired Google account
        div_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[@data-identifier='{GOOGLE_ACCOUNT_NAME}']"))
        )
        div_element.click()
        LOGGER.info(f"Selected Google account: {GOOGLE_ACCOUNT_NAME}")
        driver.switch_to.window(original_window)
    except TimeoutException:
        print("Login timed out.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        #driver.quit() #Remove this line if you want the browser to remain open.
        pass

