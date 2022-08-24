import copy
import json
import os
from typing import List, Optional

from .utils import RunMode, RunDate, Domain, yesterday, date_range, parse_bool, cache_property


class Config:
    """
    Configurations from environment variables
    Usage:
        # Use default settings
        from common.helper.config import config
        config.run_date  # Get RUN_DATE from environment variables, yesterday by default

        # Use customized settings
        from common.helper.config import Config, today
        config = Config(default_run_date=today() - timedelta(days=30))
        config.run_date  # Get RUN_DATE from environment variables, 30d in the past by default
    """

    def __init__(
        self,
        default_run_mode=RunMode.DAILY,
        default_run_date=None,
        default_start_date=None,
        default_end_date=None,
        default_regenerate_id=False,
        default_rewrite_date_window=1,
    ):
        config_json = os.environ.get('CONFIG_JSON')
        if config_json:
            self._conf = json.loads(config_json)
        else:
            self._conf = copy.deepcopy(os.environ)

        self._default_run_mode = default_run_mode
        self._default_run_date = default_run_date or yesterday()
        self._default_start_date = default_start_date or yesterday()
        self._default_end_date = default_end_date or yesterday()
        self._default_regenerate_id = default_regenerate_id
        self._default_rewrite_date_window = default_rewrite_date_window

    @property
    @cache_property
    def run_mode(self) -> RunMode:
        return RunMode(self._conf.get('RUN_MODE', self._default_run_mode))

    @property
    @cache_property
    def run_date(self) -> RunDate:
        return RunDate(self._conf.get('RUN_DATE', self._default_run_date))

    @property
    @cache_property
    def start_time(self) -> Optional[str]:
        return self._conf.get('START_TIME')

    @property
    @cache_property
    def end_time(self) -> Optional[str]:
        return self._conf.get('END_TIME')

    @property
    @cache_property
    def start_date(self) -> RunDate:
        return RunDate(self._conf.get('START_DATE', self._default_start_date))

    @property
    @cache_property
    def end_date(self) -> RunDate:
        return RunDate(self._conf.get('END_DATE', self._default_end_date))

    @property
    @cache_property
    def date_range(self) -> List[RunDate]:
        return date_range(self.start_date, self.end_date)

    @property
    @cache_property
    def regenerate_id(self) -> bool:
        return parse_bool(self._conf.get('REGENERATE_ID', self._default_regenerate_id))

    @property
    @cache_property
    def rewrite_date_window(self) -> int:
        return int(self._conf.get('REWRITE_DATE_WINDOW', self._default_rewrite_date_window))

    @property
    @cache_property
    def email_to(self) -> str:
        return self._conf.get('EMAIL_TO')

    @property
    @cache_property
    def email_cc(self) -> str:
        return self._conf.get('EMAIL_CC')

    @property
    @cache_property
    def email_bcc(self) -> str:
        return self._conf.get('EMAIL_BCC')


class CubeConfig(Config):
    def __init__(
        self,
        default_domain=Domain.VNSHOP,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._default_domain = default_domain

    @property
    @cache_property
    def domain(self) -> Domain:
        return Domain(self._conf.get("DOMAIN", self._default_domain))


class JDBCIngestionConfig:
    def __init__(self):
        self._conf = copy.deepcopy(os.environ)

    def get_additional_jdbc_property_options(self) -> dict:
        additional_jdbc_property_options = {
            "partitionColumn": self._conf.get('PARTITIONCOLUMN'),
            "lowerBound": self._conf.get('LOWERBOUND'),
            "upperBound": self._conf.get('UPPERBOUND'),
            "numPartitions": self._conf.get('NUMPARTITIONS'),
            "sessionInitStatement": self._conf.get('SESSIONINITSTATEMENT'),
            "customSchema": self._conf.get('CUSTOMSCHEMA'),
            "serverTimezone": self._conf.get('SERVERTIMEZONE'),
        }
        return {k: v for k, v in additional_jdbc_property_options.items() if v}

    @property
    @cache_property
    def url(self) -> str:
        return self._conf.get('URL')

    @property
    @cache_property
    def driver(self) -> str:
        return self._conf.get('DRIVER')

    @property
    @cache_property
    def dbtable(self) -> str:
        return self._conf.get('DBTABLE')

    @property
    @cache_property
    def user(self) -> str:
        return self._conf.get('USER')

    @property
    @cache_property
    def password(self) -> str:
        return self._conf.get('PASSWORD')

    @property
    @cache_property
    def sink_path(self) -> str:
        return self._conf.get('SINK_PATH')

    @property
    @cache_property
    def save_mode(self) -> str:
        return self._conf.get('SAVE_MODE')

    @property
    @cache_property
    def spark_app_name(self) -> str:
        return self._conf.get('SPARK_APP_NAME')


class MongoIngestionConfig:
    def __init__(self):
        self._conf = copy.deepcopy(os.environ)

    @property
    @cache_property
    def uri(self) -> str:
        return self._conf.get('URI')

    @property
    @cache_property
    def database(self) -> str:
        return self._conf.get('DATABASE')

    @property
    @cache_property
    def collection(self) -> str:
        return self._conf.get('COLLECTION')

    @property
    @cache_property
    def sink_path(self) -> str:
        return self._conf.get('SINK_PATH')

    @property
    @cache_property
    def save_mode(self) -> str:
        return self._conf.get('SAVE_MODE', 'overwrite')
