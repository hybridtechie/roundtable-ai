import os
from dotenv import load_dotenv
from logger_config import setup_logger
from llm_providers.azure_openai import AzureOpenAIClient
from llm_providers.openai_client import OpenAIClient

# Set up logger
logger = setup_logger(__name__)

class LLMClient:
    def __init__(self, provider_details):
        load_dotenv() # Ensure environment variables are loaded

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
                    model=provider_details.get("model", provider_details.get("deployment_name")), # Use model or deployment_name
                )
            elif self.provider.lower() == "openai":
                required_fields = ["model", "api_key"] # api_key can be None if env var is set
                self._validate_required_fields(provider_details, required_fields, allow_none=["api_key"])

                self.client = OpenAIClient(
                    api_key=provider_details.get("api_key"), # Pass None if not provided, 
                    model=provider_details["model"],
                )
            else:
                error_msg = f"Unsupported provider: {self.provider}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        except Exception as e:
            logger.error("Failed to initialize LLM client: %s", str(e), exc_info=True)
            raise

    def _validate_required_fields(self, provider_details, required_fields, allow_none=None):
        """Validate that all required fields are present in provider_details."""
        if allow_none is None:
            allow_none = []

        missing_fields = []
        for field in required_fields:
            if field not in provider_details:
                missing_fields.append(field)
            elif provider_details[field] is None and field not in allow_none:
                 missing_fields.append(f"{field} (cannot be None)")


        if missing_fields:
            error_msg = f"Missing or invalid required fields for {self.provider}: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def send_request(self, prompt_or_messages, **kwargs):
        """Sends a request using the initialized provider client."""
        return self.client.send_request(prompt_or_messages, **kwargs)

    def send_request_w_structured_response(self, prompt_or_messages, response_format, **kwargs):
        """Sends a request expecting a structured response using the initialized provider client."""
        return self.client.send_request_w_structured_response(prompt_or_messages, response_format, **kwargs)


# Example usage (similar to the original __main__ block)
if __name__ == "__main__":
    try:
        load_dotenv()

        # Example Azure OpenAI provider details
        azure_provider_details = {
            "provider": "AzureOpenAI",
            "deployment_name": os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4"), # Example default
            "model": os.getenv("AZURE_MODEL_NAME", "gpt-4"), # Example default
            "endpoint": os.getenv("AZURE_ENDPOINT"),
            "api_version": "2024-10-21", # Matches hardcoded version in client
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        }

        # Initialize client with Azure OpenAI provider
        if all(azure_provider_details.values()): # Basic check if env vars are set
            logger.info("--- Testing Azure OpenAI Client ---")
            client = LLMClient(azure_provider_details)
            logger.info("Testing LLM client with provider: %s", azure_provider_details["provider"])

            # Test single message
            prompt = "What is the capital of France?"
            logger.info("Testing single message prompt...")
            response, usage = client.send_request(prompt)
            logger.info(f"Response: {response}")
            logger.info(f"Usage: {usage}")
            logger.info("Single message test successful.")

            # Test chat message
            logger.info("Testing chat message prompt...")
            prompt_chat = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there! How can I help you today?"},
                {"role": "user", "content": "What is the time now?"},
            ]
            response_chat, usage_chat = client.send_request(prompt_chat)
            logger.info(f"Response: {response_chat}")
            logger.info(f"Usage: {usage_chat}")
            logger.info("Chat message test successful.")
        else:
            logger.warning("Skipping Azure OpenAI tests - Environment variables not fully set.")


        # Example OpenAI provider details
        openai_provider_details = {
            "provider": "OpenAI",
            "model": os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"), # Example default
            "api_key": os.getenv("OPENAI_API_KEY") # Can be None if env var is set globally
        }

        # Initialize client with OpenAI provider
        if openai_provider_details["api_key"] or os.getenv("OPENAI_API_KEY"): # Check if key is provided or set in env
            logger.info("--- Testing OpenAI Client ---")
            client_openai = LLMClient(openai_provider_details)
            logger.info("Testing LLM client with provider: %s", openai_provider_details["provider"])

            # Test single message
            prompt_openai = "Tell me a joke about programming."
            logger.info("Testing single message prompt...")
            response_openai = client_openai.send_request(prompt_openai) # Usage info might not be returned consistently
            logger.info(f"Response: {response_openai}")
            logger.info("Single message test successful.")
        else:
            logger.warning("Skipping OpenAI tests - OPENAI_API_KEY not set.")

    except Exception as e:
        logger.error("Test failed: %s", str(e), exc_info=True)
        raise