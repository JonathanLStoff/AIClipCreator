import math
import os
import time
import traceback
from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

from clip_creator.conf import CHROME_USER_PATH, CONFIG, LOGGER
from clip_creator.social.google_login import login_with_google_account


def upload_video_tt(
    video_path: str,
    schedule: datetime | None = None,
    description: str = "",
    submit: bool = False,
    save_draft: bool = False,
):
    """
    Uploads a video to TikTok using the TikTok API.

    Args:
        video_path: The path to the video file.
        title: The title of the video.

        schedule: The scheduled time for the video (optional).

    Returns:
        A dictionary containing the API response, or None if an error occurs.  Prints error details to console.
    """
    chrome_options = webdriver.ChromeOptions()
    LOGGER.info("user-data-dir: %s", CHROME_USER_PATH)
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"
    )
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument(f"--user-data-dir={CHROME_USER_PATH}")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    actual_user_data_dir = driver.capabilities.get("userDataDir")

    wait = WebDriverWait(driver, 60)
    LOGGER.info(actual_user_data_dir)
    try:
        driver.get("https://www.tiktok.com/tiktokstudio/upload?from=webapp")
        LOGGER.info("Navigated to TikTok Studio upload page successfully.")
        element_goog = check_google_continue_button(driver)
        if element_goog:
            login_with_google_account(driver=driver, element_goog=element_goog)

        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@type='file' and @accept='video/*']")
            )
        )

        # Send the file path to the input element
        # Ensure the file exists
        if os.path.exists(video_path):
            file_input.send_keys(video_path)
            LOGGER.info(f"File uploaded successfully: {video_path}")
        else:
            LOGGER.error(f"File not found: {video_path}")
            return None
        set_draftjs_text(driver, description, wait)
        edit_video_tt_mus(driver)
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//*[contains(@class, 'suggest-item') and contains(text(), 'States')]")
                )
            )
            element.click()
        except Exception as e:
            LOGGER.error(f"Failed to click the Location: {e}")
        if schedule:
            # Select the "Schedule" radio option
            span_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        (
                            "//span[@class='Radio__innerCircle"
                            " Radio__innerCircle--checked-false"
                            " Radio__innerCircle--disabled-false']"
                        ),
                    )
                )
            )
            span_element.click()
            LOGGER.info("Selected the 'Schedule' option.")
            _set_schedule_video(driver, schedule)
            if submit:
                
                schedule_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[.//div[contains(text(), 'Schedule')]]")
                    )
                )
                schedule_button.click()
            else:
                if save_draft:
                    draft_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                "//*[contains(@class, 'Button__content') and contains(@class, 'Button__content--shape-default') "
                                "and contains(@class, 'Button__content--size-large') and contains(@class, 'Button__content--type-neutral') "
                                "and contains(@class, 'Button__content--loading-false') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'draft')]"
                            )
                        )
                    )
                    draft_button.click()
                    LOGGER.info("Clicked the 'draft' button successfully.")
                time.sleep(600)
        elif submit:

            time.sleep(5)
            post_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//div[contains(text(), 'Post')]]")
                )
            )
            post_button.click()
        else:
            if save_draft:
                draft_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//*[contains(@class, 'Button__content') and contains(@class, 'Button__content--shape-default') "
                            "and contains(@class, 'Button__content--size-large') and contains(@class, 'Button__content--type-neutral') "
                            "and contains(@class, 'Button__content--loading-false') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'draft')]"
                        )
                    )
                )
                draft_button.click()
                LOGGER.info("Clicked the 'draft' button successfully.")
            time.sleep(600)
        time.sleep(10)
        # Additional automation steps for uploading the video can be added here.
        return {"status": "success", "message": "Opened TikTok upload page."}
    except Exception:
        LOGGER.error(f"Failed to open TikTok upload page: {traceback.format_exc()}")
        return None
    finally:
        driver.quit()
def edit_video_tt_mus(driver):
    try:
        wait = WebDriverWait(driver, 10)
        button = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "TUXButton-content"))
        )
        button.click()
        LOGGER.info("Clicked the edit video button successfully.")
        # Hover over the music card operation element
        music_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'music-card-operation')]"))
        )
        ActionChains(driver).move_to_element(music_element).perform()
        LOGGER.info("Hovered over the music element successfully.")
        music_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'music-card-operation')]"))
        )
        music_button.click()
        
        try:
            image_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//img[contains(@src, 'PHN2ZyB3aWR0aD0iMjEi')]")
                )
            )
            image_element.click()
            LOGGER.info("Clicked the image element successfully.")
        except Exception as e:
            LOGGER.error("Failed to click the image element: %s", e)
        range_inputs = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input.scaleInput"))
        )
        range_input = range_inputs[1]  # Get the second input element
        ActionChains(driver).move_to_element(range_input).perform()
        for _ in range(100):
            range_input.send_keys(Keys.LEFT)
        LOGGER.info("Updated range input value without dragging.")
        
        save_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(@class, 'TUXButton-label') and contains(text(), 'Save')]")
            )
        )
        save_button.click()
        LOGGER.info("Clicked the Save button successfully.")
    except Exception as e:
        LOGGER.error("Failed to click the button: %s", e)

def check_google_continue_button(driver):
    """Checks for the 'Continue with Google' button on a webpage."""
    try:
        # Wait for the element to be present
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
        LOGGER.info("Element 'Continue with Google' found!")
        return True  # element was found

    except TimeoutException:
        print("Element 'Continue with Google' not found within the timeout.")
        return False  # element was not found

    except Exception as e:
        print(f"An error occurred: {e}")
        return False  # error occurred


def set_draftjs_text(driver, new_text, wait):
    """Sets text in a Draft.js editor."""
    try:
        editable_div = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@class='notranslate public-DraftEditor-content']")
            )
        )
        # Click the div
        editable_div.click()
        # Type 30 backspaces followed by the new_text
        actions = ActionChains(driver)
        backspaces = 30 * "\b"
        actions.send_keys(backspaces + new_text).perform()
    except Exception as e:
        LOGGER.error(f"An error occurred: {e}")


def _set_schedule_video(driver, schedule: datetime) -> None:
    """
    Sets the schedule of the video

    Parameters
    ----------
    driver : selenium.webdriver
    schedule : datetime.datetime
        The datetime to set
    """

    month = schedule.month
    day = schedule.day
    hour = schedule.hour
    minute = schedule.minute

    try:
        switch = driver.find_element(
            By.XPATH, CONFIG["selectors"]["schedule"]["switch"]
        )
        switch.click()
        scroll_to_timepicker_options(driver, hour, minute)
        return

        click_matching_time_option(driver, hour, "h")
        switch.click()
        switch.click()

        click_matching_time_option(driver, minute, "m")
        return
        __date_picker(driver, month, day)
        __time_picker(driver, hour, minute)
    except Exception as e:
        msg = f"Failed to set schedule: {e}"
        LOGGER.error(msg)


def __date_picker(driver, month: int, day: int) -> None:
    condition = EC.presence_of_element_located(
        (By.XPATH, CONFIG["selectors"]["schedule"]["date_picker"])
    )
    date_picker = WebDriverWait(driver, CONFIG["implicit_wait"]).until(condition)
    date_picker.click()

    condition = EC.presence_of_element_located(
        (By.XPATH, CONFIG["selectors"]["schedule"]["calendar"])
    )
    calendar = WebDriverWait(driver, CONFIG["implicit_wait"]).until(condition)

    calendar_month = driver.find_element(
        By.XPATH, CONFIG["selectors"]["schedule"]["calendar_month"]
    ).text
    n_calendar_month = datetime.strptime(calendar_month, "%B").month
    if n_calendar_month != month:  # Max can be a month before or after
        if n_calendar_month < month:
            arrow = driver.find_elements(
                By.XPATH, CONFIG["selectors"]["schedule"]["calendar_arrows"]
            )[-1]
        else:
            arrow = driver.find_elements(
                By.XPATH, CONFIG["selectors"]["schedule"]["calendar_arrows"]
            )[0]
        arrow.click()
    valid_days = driver.find_elements(
        By.XPATH, CONFIG["selectors"]["schedule"]["calendar_valid_days"]
    )

    day_to_click = None
    for day_option in valid_days:
        if int(day_option.text) == day:
            day_to_click = day_option
            break
    if day_to_click:
        day_to_click.click()
    else:
        raise Exception("Day not found in calendar")


def click_matching_time_option(driver, target_number, min_or_hour):
    """
    Finds time picker options with the specified class, checks if their text matches the
    target number, and clicks the matching option.

    Args:
        driver: The Selenium WebDriver instance.
        target_number: The number to match against the time picker options.
    """
    try:
        wait = WebDriverWait(driver, 10)  # Adjust timeout as needed
        # Wait until the time picker container exists
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, CONFIG["selectors"]["schedule"]["time_picker_container"])
            )
        )
        input_box = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[@class='TUXInputBox']"))
        )

        # Click the input box
        input_box.click()
        if min_or_hour == "h":
            time_options = wait.until(
                EC.presence_of_all_elements_located(
                    (
                        By.XPATH,
                        (
                            "//span[@class='tiktok-timepicker-option-text"
                            " tiktok-timepicker-left']"
                        ),
                    )
                )
            )
        else:
            time_options = wait.until(
                EC.presence_of_all_elements_located(
                    (
                        By.XPATH,
                        (
                            "//span[@class='tiktok-timepicker-option-text"
                            " tiktok-timepicker-right']"
                        ),
                    )
                )
            )
            scroll_timepicker_options(driver)

        for _i, option in enumerate(time_options):
            option_text = option.text.strip()
            try:
                LOGGER.info(f"Option text: {option_text}")
                if int(option_text) == int(target_number):
                    option.click()
                    LOGGER.info(f"Clicked time option: {target_number}")
                    return  # Exit after clicking the matching option
            except ValueError as e:
                LOGGER.error(
                    f"Skipping non-integer option: {e}"
                )  # handles non integer text in the span.

        LOGGER.info(f"Time option '{target_number}' not found.")

    except Exception as e:
        LOGGER.info(f"Error finding and clicking time option: {e}")
        raise  # re-raise the exception to stop or handle it in the calling code.


def scroll_timepicker_options(driver, scroll_amount=10, scroll_iterations=5):
    """
    Finds all elements with class "tiktok-timepicker-option-list" and scrolls on them up and down.

    Args:
        driver: The Selenium WebDriver instance.
        scroll_amount: The number of pixels to scroll in each iteration.
        scroll_iterations: The number of scroll up and down iterations.
    """
    try:
        wait = WebDriverWait(driver, 10)  # Adjust timeout as needed

        timepicker_lists = wait.until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "tiktok-timepicker-option-list")
            )
        )

        for timepicker_list in timepicker_lists:
            actions = ActionChains(driver)

            for _ in range(scroll_iterations):
                # Scroll down
                actions.move_to_element(timepicker_list).scroll_by_amount(
                    0, scroll_amount
                ).perform()
                time.sleep(1)  # Add a delay to allow the page to load
                # Scroll up
                actions.move_to_element(timepicker_list).scroll_by_amount(
                    0, -scroll_amount
                ).perform()

            print("Scrolled timepicker list.")

    except Exception as e:
        print(f"Error scrolling timepicker options: {e}")
        raise  # re-raise the exception to stop or handle it in the calling code


def scroll_to_timepicker_options(driver, hour, min):
    """
    Finds all elements with class "tiktok-timepicker-option-list" and scrolls on them up and down.

    Args:
        driver: The Selenium WebDriver instance.
        scroll_amount: The number of pixels to scroll in each iteration.
        scroll_iterations: The number of scroll up and down iterations.
    """
    try:
        wait = WebDriverWait(driver, 10)  # Adjust timeout as needed

        timepicker_lists = wait.until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "tiktok-timepicker-option-list")
            )
        )
        script = """
                    function simulateWheel(element, deltaX, deltaY, deltaZ) {
                    var event = new WheelEvent('wheel', {
                        deltaX: deltaX,
                        deltaY: deltaY,
                        deltaZ: deltaZ,
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    element.dispatchEvent(event);
                    }
                    simulateWheel(arguments[0], arguments[1], arguments[2], arguments[3]);
                """
        for timepicker_list in timepicker_lists:
            children_count = driver.execute_script(
                "return arguments[0].childElementCount;", timepicker_list
            )
            parent_element = driver.execute_script(
                "return arguments[0].parentElement;", timepicker_list
            )

            LOGGER.info("Parent element found with tag: %s", parent_element.tag_name)

            time.sleep(1)
            if children_count == 24:
                mins_to_scroll = (
                    -(datetime.now().hour + 1 - hour)
                    if datetime.now().minute > 40
                    else -(datetime.now().hour - hour)
                )
                # Execute the JavaScript, passing the element and delta values
                for _i in range(abs(mins_to_scroll)):
                    driver.execute_script(
                        script, parent_element, 0, mins_to_scroll * 10000, 0
                    )
                    time.sleep(0.2)
                LOGGER.info("Scrolled for hour: %s", -(datetime.now().hour - hour))
                LOGGER.info("hour: %s", hour)
            else:
                # Execute the JavaScript, passing the element and delta values
                if datetime.now().minute > 55:
                    tmp_min = 15
                elif datetime.now().minute > 50:
                    tmp_min = 10
                elif datetime.now().minute > 45:
                    tmp_min = 5
                elif datetime.now().minute > 40:
                    tmp_min = 0
                else:
                    tmp_min = math.ceil((datetime.now().minute + 15) / 5) * 5

                mins_to_scroll = -int((tmp_min - min) / 5)
                for _i in range(abs(mins_to_scroll)):
                    driver.execute_script(
                        script, parent_element, 0, mins_to_scroll * 10000, 0
                    )
                    time.sleep(0.2)

                LOGGER.info("Scrolled for minute: %s", mins_to_scroll)
                LOGGER.info("minute: %s", min)

    except Exception as e:
        print(f"Error scrolling timepicker options: {e}")
        raise  # re-raise the exception to stop or handle it in the calling code


def __time_picker(driver, hour: int, minute: int) -> None:
    condition = EC.presence_of_element_located(
        (By.XPATH, CONFIG["selectors"]["schedule"]["time_picker"])
    )
    time_picker = WebDriverWait(driver, CONFIG["implicit_wait"]).until(condition)
    time_picker.click()

    condition = EC.presence_of_element_located(
        (By.XPATH, CONFIG["selectors"]["schedule"]["time_picker_container"])
    )
    time_picker_container = WebDriverWait(driver, CONFIG["implicit_wait"]).until(
        condition
    )

    # 00 = 0, 01 = 1, 02 = 2, 03 = 3, 04 = 4, 05 = 5, 06 = 6, 07 = 7, 08 = 8, 09 = 9, 10 = 10, 11 = 11, 12 = 12,
    # 13 = 13, 14 = 14, 15 = 15, 16 = 16, 17 = 17, 18 = 18, 19 = 19, 20 = 20, 21 = 21, 22 = 22, 23 = 23
    hour_options = driver.find_elements(
        By.XPATH, CONFIG["selectors"]["schedule"]["timepicker_hours"]
    )
    # 00 == 0, 05 == 1, 10 == 2, 15 == 3, 20 == 4, 25 == 5, 30 == 6, 35 == 7, 40 == 8, 45 == 9, 50 == 10, 55 == 11
    minute_options = driver.find_elements(
        By.XPATH, CONFIG["selectors"]["schedule"]["timepicker_minutes"]
    )

    hour_to_click = hour_options[hour]
    minute_option_correct_index = int(minute / 5)
    minute_to_click = minute_options[minute_option_correct_index]

    time.sleep(1)  # temporay fix => might be better to use an explicit wait
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
        hour_to_click,
    )
    time.sleep(1)  # temporay fix => might be better to use an explicit wait
    hour_to_click.click()

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
        minute_to_click,
    )
    time.sleep(2)  # temporary fixed => Might be better to use an explicit wait
    minute_to_click.click()

    # click somewhere else to close the time picker
    time_picker.click()


if __name__ == "__main__":
    # MACOS upload_video("/Users/jonathanstoff/Downloads/B0RXp2A_Wv0.mp4", datetime(2025, 2, 23, 12, 0), "Check out this cool video!")

    upload_video_tt(
        "D:/tmp/clips/qCuEQGLtfQ8.mp4",
        datetime(2025, 2, 24, 22, 35),
        open("D:/tmp/clips/qCuEQGLtfQ8.txt").read(),
        submit=False,
    )
