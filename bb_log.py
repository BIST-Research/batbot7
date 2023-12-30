import logging

def get_log():

    log = logging.getLogger("bat")
    log.setLevel(logging.DEBUG)
    
    ch= logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    
    ch.setFormatter(CustomFormatter())
    
    log.addHandler(ch)
    
    return log

class CustomFormatter(logging.Formatter):
    
    grey = "\x1b[38;20m"
    grey_light = "\x1b[0;37m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    dark_purple = "\x1b[0;35m"
    reset = "\x1b[0m"
    
    format = "[%(asctime)s - %(levelname)s]:\t%(message)s"
    
    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey_light + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
