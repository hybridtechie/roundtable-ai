import os
import datetime
import json
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from logger_config import setup_logger
from openai import AzureOpenAI

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

    def _log_to_csv(self, date, time, prompt, response, completion):
        """
        Logs request and response details into a CSV file.
        """
        try:
            log_dir = f"./logs/{date}"
            self._ensure_directory_exists(log_dir)

            log_file = os.path.join(log_dir, "llm_logs.csv")
            file_exists = os.path.isfile(log_file)

            header = [
                "Date",
                "Time",
                "Prompt",
                "Response",
                "Prompt Tokens",
                "Completion Tokens",
                "Total Tokens",
                "Model",
                "Cost",
            ]

            # Convert prompt and response to strings if needed
            if isinstance(prompt, list):
                prompt_summary = " ".join([msg["content"] for msg in prompt if "content" in msg])[:50].replace("\n", " ")
            else:
                prompt_summary = str(prompt)[:50].replace("\n", " ")

            response_summary = str(response)[:50].replace("\n", " ")
            prompt_token_cost = 0.0000025
            completion_token_cost = 0.00001
            cost = (completion.usage.prompt_tokens * prompt_token_cost) + (completion.usage.completion_tokens * completion_token_cost)
            row = [
                date,
                time,
                prompt_summary,
                response_summary,
                completion.usage.prompt_tokens,
                completion.usage.completion_tokens,
                completion.usage.total_tokens,
                completion.model,
                cost,
            ]

            with open(log_file, "a", encoding="utf-8") as f:
                if not file_exists:
                    f.write(",".join(header) + "\n")
                f.write(",".join(map(str, row)) + "\n")

            logger.debug("Logged LLM interaction to CSV: %s", log_file)
        except Exception as e:
            logger.error("Failed to log to CSV: %s", str(e), exc_info=True)
            # Don't raise the error as this is a non-critical operation

    @staticmethod
    def log_request_response(prompt, response, step_name, folder="./responses"):
        """
        Logs prompt and response details into separate files for debugging.
        """
        try:
            today, now = LLMBase._get_timestamp()
            log_dir = os.path.join(folder, step_name, today)
            LLMBase._ensure_directory_exists(log_dir)

            request_file = os.path.join(log_dir, f"{now}_req.txt")
            response_file = os.path.join(log_dir, f"{now}_res.txt")

            with open(request_file, "w", encoding="utf-8") as req_file:
                req_file.write(prompt if isinstance(prompt, str) else " ".join(message.get("content", "") for message in prompt))

            with open(response_file, "w", encoding="utf-8") as res_file:
                if isinstance(response, str):
                    res_file.write(response)
                else:
                    res_file.write(json.dumps(response, indent=2))

            logger.debug("Logged request/response to files: %s, %s", request_file, response_file)
        except Exception as e:
            logger.error("Failed to log request/response: %s", str(e), exc_info=True)
            # Don't raise the error as this is a non-critical operation


class AzureOpenAIClient(LLMBase):
    def __init__(self, api_key, azure_endpoint, **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.azure_endpoint = azure_endpoint

        try:
            self.client = AzureOpenAI(api_key=api_key, api_version="2024-10-21", azure_endpoint=azure_endpoint)
            logger.info("Successfully initialized Azure OpenAI client with endpoint: %s", azure_endpoint)
        except Exception as e:
            logger.error("Failed to initialize Azure OpenAI client: %s", str(e), exc_info=True)
            raise

    def send_request(self, prompt_or_messages, **kwargs):
        if isinstance(prompt_or_messages, str):
            messages = [{"role": "user", "content": prompt_or_messages}]
        elif isinstance(prompt_or_messages, list):
            messages = prompt_or_messages
        else:
            error_msg = "Input must be a string or a list of messages"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            parameters = {
                "model": kwargs.get("model", self.model),
                "temperature": kwargs.get("temperature", 0.5),
                "top_p": kwargs.get("top_p", 0.5),
                "max_tokens": kwargs.get("max_tokens", 10000),
                "messages": messages,
            }
            logger.debug("Sending request to Azure OpenAI with parameters: %s", parameters)

            completion = self.client.chat.completions.create(**parameters)
            request_tokens = completion.usage.prompt_tokens
            completion_tokens = completion.usage.completion_tokens
            total_tokens = completion.usage.total_tokens

            logger.info("Request successful - Tokens used: %d (prompt: %d, completion: %d)", total_tokens, request_tokens, completion_tokens)

            return completion.choices[0].message.content.strip(), {
                "request_tokens": request_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            }
        except Exception as e:
            logger.error("Failed to send request to Azure OpenAI: %s", str(e), exc_info=True)
            raise

    def send_request_w_structured_response(self, prompt_or_messages, response_format, **kwargs):
        if isinstance(prompt_or_messages, str):
            messages = [{"role": "user", "content": prompt_or_messages}]
        elif isinstance(prompt_or_messages, list):
            messages = prompt_or_messages
        else:
            error_msg = "Input must be a string or a list of messages"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            logger.debug("Sending structured request to Azure OpenAI")
            completion = self.client.beta.chat.completions.parse(
                model=kwargs.get("model", self.model),
                messages=messages,
                response_format=response_format,
            )

            response = completion.choices[0].message.parsed
            logger.info("Successfully received structured response from Azure OpenAI")
            return response

        except Exception as e:
            logger.error("Failed to send structured request: %s", str(e), exc_info=True)
            raise


class OpenAIClient(LLMBase):
    def __init__(self, api_key, **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        from openai import OpenAI

        try:
            self.client = OpenAI()
            logger.info("Successfully initialized OpenAI client")
        except Exception as e:
            logger.error("Failed to initialize OpenAI client: %s", str(e), exc_info=True)
            raise

    def send_request(self, prompt_or_messages, **kwargs):
        if isinstance(prompt_or_messages, str):
            messages = [{"role": "user", "content": prompt_or_messages}]
        elif isinstance(prompt_or_messages, list):
            messages = prompt_or_messages
        else:
            error_msg = "Input must be a string or a list of messages"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            logger.debug("Sending request to OpenAI")
            response = self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                temperature=kwargs.get("temperature", 0.5),
                max_tokens=kwargs.get("max_tokens", 10000),
                top_p=kwargs.get("top_p", 0.5),
            )
            logger.info("Successfully received response from OpenAI")
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("Failed to send request to OpenAI: %s", str(e), exc_info=True)
            raise

    def send_request_w_structured_response(self, prompt_or_messages, response_format, **kwargs):
        error_msg = "OpenAI structured response logic not implemented"
        logger.error(error_msg)
        raise NotImplementedError(error_msg)


# Unified LLM Client
class LLMClient:
    def __init__(self, provider_details):
        """
        Initialize LLM client with provider-specific details.

        Args:
            provider_details (dict): Dictionary containing provider configuration
                Required fields for Azure:
                    - provider: "AzureOpenAI"
                    - deployment_name: Deployment name for the model
                    - model: Model name
                    - endpoint: Azure endpoint URL
                    - api_version: API version
                    - api_key: API key
                Required fields for OpenAI:
                    - provider: "OpenAI"
                    - model: Model name
                    - api_key: API key
        """
        load_dotenv()

        if not isinstance(provider_details, dict):
            error_msg = "Provider details must be a dictionary"
            logger.error(error_msg)
            raise ValueError(error_msg)

        self.provider = provider_details.get("provider")
        if not self.provider:
            error_msg = "Provider field is required in provider_details"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("Initializing LLM client with provider: %s", self.provider)

        try:
            if self.provider.lower() == "azureopenai":
                required_fields = ["deployment_name", "model", "endpoint", "api_version", "api_key"]
                self._validate_required_fields(provider_details, required_fields)

                self.client = AzureOpenAIClient(
                    api_key=provider_details["api_key"],
                    azure_endpoint=provider_details["endpoint"],
                    model=provider_details["model"],
                )
            elif self.provider.lower() == "openai":
                required_fields = ["model", "api_key"]
                self._validate_required_fields(provider_details, required_fields)

                self.client = OpenAIClient(
                    api_key=provider_details["api_key"],
                    model=provider_details["model"],
                )
            else:
                error_msg = f"Unsupported provider: {self.provider}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        except Exception as e:
            logger.error("Failed to initialize LLM client: %s", str(e), exc_info=True)
            raise

    def _validate_required_fields(self, provider_details, required_fields):
        """Validate that all required fields are present in provider_details."""
        missing_fields = [field for field in required_fields if field not in provider_details]
        if missing_fields:
            error_msg = f"Missing required fields for {self.provider}: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def send_request(self, prompt_or_messages, **kwargs):
        return self.client.send_request(prompt_or_messages, **kwargs)

    def send_request_w_structured_response(self, prompt_or_messages, response_format, **kwargs):
        return self.client.send_request_w_structured_response(prompt_or_messages, response_format, **kwargs)


if __name__ == "__main__":
    try:
        load_dotenv()

        # Example Azure OpenAI provider details
        azure_provider_details = {
            "provider": "AzureOpenAI",
            "deployment_name": "gpt-4",
            "model": "gpt-4",
            "endpoint": os.getenv("AZURE_ENDPOINT"),
            "api_version": "2024-10-21",
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        }

        # Initialize client with Azure OpenAI provider
        client = LLMClient(azure_provider_details)
        logger.info("Testing LLM client with provider: %s", azure_provider_details["provider"])

        # Test single message
        prompt = "What is the capital of France?"
        logger.info("Testing single message prompt")
        response = client.send_request(prompt)
        logger.info("Single message test successful")

        # Test chat message
        logger.info("Testing chat message prompt")
        prompt = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there! How can I help you today?"},
            {"role": "user", "content": "What is the time now?"},
        ]
        response = client.send_request(prompt)
        logger.info("Chat message test successful")

        # Example OpenAI provider details (commented out for reference)
        # openai_provider_details = {
        #     "provider": "OpenAI",
        #     "model": "gpt-4",
        #     "api_key": os.getenv("OPENAI_API_KEY")
        # }

    except Exception as e:
        logger.error("Test failed: %s", str(e), exc_info=True)
        raise
