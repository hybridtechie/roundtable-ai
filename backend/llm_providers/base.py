import os
import datetime
import json
from abc import ABC, abstractmethod
from logger_config import setup_logger

# Set up logger
logger = setup_logger(__name__)


class LLMBase(ABC):
    def __init__(self, api_key=None, model="default-model", **kwargs):
        self.api_key = api_key
        self.model = model
        logger.info("Initializing LLM with model: %s", model)

    @abstractmethod
    def send_request(self, prompt_or_messages, **kwargs):
        pass

    @abstractmethod
    def send_request_w_structured_response(self, prompt_or_messages, response_format, **kwargs):
        pass

    @staticmethod
    def _get_timestamp():
        """
        Returns the current date and time.
        """
        now = datetime.datetime.now()
        return now.strftime("%Y-%m-%d"), now.strftime("%H-%M-%S")

    @staticmethod
    def _ensure_directory_exists(directory):
        """
        Ensures that the specified directory exists.
        """
        try:
            os.makedirs(directory, exist_ok=True)
            logger.debug("Created/verified directory: %s", directory)
        except Exception as e:
            logger.error("Failed to create directory %s: %s", directory, str(e), exc_info=True)
            raise