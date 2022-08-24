from datetime import datetime, date, timedelta

import pytest
from dateutil.relativedelta import relativedelta

from .utils import cache_property, parse_bool, RunMode, RunDate, date_range, month_range


def test_cache_property():
    class DateTime:
        @property
        @cache_property
        def now(self):
            return datetime.now()

    x = DateTime()

    with pytest.raises(AttributeError) as e:
        x._now
    assert str(e.value) == "'DateTime' object has no attribute '_now'"

    now = x.now
    assert x._now == now
    assert x.now == now


def test_parse_bool():
    assert parse_bool("True") is True
    assert parse_bool("TRUE") is True
    assert parse_bool("true") is True
    assert parse_bool("1") is True
    assert parse_bool(1) is True
    assert parse_bool(True) is True
    assert parse_bool("False") is False
    assert parse_bool("FALSE") is False
    assert parse_bool("false") is False
    assert parse_bool("0") is False
    assert parse_bool(0) is False
    assert parse_bool("") is False
    assert parse_bool(None) is False
    assert parse_bool(False) is False
    with pytest.raises(ValueError) as e:
        parse_bool("test")
    assert str(e.value) == "Cannot parse `test` of type <class 'str'> to bool"


def test_run_mode():
    assert RunMode("daily") == RunMode.DAILY
    assert RunMode(RunMode.DAILY) == RunMode.DAILY
    assert RunMode.DAILY.is_daily() is True
    assert RunMode.DAILY.is_monthly() is False
    assert RunMode.DAILY.is_full_scan() is False
    assert RunMode.FULL_SCAN.is_daily() is False
    assert RunMode.FULL_SCAN.is_monthly() is False
    assert RunMode.FULL_SCAN.is_full_scan() is True

    assert RunMode("monthly") == RunMode.MONTHLY
    assert RunMode(RunMode.MONTHLY) == RunMode.MONTHLY
    assert RunMode.MONTHLY.is_daily() is False
    assert RunMode.MONTHLY.is_monthly() is True
    assert RunMode.MONTHLY.is_full_scan() is False

    with pytest.raises(ValueError) as e:
        RunMode("test")
    assert str(e.value) == "'test' is not a valid RunMode"


def test_run_date_init():
    assert isinstance(RunDate("20200101"), str)
    assert RunDate(20200101) == RunDate("20200101")
    assert RunDate(datetime(2020, 1, 1)) == RunDate("20200101")
    assert RunDate(date(2020, 1, 1)) == RunDate("20200101")
    assert RunDate("20200101") == "20200101"

    with pytest.raises(ValueError) as e:
        RunDate("x")
    assert str(e.value) == "time data 'x' does not match format '%Y%m%d'"

    with pytest.raises(TypeError) as e:
        RunDate(None)
    assert str(
        e.value) == "RunDate() got an unexpected type `<class 'NoneType'>`. Must be datetime, date or str in format %Y%m%d"


def test_run_date_functions():
    assert isinstance(RunDate("20200101").to_date(), date)
    assert RunDate("20200101").to_date() == date(2020, 1, 1)
    assert isinstance(RunDate("20200101").to_datetime(), datetime)
    assert RunDate("20200101").to_datetime() == datetime(2020, 1, 1)
    assert RunDate("20200526").begin_of_week() == "20200525"
    assert RunDate("20200526").end_of_week() == "20200531"
    assert RunDate("20200526").begin_of_month() == "20200501"
    assert RunDate("20200526").begin_of_last_month() == "20200401"
    assert RunDate("20200526").end_of_month() == "20200531"


def test_run_date_operators():
    assert RunDate("20200101") + timedelta(days=1) == "20200102"
    assert RunDate("20200101") + relativedelta(months=1) == "20200201"
    assert "date=" + RunDate("20200201") == "date=20200201"
    assert "date={}".format(RunDate("20200201")) == "date=20200201"
    assert RunDate("20200102") - timedelta(days=1) == "20200101"
    assert RunDate("20200201") - relativedelta(months=1) == "20200101"
    assert RunDate("20200102") - date(2020, 1, 1) == timedelta(days=1)
    assert RunDate("20200102") - datetime(2020, 1, 1) == timedelta(days=1)
    assert RunDate("20200102") - RunDate("20200101") == timedelta(days=1)

    assert RunDate("20200101") == date(2020, 1, 1)
    assert RunDate("20200101") == datetime(2020, 1, 1)
    assert RunDate("20200101") == "20200101"
    assert RunDate("20200101") == 20200101
    assert RunDate("20200101") == RunDate("20200101")

    assert RunDate("20200101") < date(2020, 1, 2)
    assert RunDate("20200101") < datetime(2020, 1, 2)
    assert RunDate("20200101") < "20200102"
    assert RunDate("20200101") < 20200102
    assert RunDate("20200101") < RunDate("20200102")

    assert RunDate("20200102") > date(2020, 1, 1)
    assert RunDate("20200102") > datetime(2020, 1, 1)
    assert RunDate("20200102") > "20200101"
    assert RunDate("20200102") > 20200101
    assert RunDate("20200102") > RunDate("20200101")

    assert RunDate("20200101") <= date(2020, 1, 2)
    assert RunDate("20200101") <= datetime(2020, 1, 2)
    assert RunDate("20200101") <= "20200102"
    assert RunDate("20200101") <= 20200102
    assert RunDate("20200101") <= RunDate("20200102")

    assert RunDate("20200102") >= date(2020, 1, 1)
    assert RunDate("20200102") >= datetime(2020, 1, 1)
    assert RunDate("20200102") >= "20200101"
    assert RunDate("20200102") >= 20200101
    assert RunDate("20200102") >= RunDate("20200101")


def test_date_range():
    assert date_range(RunDate("20200101"), RunDate("20200102")) == [RunDate("20200101"), RunDate("20200102")]
    assert date_range("20200101", "20200102") == [RunDate("20200101"), RunDate("20200102")]
    assert date_range(20200101, 20200102) == [RunDate("20200101"), RunDate("20200102")]
    assert date_range(date(2020, 1, 1), date(2020, 1, 2)) == [RunDate("20200101"), RunDate("20200102")]
    assert date_range(datetime(2020, 1, 1), datetime(2020, 1, 2)) == [RunDate("20200101"), RunDate("20200102")]


def test_month_range():
    assert month_range(RunDate("20200101"), RunDate("20200110")) == ["202001"]
    assert month_range("20200101", "20200110") == ["202001"]
    assert month_range(20201010, 20201011) == ["202010"]
    assert month_range(date(2020, 10, 10), date(2020, 12, 10)) == ["202010", "202011", "202012"]
    assert month_range(date(2020, 10, 10), date(2020, 12, 10)) == ["202010", "202011", "202012"]
    assert month_range("20191001", "20200101") == ["201910", "201911", "201912", "202001"]
