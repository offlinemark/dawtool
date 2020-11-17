from dawtool import format_time

def test_format_time_over_hour():
    assert format_time(60*60) == '60:00'

def test_format_time_under_hour():
    assert format_time(59*60) == '59:00'

def test_format_time_under_min():
    assert format_time(59) == '00:59'

def test_format_time_under_min_hour_fmt():
    assert format_time(59, True) == '00:00:59'

def test_format_time_min():
    assert format_time(60) == '01:00'

def test_format_time_min_hour_fmt():
    assert format_time(60, True) == '00:01:00'

def test_format_time_min_precise():
    assert format_time(60, precise=True) == '01:00.000'

def test_format_time_hour_precise():
    assert format_time(60*60, precise=True) == '60:00.000'

def test_format_time_hour_hour_fmt_precise():
    assert format_time(60*60, precise=True) == '60:00.000'

def test_hours_pad():
    assert format_time(60*60, hours_fmt=True, hours_pad=False) == '1:00:00'
    assert format_time(60*60 + 71, hours_fmt=True, hours_pad=False) == '1:01:11'
    assert format_time(60*60*9, hours_fmt=True, hours_pad=False) == '9:00:00'
    assert format_time(60*60*10, hours_fmt=True, hours_pad=False) == '10:00:00'
    assert format_time(60*60*10 + 59*60 + 59, hours_fmt=True, hours_pad=False) == '10:59:59'
    assert format_time(60*60*10 + 59*60 + 59 + 1, hours_fmt=True, hours_pad=False) == '11:00:00'
    assert format_time(59*60, hours_fmt=True, hours_pad=False) == '0:59:00'
    assert format_time(59, hours_fmt=True, hours_pad=False) == '0:00:59'
    assert format_time(0, hours_fmt=True, hours_pad=False) == '0:00:00'


def test_precise():
    assert format_time(59.1, precise=True) == '00:59.100'
    assert format_time(59.1) == '00:59'
    assert format_time(60.1, precise=True) == '01:00.100'
    assert format_time(60.1) == '01:00'

def test_format_time_sep():
    sep = '〰'
    assert format_time(60*60, sep=sep) == '01〰00〰00'

    assert format_time(59*60, sep=sep) == '59〰00'

    assert format_time(59, sep=sep) == '00〰59'

    assert format_time(59, True, sep=sep) == '00〰00〰59'

    assert format_time(60, sep=sep) == '01〰00'
    assert format_time(60, True, sep=sep) == '00〰01〰00'

    assert format_time(60, precise=True, sep=sep) == '01〰00.000'
    assert format_time(60*60, precise=True, sep=sep) == '01〰00〰00.000'

