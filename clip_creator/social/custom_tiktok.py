import os
import time
from datetime import datetime
from clip_creator.conf import CHROME_USER_PATH, LOGGER
from clip_creator.social.google_login import login_with_google_account
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def upload_video(video_path: str, schedule: datetime | None = None, description: str = "", submit: bool = False):
    """
    Uploads a video to TikTok using the TikTok API.

    Args:
        video_path: The path to the video file.
        title: The title of the video.
        
        schedule: The scheduled date and time for the video (optional).

    Returns:
        A dictionary containing the API response, or None if an error occurs.  Prints error details to console.
    """
    chrome_options = webdriver.ChromeOptions()
    LOGGER.info("user-data-dir: %s" , CHROME_USER_PATH)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument(f"--user-data-dir={CHROME_USER_PATH}")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    actual_user_data_dir = driver.capabilities.get("userDataDir")
    LOGGER.info(actual_user_data_dir)
    try:
        driver.get("https://www.tiktok.com/tiktokstudio/upload?from=webapp")
        #time.sleep(120)
        LOGGER.info("Navigated to TikTok Studio upload page successfully.")
        if check_google_continue_button(driver):
            login_with_google_account(driver=driver)
            
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file' and @accept='video/*']"))
        )

        # Send the file path to the input element
        # Ensure the file exists
        if os.path.exists(video_path):
            file_input.send_keys(video_path)
            LOGGER.info(f"File uploaded successfully: {video_path}")
        else:
            LOGGER.error(f"File not found: {video_path}")
            return None
        set_draftjs_text(driver, description)
        if schedule:
            # Select the "Schedule" radio option
            span_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[@class='Radio__innerCircle Radio__innerCircle--checked-false Radio__innerCircle--disabled-false']"))
            )
            span_element.click()
            LOGGER.info("Selected the 'Schedule' option.")
            # Allow access to save the video
            allow_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//div[contains(text(), 'Allow')]]"))
            )
            allow_button.click()
            # Set the scheduled date and time
            input_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "TUXTextInputCore-input"))
            )

            # Clear the existing value
            input_element.clear()

            # Format the date and time as HH:MM 24-hour format"
            new_time = schedule.strftime("%H:%M")
            # Send the new time
            input_element.send_keys(new_time)
            
            input_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "TUXTextInputCore-input"))
            )

            # Clear the existing value
            input_element.clear()
            # Format the date as MM/DD/YYYY
            new_date = schedule.strftime("%Y-%m-%d")
            # Send the new date
            input_element.send_keys(new_date)
            LOGGER.info(f"Set scheduled date and time: {schedule}")
            if submit:
                # Click the "Schedule" button
                schedule_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[.//div[contains(text(), 'Schedule')]]"))
                )
                schedule_button.click()
        elif submit:
            # Click the "Post" button
            post_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//div[contains(text(), 'Post')]]"))
            )
            post_button.click()
            
        # Additional automation steps for uploading the video can be added here.
        return {"status": "success", "message": "Opened TikTok upload page."}
    except Exception as e:
        LOGGER.error(f"Failed to open TikTok upload page: {e}")
        return None
    finally:
        driver.quit()
def check_google_continue_button(driver):
    """Checks for the 'Continue with Google' button on a webpage."""
    try:

        # Wait for the element to be present
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@style='font-size: 15px;'][contains(text(), 'Continue with Google')]"))
        )
        print("Element 'Continue with Google' found!")
        return True #element was found

    except TimeoutException:
        print("Element 'Continue with Google' not found within the timeout.")
        return False #element was not found

    except Exception as e:
        print(f"An error occurred: {e}")
        return False #error occurred

    finally:
        driver.quit()
        
def set_draftjs_text(driver, new_text):
    """Sets text in a Draft.js editor."""

    try:
        editor_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "public-DraftEditor-content"))
        )

        # Clear existing text using JavaScript
        driver.execute_script("""
            const editor = arguments[0];
            editor.innerHTML = '<div data-contents="true"><div class="" data-block="true" data-editor="2udup" data-offset-key="5rs50-0-0"><div data-offset-key="5rs50-0-0" class="public-DraftStyleDefault-block public-DraftStyleDefault-ltr"><span data-offset-key="5rs50-0-0"><span data-text="true"></span></span></div></div></div>';
        """, editor_element)

        # Set the new text using JavaScript
        driver.execute_script("""
            const editor = arguments[0];
            const newText = arguments[1];
            editor.querySelector('span[data-text="true"]').textContent = newText;
        """, editor_element, new_text)

        print(f"Text set to: {new_text}")

    except Exception as e:
        print(f"An error occurred: {e}")

    
if __name__ == "__main__":
    upload_video("/Users/jonathanstoff/Downloads/B0RXp2A_Wv0.mp4", datetime(2025, 2, 23, 12, 0), "Check out this cool video!")
    