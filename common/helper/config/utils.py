from __future__ import annotations

from calendar import MONDAY, SUNDAY
from datetime import datetime, timedelta, date
from enum import Enum
from functools import wraps
from typing import List, Union, Any

import pandas as pd
import pytz
from dateutil.relativedelta import relativedelta

__all__ = [
    'today',
    'yesterday',
    'date_range',
    'RunMode',
    'RunDate',
    'parse_bool',
    'timestamp_to_datetime',
    'cache_property',
    'Domain'
]

TRUE_VALUES = ['True', 'TRUE', 'true', '1', 1, True]
FALSE_VALUES = ['False', 'FALSE', 'false', '0', '', 0, None, False]
TZ_VIETNAM = pytz.timezone('Asia/Saigon')


def cache_property(func):
    """
    Cache property of a property at the first time use and reuse it in the later uses
    Usage:
        class X:
            @property
            @cache_property
            def value(self):
                return 'x'

        x = X()
        x._value  # AttributeError
        x.value   # First time use => 'x'
        x._value  # Cached property => 'x'
        x.value   # Second time use => The same as x._value
    """

    @wraps(func)
    def func_wrapper(self):
        cached_property_name = f'_{func.__name__}'
        if not hasattr(self, cached_property_name):
            setattr(self, cached_property_name, func(self))
        return getattr(self, cached_property_name)

    return func_wrapper


def parse_bool(value: Any) -> bool:
    if value in TRUE_VALUES:
        return True
    elif value in FALSE_VALUES:
        return False
    else:
        raise ValueError(f"Cannot parse `{value}` of type {type(value)} to bool")


def timestamp_to_datetime(value: Union[str, int]) -> datetime:
    return datetime.fromtimestamp(int(value))


class RunMode(Enum):
    DAILY = 'daily'
    MONTHLY = 'monthly'
    FULL_SCAN = 'full_scan'

    def is_daily(self) -> bool:
        return self == RunMode.DAILY

    def is_monthly(self) -> bool:
        return self == RunMode.MONTHLY

    def is_full_scan(self) -> bool:
        return self == RunMode.FULL_SCAN


class RunDate(str):
    FORMAT = "%Y-%m-%d"

    def __new__(cls, value):
        if isinstance(value, (datetime, date)):
            return super().__new__(cls, value.strftime(cls.FORMAT))
        elif isinstance(value, (str, int)):
            value = str(value)
            # Validate format
            datetime.strptime(value, cls.FORMAT)
            return super().__new__(cls, value)
        else:
            raise TypeError(
                f"RunDate() got an unexpected type `{type(value)}`. "
                f"Must be datetime, date or str in format {cls.FORMAT}"
            )

    def to_date(self) -> date:
        return self.to_datetime().date()

    def to_datetime(self) -> datetime:
        return datetime.strptime(self, self.FORMAT)

    def begin_of_week(self) -> RunDate:
        return self + timedelta(days=MONDAY - self.to_date().weekday())

    def end_of_week(self) -> RunDate:
        return self + timedelta(days=SUNDAY - self.to_date().weekday())

    def begin_of_month(self) -> RunDate:
        return RunDate(self.to_date().replace(day=1))

    def begin_of_last_month(self):
        return RunDate((self.to_date() - relativedelta(months=1)).replace(day=1))

    def end_of_month(self) -> RunDate:
        return self.begin_of_month() + relativedelta(months=1) - relativedelta(days=1)

    def end_of_last_month(self):
        return RunDate((self.to_date().replace(day=1) - relativedelta(days=1)))

    def begin_of_year(self) -> RunDate:
        return RunDate(self.to_date().replace(day=1, month=1))

    def end_of_last_year(self) -> RunDate:
        return RunDate((self.to_date().replace(day=1, month=1)) - relativedelta(days=1))

    def __add__(self, other):
        if isinstance(other, (timedelta, relativedelta)):
            return RunDate(self.to_datetime() + other)
        return super().__add__(other)

    def __sub__(self, other):
        if isinstance(other, (timedelta, relativedelta)):
            return RunDate(self.to_datetime() - other)
        elif isinstance(other, datetime):
            return self.to_datetime() - other
        elif isinstance(other, date):
            return self.to_date() - other
        elif isinstance(other, RunDate):
            return self.to_datetime() - other.to_datetime()
        raise TypeError(f"unsupported operand type(s) for -: '{type(self)}' and '{type(other)}'")

    def __eq__(self, other):
        if isinstance(other, datetime):
            return self.to_datetime() == other
        elif isinstance(other, date):
            return self.to_date() == other
        elif isinstance(other, int):
            other = str(other)
        return super().__eq__(other)

    def __lt__(self, other):
        if isinstance(other, datetime):
            return self.to_datetime() < other
        elif isinstance(other, date):
            return self.to_date() < other
        elif isinstance(other, int):
            other = str(other)
        return super().__lt__(other)

    def __gt__(self, other):
        if isinstance(other, datetime):
            return self.to_datetime() > other
        elif isinstance(other, date):
            return self.to_date() > other
        elif isinstance(other, int):
            other = str(other)
        return super().__gt__(other)

    def __le__(self, other):
        if isinstance(other, datetime):
            return self.to_datetime() <= other
        elif isinstance(other, date):
            return self.to_date() <= other
        elif isinstance(other, int):
            other = str(other)
        return super().__le__(other)

    def __ge__(self, other):
        if isinstance(other, datetime):
            return self.to_datetime() >= other
        elif isinstance(other, date):
            return self.to_date() >= other
        elif isinstance(other, int):
            other = str(other)
        return super().__ge__(other)


def date_range(
    start: Union[str, int, date, datetime, RunDate],
    end: Union[str, int, date, datetime, RunDate],
) -> List[RunDate]:
    start = str(RunDate(start))
    end = str(RunDate(end))
    return list(map(RunDate, pd.date_range(start, end).to_pydatetime().tolist()))


def month_range(
    start: Union[str, int, date, datetime, RunDate],
    end: Union[str, int, date, datetime, RunDate],
) -> List[str]:
    """
    Currently used for migrations in cube/pos365_monthly.
    Given the date range, return list of months in str, format '%Y%m'
    """
    start = str(RunDate(start))
    end = str(RunDate(end))
    list_dup_months = list(map(lambda item: datetime.strftime(item, '%Y%m'),
                               pd.date_range(start, end).to_pydatetime()))
    return sorted(set(list_dup_months))


def today() -> RunDate:
    return RunDate(datetime.now(tz=TZ_VIETNAM).date())


def yesterday() -> RunDate:
    return today() - timedelta(days=1)


class Domain(Enum):
    VNSHOP = 'VNSHOP'
    TRACKING = 'TRACKING'
