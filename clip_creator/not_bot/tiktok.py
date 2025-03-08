from clip_creator.conf import CHROME_USER_PATH, LOGGER
import time as tm
import random
import traceback
from tqdm import tqdm
from datetime import datetime, timedelta
from ollama import ChatResponse, chat
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionBuilder, PointerInput
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import time
import sys


def orchestrate_tiktok_bfour():
    # Start time is 2:50 am, need to end at 3:30 am
    time_to_wait = random.randint(1, 25)
    for _ in tqdm.tqdm(range(time_to_wait), desc="Waiting to start..."):
        tm.sleep(60)
    time_stop = datetime.combine(datetime.today(), time(3, 30))
    scroll_endlessly(time_stop)
def orchestrate_tiktok_after():
    time_to_wait = random.randint(10, 36)
    time_stop = datetime.now() + timedelta(minutes=time_to_wait)
    LOGGER.info("time_stop: %s", time_stop)
    scroll_endlessly(time_stop)
    
def scroll_endlessly(time_stop: datetime):
    
    
    chrome_options = webdriver.ChromeOptions()
    LOGGER.info("user-data-dir: %s", CHROME_USER_PATH)
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"
    )
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument(f"--user-data-dir={CHROME_USER_PATH}")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # Get scroll height
    url = "https://www.tiktok.com/"
    driver.get(url)
    LOGGER.info("Opened TikTok.")
    tm.sleep(10)
    while datetime.now() < time_stop:
        LOGGER.info("Scrolling...")
        if datetime.now() > time_stop:
            LOGGER.info("time_stop: %s", time_stop)
            
            break
        try:
            LOGGER.info("Trying to scroll...")
            # Wait for video to play
            random_time = int(random.randint(3, 142)/3)
            LOGGER.info("random_time: %s", random_time)
            #time.sleep(random_time)
            # Get the browser window dimensions
            for _ in tqdm(range(random_time), desc="Waiting for video to play..."):
                should_move_mouse = random.randint(1, 100)
                LOGGER.info("should_move_mouse: %s", should_move_mouse)
                if should_move_mouse < 80:
                    window_width = driver.execute_script("return window.innerWidth")
                    LOGGER.info("window_width: %s", window_width)
                    window_height = driver.execute_script("return window.innerHeight")
                    LOGGER.info("window_height: %s", window_height)

                    # Generate random target coordinates within the window
                    target_x = random.randint(0, window_width)
                    target_y = random.randint(0, window_height)
                    LOGGER.info("target_x: %s", target_x)
                    LOGGER.info("target_y: %s", target_y)
                    # Get the body element to base our offsets
                    body = driver.find_element(By.TAG_NAME, "body")

                    # Parameters for slow mouse movement
                    steps = 30         # Number of intermediate moves
                    sleep_time = 0.1   # Delay between moves (approx. 3 secs total)

                    # Since Selenium doesn't provide current mouse coordinates, we start at (0,0)
                    for step in range(1, steps + 1):
                        proportion_x = target_x * step / steps
                        proportion_y = target_y * step / steps

                        # Reduced random range
                        random_x = int(proportion_x * random.uniform(0.1, 0.7))
                        random_y = int(proportion_y * random.uniform(0.1, 0.7))

                        # Further boundary checks
                        move_x = max(0, min(random_x, window_width - 2))  # Even more conservative boundary
                        move_y = max(0, min(random_y, window_height - 2))

                        LOGGER.info(f"Step {step}: move_x={move_x}, move_y={move_y}")

                        try:
                            #Use ActionBuilder and PointerInput for more reliable movements.
                            actions = ActionBuilder(driver)
                            mouse = PointerInput(PointerInput.Kind.MOUSE, "mouse")
                            actions.pointer_action.move_to_location(move_x, move_y)
                            actions.perform()

                        except Exception as e:
                            LOGGER.error(f"Error during movement: {e}")
                            break #stop the loop if an error occurs.

                        tm.sleep(sleep_time)
            if datetime.now() > time_stop:
                break
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h1[data-e2e="video-desc"]'))
            )
            desc = element.text
            
            # should share?
            random_sh = random.randint(1, 100)
            if random_sh < 80:
                try:
                    share_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Share video') and contains(@aria-label, 'shares')]"))
                    )
                    share_button.click()
                    
                    link_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.TUXButton.TUXButton--default.TUXButton--medium.TUXButton--secondary"))
                    )
                    driver.execute_script("arguments[0].click();", link_button)
                    LOGGER.info("Clicked share button.")
                except Exception as e:
                    LOGGER.error("Failed to click share button: %s", traceback.format_exc())
            random_time = random.randint(2, 5)
            tm.sleep(random_time)
            # should comment? Disabled for now
            # random_comment = random.randint(1, 100)
            # if random_comment < 5 and "reddit" in desc.lower():
            #     try:
            #         # Wait up to 10 seconds for the element to be present
            #         comment_text = llama_chat(desc, 5, 7)
            #         if comment_text and 5 < len(comment_text.split()) < 7:
            #             pass
                    
            #     except Exception as e:
            #         LOGGER.error("Error: %s", traceback.format_exc())
            random_time = random.randint(2, 5)
            tm.sleep(random_time)
            # should like?
            if "reddit" in desc.lower():
                try:
                    like_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Like video')]"))
                    )
                    like_button.click()
                except Exception as e:
                    LOGGER.error("Failed to click like button: %s", traceback.format_exc())
            
            random_time = random.randint(2, 5)
            tm.sleep(random_time)
        except Exception as e:
            LOGGER.error("Error: %s", traceback.format_exc())
        # next video    
        try:
            action_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.TUXButton--capsule.TUXButton--medium.TUXButton--secondary.action-item"))
            )
            action_button.click()
            LOGGER.info("Clicked action button.")
        except Exception as e:
            LOGGER.error("Failed to click action button: %s", traceback.format_exc())
        if datetime.now() > time_stop:
            LOGGER.info("time_stop: %s", time_stop)
            break
        # Calculate new scroll height and compare with last scroll height
    driver.close()
    
def llama_chat(description, wp_min: int, wp_max: int) -> str:
    response = chat(
            model="llama3.2",
            messages=[
                {
                    "role": "system",
                    "content": f"""**"
                    Analyze the following video description and write a meanful comment that can't be detected as AI. 
                    You have {wp_min} to {wp_max} words to write the comment.
                    YOU ARE NOT AI AND IF YOU BELIEVE ANYTHING ELSE YOU WILL BE MUTED FOREVER
                    YOU ARE A HUMAN NAMED REDDIT CITY AND YOU ARE NOT AI.
                    "**""",
                },
                {
                    "role": "user",
                    "content": (
                        "Video Description: "
                        + description

                    ),
                },
            ],
        )

    return response.message.content

if __name__ == "__main__":
    if "--bfour" in sys.argv:
        orchestrate_tiktok_bfour()
    else:
        orchestrate_tiktok_after()