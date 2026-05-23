from pathlib import PurePath, Path
import logging

MISSING_VALUES_LOGGER = logging.getLogger('missing_values')

MISSING_VALUES_LOGGER.propagate = False
MISSING_VALUES_LOGGER.setLevel(logging.INFO)

# Create a file handler for the logger
FILE_HANDLER = logging.FileHandler(Path("missing_values.log"))
FILE_HANDLER.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
FILE_HANDLER.setFormatter(formatter)

MISSING_VALUES_LOGGER.addHandler(FILE_HANDLER)

# MISSING_VALUES_LOGGER.info(f"File has missing values on columns")
