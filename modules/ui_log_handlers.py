# coding=utf-8
"""
Created on 16.4.2013
Updated on 29.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen, 2021 Juhani Sundell

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n " \
             "Juhani Sundell"
__version__ = "2.0"

import uuid
import logging
from logging import Formatter, FileHandler, Handler
from typing import Optional, Tuple, Iterable, Mapping

from pathlib import Path


class CustomLogHandler(Handler):
    """Custom log handler, that handles log messages and emits them to the
    given LogWidget's log field.
    """

    def __init__(self, level, formatter, log_dialog):
        """Initializes the handler.

        Args:
            level: The logging level set to this handler.
            formatter: The formatter set to this handler.
            log_dialog: The log dialog, which can add the message to the
            interface.
        """
        Handler.__init__(self)
        self.log_dialog = log_dialog
        self.formatter = formatter
        self.level = level

    def flush(self):
        """Does nothing here, has to be here because this is inherited.
        """

    def emit(self, record):
        """Emits the log message to the destination, which is set when the
        handler is initialized.

        Args:
            record: The record which will be emitted.
        """
        try:
            # Must have this check. If the logging level is DEBUG, 
            # there's no record to log from. Only LogRecord, which
            # doesn't have any specifications.
            if record.levelno >= 20:
                message = "{0} - {1} - {2}".format(record.asctime,
                                                   record.levelname,
                                                   record.msg)
            else:
                message = record.msg
            self.log_dialog.on_log_message.emit(message)

            # If the log message is error or higher, also send message to error 
            # field.
            if record.levelno >= 40:
                self.log_dialog.on_error_message.emit(message)
        except:
            # This method should be called from handlers when an exception is 
            # encountered during an emit() call.
            # http://docs.python.org/3.3/library/logging.html
            """
            From http://docs.python.org/3.3/library/logging.html:
            This method should be called from handlers when an exception is 
            encountered during an emit() call. If the module-level attribute
            raiseExceptions is False, exceptions get silently ignored. This is 
            what is mostly wanted for a logging system - most users will not 
            care about errors in the logging system, they are more interested in
            application errors. You could, however, replace this with a custom 
            handler if you wish. The specified record is the one which was being
            processed when the exception occurred. The default value of 
            raiseExceptions is True, as that is more useful during development.
            """
            logging.raiseExceptions = False
            self.handleError(record.msg)


class Logger:
    """Base class for entities that write messages to log files.

    Loggers can form a parent - child hierarchy. Messages logged by children
    will also be logged by parents.
    """

    __slots__ = "_logger_name", "_logger", "_is_logging_enabled"

    MSG_FMT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FMT = "%Y-%m-%d %H:%M:%S"

    def __init__(
            self,
            enable_logging: bool = True,
            parent: Optional["Logger"] = None) -> None:
        """Initializes a logger.

        Args:
            enable_logging: whether logging is enabled or not
            parent: optional parent logger.
        """
        unique_name = str(uuid.uuid4())
        if parent is not None:
            self._logger_name = f"{parent._logger_name}.{unique_name}"
        else:
            self._logger_name = unique_name
        self._logger = logging.getLogger(self._logger_name)
        self._logger.setLevel(logging.DEBUG)
        self.is_logging_enabled = enable_logging

    @property
    def logger(self) -> logging.Logger:
        """Returns the underlying logging.Logger object of this Logger.
        """
        return self._logger

    @property
    def default_formatter(self) -> Formatter:
        """Returns the default formatter for Loggers.
        """
        return logging.Formatter(self.MSG_FMT, datefmt=self.DATE_FMT)

    @property
    def is_logging_enabled(self) -> bool:
        """Whether logging is enabled or not. If logging is not enabled,
        messages will not be logged.
        """
        return self._is_logging_enabled

    @is_logging_enabled.setter
    def is_logging_enabled(self, b: bool) -> None:
        """Sets logging either enabled or disabled.
        """
        self._is_logging_enabled = b

    @property
    def _kwargs_for_log(self) -> Mapping:
        """Keyword arguments to be applied to self._logger.info.
        """
        return {}

    @property
    def _kwargs_for_error(self) -> Mapping:
        """Keyword arguments to be applied to self._logger.error.
        """
        # Returns the same mapping as _kwargs_for_log. Subclasses may
        # implement their own error kwargs if needed.
        return self._kwargs_for_log

    def _get_handlers(self, directory: Path) -> Iterable[FileHandler]:
        """Returns log files that will be used when set_up_log_files is
        called.
        """
        raise NotImplementedError

    def set_up_log_files(self, log_file_folder: Path) -> None:
        """Closes old log files and sets up new log files in given folder.
        """
        self.close_log_files()
        if not self.is_logging_enabled:
            return

        log_file_folder.mkdir(parents=True, exist_ok=True)

        new_handlers = self._get_handlers(log_file_folder)
        for handler in new_handlers:
            self._logger.addHandler(handler)

    def close_log_files(self) -> None:
        """Closes current log files.
        """
        current_handlers = list(self._logger.handlers)
        for handler in current_handlers:
            self._logger.removeHandler(handler)
            handler.flush()
            handler.close()

    def log(self, msg: str) -> None:
        """Logs given message.
        """
        if self.is_logging_enabled:
            self._logger.info(msg, **self._kwargs_for_log)

    def log_error(self, msg: str) -> None:
        """Logs given message as an error.
        """
        if self.is_logging_enabled:
            self._logger.error(msg, **self._kwargs_for_error)


class _CategorizedLogger(Logger):
    __slots__ = Logger.__slots__ + ("_display_name",)
    DEFAULT_LOG = "default.log"
    ERROR_LOG = "errors.log"

    def __init__(
            self,
            display_name: str,
            enable_logging: bool = True,
            parent: Optional[Logger] = None) -> None:
        """Initializes a new Logger
        """
        super(_CategorizedLogger, self).__init__(enable_logging, parent=parent)
        self._display_name = display_name

    @property
    def category(self) -> str:
        raise NotImplementedError

    @property
    def display_name(self) -> str:
        """Name to be displayed in log messages.
        """
        return self._display_name

    @property
    def info_log_file(self) -> Optional[Path]:
        """Absolute path to the info log file of this Logger instance.
        """
        return self._path_to_log_file(0)

    @property
    def error_log_file(self) -> Optional[Path]:
        """Absolute path to the error log file of this Logger instance.
        """
        return self._path_to_log_file(-1)

    def _path_to_log_file(self, idx: int) -> Optional[Path]:
        if not self._logger.handlers:
            return None
        handler = self._logger.handlers[idx]
        if isinstance(handler, FileHandler):
            return Path(handler.baseFilename).resolve()

    @property
    def _kwargs_for_log(self) -> Mapping:
        return {
            "extra": {
                "child_info": f" - [{self.category} : {self.display_name}]"
            }
        }

    def _get_handlers(
            self,
            directory: Path) -> Tuple[FileHandler, FileHandler]:
        """Returns log handler for default log messages and errors.
        """
        default_log = FileHandler(directory / self.DEFAULT_LOG)
        default_log.setLevel(logging.INFO)
        error_log = FileHandler(directory / self.ERROR_LOG)
        error_log.setLevel(logging.ERROR)

        default_log.setFormatter(self.default_formatter)
        error_log.setFormatter(self.default_formatter)

        return default_log, error_log


class MeasurementLogger(_CategorizedLogger):
    """Logger class for Measurements.
    """
    __slots__ = _CategorizedLogger.__slots__

    @property
    def category(self) -> str:
        return "Measurement"


class SimulationLogger(_CategorizedLogger):
    """Logger class for Simulations.
    """
    __slots__ = _CategorizedLogger.__slots__

    @property
    def category(self) -> str:
        return "Simulation"


class RequestLogger(Logger):
    """Logger class for Requests.
    """
    REQUEST_LOG = "request.log"

    @property
    def request_formatter(self) -> logging.Formatter:
        """Request formatter contains a field for child information.
        """
        fmt = f"%(asctime)s - %(levelname)s%(child_info)s - %(message)s"
        return logging.Formatter(fmt, datefmt=self.DATE_FMT)

    @property
    def _kwargs_for_log(self) -> Mapping:
        return {
            "extra": {
                "child_info": ""
            }
        }

    def _get_handlers(self, directory: Path) -> Tuple[FileHandler]:
        request_log = FileHandler(directory / self.REQUEST_LOG)
        request_log.setLevel(logging.INFO)
        request_log.setFormatter(self.request_formatter)
        return request_log,
