import os
import logging.handlers

class TruncatingLogHandler(logging.handlers.RotatingFileHandler):
    def __init__(self, filename, maxBytes=0, encoding=None, delay=False):
        super().__init__(filename, maxBytes=maxBytes, backupCount=0, encoding=encoding, delay=delay)

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.maxBytes > 0:
            curr_size = os.stat(self.baseFilename).st_size
            if curr_size >= self.maxBytes:
                with open(self.baseFilename, 'w') as f:
                    f.truncate(0)
        if not self.delay:
            self.stream = self._open()