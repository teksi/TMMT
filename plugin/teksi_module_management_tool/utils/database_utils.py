import collections
import configparser
import os
from typing import List

import logging

try:
    import psycopg

    PSYCOPG_VERSION = 3
    DEFAULTS_CONN_ARG = {"autocommit": True}
except ImportError:
    import psycopg2 as psycopg

    PSYCOPG_VERSION = 2
    DEFAULTS_CONN_ARG = {}


class DatabaseUtils:

    class PsycopgConnection:
        def __init__(self, service=None) -> None:
            self.connection = None
            self.service = service

        def __enter__(self):
            connection_parameters = DEFAULTS_CONN_ARG
            if self.service:
                connection_parameters["service"] = self.service

            self.connection = psycopg.connect(
                DatabaseUtils.get_pgconf_as_psycopg_dsn(), **connection_parameters,
            )
            if PSYCOPG_VERSION == 2:
                self.connection.set_session(autocommit=True)

            return self.connection

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.connection.commit()
            self.connection.close()

