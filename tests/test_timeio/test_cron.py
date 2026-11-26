# python
import pytest
import random


from timeio.cron import schedule as cron


@pytest.mark.parametrize(
    "schedule, expected",
    [
        ("* * * * *", 1),
        ("*/2 * * * *", 2),
        ("0-59/3 * * * *", 3),
        ("19-59/20 * * * *", 20),
        ("20-59/30 * * * *", 30),
        ("30-59/37 * * * *", 60),
        ("30-59/40 * * * *", 60),
        ("0-59/40 * * * *", 40),
        ("58-59/59 * * * *", 60),
        ("11 */1 * * *", 60),
        ("5 */2 * * *", 120),
        ("1 5 */1 * *", 1440),
        ("1 5 */2 * *", 2880),
        # tricky values
        ("8-59/9 * * * *", 9),  # [8,17,..,53],[8,17,.. -> 9,14,9 --> majority 9
        ("5-59/25 * * * *", 25),  # [5,30,55],[5,30,.. -> 25,10,25 --> majority: 25
        ("0-59/40 * * * *", 40),  # [0,40],[0,40].. -> 20,40,20 or 40,20,40 --> max: 40
        ("0-59/35 * * * *", 35),  # [0,35],[0,35].. -> 35,25,35 or 25,35,25 --> max: 35
    ],
)
def test_get_current_interval(schedule, expected):
    interval = cron.get_current_interval(schedule)
    assert interval == expected


@pytest.mark.parametrize(
    ("schedule", "expected_base_minute"),
    [
        ("0 * * * *", 0),
        ("*/12 * * * *", 0),
        ("@daily", 0),
        ("10,30,50 * * * *", 10),
        ("7-59/12 3-23/5 * * *", 7),
        ("*/12,3-23/5 * * * *", 0),
        ("3-4/12,3-23/5 * * * *", 3),
    ],
)
def test_extract_base_minute(schedule, expected_base_minute):
    base_minute = cron.extract_base_minute(schedule)
    assert base_minute == expected_base_minute


@pytest.mark.parametrize(
    ("schedule", "expected_base_hour"),
    [
        ("* 0 * * *", 0),
        ("* */12 * * *", 0),
        ("@daily", 0),
        ("* 10,15,20 * * *", 10),
        ("* 7-23/12 * * *", 7),
        ("* */12,3-23/5 * * *", 0),
        ("* 3-4/12,3-23/5 * * *", 3),
    ],
)
def test_extract_base_hour(schedule, expected_base_hour):
    base_hour = cron.extract_base_hour(schedule)
    assert base_hour == expected_base_hour


@pytest.mark.parametrize(
    ("interval", "expected"),
    [
        # all following params need random.seed(42)
        (0, "0-59/1 * * * *"),
        (1, "0-59/1 * * * *"),
        (60, "40 0-23/1 * * *"),
        (60 * 24, "40 3 1-31/1 * *"),
        (60 * 24 * 7, "40 3 * * 0"),
        # other
        (30, "20-59/30 * * * *"),
        (120, "40 0-23/2 * * *"),
        (1440, "40 3 1-31/1 * *"),
        (10, "1-59/10 * * * *"),
        (360, "40 0-23/6 * * *"),
        (1500, "40 3 1-31/1 * *"),
        # minute adjustment: odd values get adjusted to the next lower
        # proper divisor of 60
        (17, "10-59/15 * * * *"),
        (19, "10-59/15 * * * *"),
        (11, "1-59/10 * * * *"),
        (7, "5-59/6 * * * *"),
        (8, "5-59/6 * * * *"),
        (31, "20-59/30 * * * *"),
        (32, "20-59/30 * * * *"),
        (45, "20-59/30 * * * *"),
        (55, "20-59/30 * * * *"),
        # hour adjustment: 1,2,3,4,6,8,12
        (122, "40 0-23/2 * * *"),
        (60 * 5, "40 0-23/4 * * *"),
        (60 * 7, "40 0-23/6 * * *"),
        (60 * 9, "40 0-23/8 * * *"),
        (60 * 10, "40 0-23/8 * * *"),
        (60 * 11, "40 0-23/8 * * *"),
        (60 * 14, "40 0-23/12 * * *"),
        (60 * 17, "40 0-23/12 * * *"),
        (60 * 20, "40 0-23/12 * * *"),
        (60 * 23, "40 0-23/12 * * *"),
        (1439, "40 0-23/12 * * *"),
        # week adjustment
        (10085, "40 3 * * 0"),
    ],
)
def test_new_schedule(interval, expected):
    # make random deterministic to ensure we always have the same test results
    random.seed(42)

    schedule = cron.new_schedule(interval)
    schedule2 = cron.new_schedule(interval)
    assert schedule == expected
    if interval in [0, 1]:
        return
    assert schedule != schedule2


@pytest.mark.parametrize(
    ("schedule", "new_interval", "expected"),
    [
        # base minute < 60
        ("0-59/5 * * * *", 10, "0-59/10 * * * *"),
        ("0-59/10 * * * *", 5, "0-59/5 * * * *"),
        ("*/15 * * * *", 30, "0-59/30 * * * *"),
        ("5-59/15 * * * *", 30, "5-59/30 * * * *"),
        # base minute >= new interval -> creates a new random base minute
        ("20-59/30 * * * *", 15, "10-59/15 * * * *"),  # needs random.seed(42)
        # 60 < new interval < 1440
        ("16 */4 * * *", 120, "16 */2 * * *"),
        ("16 0-23/4 * * *", 120, "16 */2 * * *"),
        ("16 */4 * * *", 121, "16 */2 * * *"),
        ("16 */4 * * *", 122, "16 */2 * * *"),
        ("16 */4 * * *", 179, "16 */2 * * *"),
        ("16 */4 * * *", 180, "16 */3 * * *"),
        # interval > 1440 (1day) and interval != 10080 (7days)
        ("37 5 */2 * *", 1440, "37 5 */1 * *"),
        ("37 5 * * *", 7200, "37 5 */5 * *"),
        ("37 5 * * *", 7201, "37 5 */5 * *"),
        ("37 5 * * *", 18719, "37 5 */12 * *"),
        ("37 5 * * *", 18720, "37 5 */13 * *"),
        ("37 5 * * *", 19000, "37 5 */13 * *"),
        ("37 5 * * *", 20000, "37 5 */13 * *"),
        ("37 5 * * *", 20160, "37 5 */14 * *"),
        # interval == 10080 (7days) -> uses a random weekday
        ("37 5 * * *", 10080, "37 5 * * 5"),  # needs random.seed(42)
        ("37 5 * * *", 10090, "37 5 * * 5"),  # needs random.seed(42)
        # no changes expected
        ("5,15,25,35,45,55 * * * *", 10, "5,15,25,35,45,55 * * * *"),
        ("16 */2 * * *", 120, "16 */2 * * *"),
        ("30 */6 * * *", 360, "30 */6 * * *"),
        ("37 5 */13 * *", 20000, "37 5 */13 * *"),
        ("37 5 */13 * *", 20001, "37 5 */13 * *"),
        ("56 15 * * 2", 10080, "56 15 * * 2"),
    ],
)
def test_update_cron_expression(schedule, new_interval, expected):
    # make random deterministic to ensure we always have the same test results
    random.seed(42)

    new_schedule = cron.update_cron_expression(schedule, new_interval)
    assert new_schedule == expected
