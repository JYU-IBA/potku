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
Sinikka Siironen

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
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import logging
import os


class CustomLogHandler(logging.Handler):
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
        logging.Handler.__init__(self)
        self.log_dialog = log_dialog
        self.formatter = formatter
        self.level = level

    def flush(self):
        """Does nothing here, has to be here because this is inherited.
        """

    def emit(self, record):
        """Emits the log message to the destination, which is set when the handler
        is initialized.

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
            self.log_dialog.add_text(message)

            # If the log message is error or higher, also send message to error 
            # field.
            if record.levelno >= 40:
                self.log_dialog.add_error(message)
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
    """Common base class for Measurements and Simulations to enable logging.
    """
    # TODO add a function to disable logging
    __slots__ = "logger_name", "category", "datefmt", "defaultlog", "errorlog"

    def __init__(self, logger_name, category, datefmt="%Y-%m-%d %H:%M:%S"):
        """Initializes a new Logger

        Args:
            logger_name: name of the Logger object.
            category: category which the Logger belongs to
            datefmt: format in which to display dates
        """
        self.logger_name = logger_name
        self.category = category
        self.datefmt = datefmt
        self.defaultlog = None
        self.errorlog = None

    def set_loggers(self, directory, request_directory):
        """Sets the loggers for this Logger object.

        The logs will be displayed in the specified directory.
        After this, the logger can be called from anywhere of the
        program, using logging.getLogger([name]).
        """
        # Initializes the logger for this simulation.
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(logging.DEBUG)

        # Adds two loghandlers. The other one will be used to log info (and up)
        # messages to a default.log file. The other one will log errors and
        # criticals to the errors.log file.
        self.defaultlog = logging.FileHandler(os.path.join(directory,
                                                           "default.log"))
        self.defaultlog.setLevel(logging.INFO)
        self.errorlog = logging.FileHandler(os.path.join(directory,
                                                         "errors.log"))
        self.errorlog.setLevel(logging.ERROR)

        # Set the formatter which will be used to log messages. Here you can
        # edit the format so it will be deprived to all log messages.
        defaultformat = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt=self.datefmt)

        requestlog = logging.FileHandler(os.path.join(request_directory,
                                                      "request.log"))

        req_fmt = "%(asctime)s - %(levelname)s - [{0} : '%(name)s] - " \
                  "%(message)s".format(self.category)

        requestlogformat = logging.Formatter(req_fmt,
                                             datefmt=self.datefmt)

        # Set the formatters to the logs.
        requestlog.setFormatter(requestlogformat)
        self.defaultlog.setFormatter(defaultformat)
        self.errorlog.setFormatter(defaultformat)

        # Add handlers to this simulation's logger.
        logger.addHandler(self.defaultlog)
        logger.addHandler(self.errorlog)
        logger.addHandler(requestlog)

    def remove_and_close_log(self, log_filehandler):
        """Closes the log file and removes it from the logger.

        Args:
            log_filehandler: Log's filehandler.
        """
        logging.getLogger(self.logger_name).removeHandler(log_filehandler)
        log_filehandler.flush()
        log_filehandler.close()
