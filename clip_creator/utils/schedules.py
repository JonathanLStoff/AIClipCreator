from datetime import datetime

from clip_creator.conf import LOGGER, WK_SCHED


def round_to_nearest_5(minutes: float) -> int:
    # Rounds minutes (as float) down to the nearest 5-minute mark.
    return int(minutes // 5) * 5


def get_timestamps(sections: int) -> list:
    """
    Divides the interval between 5:00 (AM) and midnight (24:00) into equal sections.
    Returns a list of timestamps formatted as "HH:MM" (rounded to the nearest 5 minutes).

    If sections is 3, for example, the interval is divided into 3 equal parts,
    resulting in 4 timestamps (including both endpoints).
    """
    dtnh = int(datetime.now().hour)
    dtnm = int(datetime.now().minute)
    sh = 5 if dtnh < 5 else dtnh if dtnm < 40 else dtnh + 1
    start_minutes = sh * 60  # 5:00 AM in minutes (300)
    end_minutes = (23 * 60) + 59  # Midnight in minutes (1439)
    total = end_minutes - start_minutes  # Total minutes in the interval
    LOGGER.info(
        "sched: %s, %s, %s, %s, %s, %s", dtnh, dtnm, sh, start_minutes, total, sections
    )
    step = total / sections  # Duration of each section in minutes

    timestamps = []
    for i in range(sections + 1):
        # Calculate the raw minutes value for this time point.
        time_in_minutes = start_minutes + i * step
        # Round to the nearest 5 minutes.
        rounded_minutes = round_to_nearest_5(time_in_minutes)
        # Handle case where rounding reaches 1440 (display as "00:00").
        if rounded_minutes >= 1440:
            rounded_minutes %= 1440
        hour = rounded_minutes // 60
        minute = rounded_minutes % 60
        timestamps.append(
            datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        )

    return timestamps


def none_old_timestamps() -> list:
    today_index = datetime.today().weekday()  # Monday is 0, Sunday is 6
    schedule = WK_SCHED[today_index]
    now = datetime.now()
    updated = []
    for t in schedule:
        if ":" not in t:
            updated.append(t)
            continue
        hour, minute = map(int, t.split(":"))
        if minute > 59:
            minute = 59
        LOGGER.info("sched: %s, %s, %s, %s", hour, minute, now.hour, now.minute)
        scheduled_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        updated.append(None if scheduled_dt < now else t)
    return updated


def none_old_timestamps_com() -> list:
    today_index = datetime.today().weekday()  # Monday is 0, Sunday is 6
    schedule = WK_SCHED[today_index]
    now = datetime.now()
    updated = []
    for t in schedule:
        if ":" not in t:
            updated.append(t)
            continue
        hour, minute = map(int, t.split(":"))
        if minute > 59:
            minute = 59
        LOGGER.info("sched: %s, %s, %s, %s", hour, minute, now.hour, now.minute)
        scheduled_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        updated.append(None if scheduled_dt < now else t)
    return updated


# Example usage:
if __name__ == "__main__":
    # Divide the interval into 5 sections (you will get 6 timestamps including start and end)
    times = get_timestamps(5)
    print(times)
