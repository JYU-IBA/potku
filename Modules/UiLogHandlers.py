# coding=utf-8
'''
Created on 16.4.2013
Updated on 23.5.2013

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) Jarkko Aalto, Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen and 
Miika Raunio

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
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli K�rkk�inen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import logging

class customLogHandler(logging.Handler):
    '''Customloghandler, that handles log messages and emits them to the given 
    LogWidget's log field. 
    '''
    def __init__(self, level, formatter, log_dialog):
        '''Initializes the handler.
        
        Args:
            level: The logging level set to this handler.
            formatter: The formatter set to this handler.
            log_dialog: The log dialog, which can add the message to the interface.
        '''
        logging.Handler.__init__(self)
        self.log_dialog = log_dialog
        self.formatter = formatter
        self.level = level        
        
        
    def flush(self):
        """Does nothing here, has to be here because this is inherited.
        """
    
    
    def emit(self, record):
        '''Emits the log message to the destination, which is set when the handler 
        is initialized.
        
        Args:
            record: The record which will be emitted.
        '''
        try:
            message = 'Nothing to log.'           
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
            '''
            From http://docs.python.org/3.3/library/logging.html:
            This method should be called from handlers when an exception is 
            encountered during an emit() call. If the module-level attribute
            raiseExceptions is False, exceptions get silently ignored. This is what
            is mostly wanted for a logging system - most users will not care about 
            errors in the logging system, they are more interested in application 
            errors. You could, however, replace this with a custom handler if you 
            wish. The specified record is the one which was being processed when 
            the exception occurred. The default value of raiseExceptions is True, 
            as that is more useful during development.       
            '''            
            logging.raiseExceptions = False
            self.handleError(record.msg)            
