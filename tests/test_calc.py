from nauta_monitor.calc import format_hours, hours_from_credit


def test_hours_from_credit():
    assert hours_from_credit(100.0, 12.5) == 8.0
    assert hours_from_credit(0.0, 12.5) == 0.0
    assert hours_from_credit(None, 12.5) == 0.0
    assert hours_from_credit(100.0, 0) == 0.0


def test_format_hours():
    assert format_hours(1.0) == "1 h"
    assert format_hours(1.5) == "1 h 30 m"
    assert format_hours(24.0) == "1 d"
    assert format_hours(48.0) == "2 d"
    assert format_hours(0.0) == "0 m"