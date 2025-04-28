import logging

def setup_logger(name="TranscriptionServer"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Console output
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
