from clip_creator.conf import (
    POSSIBLE_TRANSLATE_LANGS,
    LOGGER
)
from clip_creator.social.custom_tiktok import scheduled_run

def sched_run():
    """
    This function is used to run the scheduled task.
    It will run the scheduled task every few hours-4x a day.
    """
    LOGGER.info("Running scheduled task...")
    scheduled_run()
    for lang in POSSIBLE_TRANSLATE_LANGS:
        LOGGER.info(f"Running scheduled task for {lang}...")
        scheduled_run(lang)
    LOGGER.info("Scheduled task completed.")
    
if __name__ == "__main__":
    sched_run()
