import logging

logger = None

def init_logger():
    global logger

    if logger == None:
        logger = logging.getLogger("pyanola")
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s\n%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
