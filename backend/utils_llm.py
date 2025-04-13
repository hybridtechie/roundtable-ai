import os
from dotenv import load_dotenv
from logger_config import setup_logger
from llm_providers.azure_openai import AzureOpenAIClient
from llm_providers.openai_client import OpenAIClient
from llm_providers.grok_client import GrokClient  # Added GrokClient import
from llm_providers.deepseek_client import DeepseekClient
from llm_providers.gemini_client import GeminiClient  # Added Gemini client

# Set up logger
logger = setup_logger(__name__)


class LLMClient:
    def __init__(self, provider_details):
        load_dotenv()  # Ensure environment variables are loaded

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
                    model=provider_details.get("model", provider_details.get("deployment_name")),  # Use model or deployment_name
                )
            elif self.provider.lower() == "openai":
                required_fields = ["model", "api_key"]  # api_key can be None if env var is set
                self._validate_required_fields(provider_details, required_fields, allow_none=["api_key"])

                self.client = OpenAIClient(
                    api_key=provider_details.get("api_key"),  # Pass None if not provided,
                    model=provider_details["model"],
                )
            elif self.provider.lower() == "grok":  # Added Grok provider handling
                required_fields = ["model", "api_key"]
                self._validate_required_fields(provider_details, required_fields)

                self.client = GrokClient(
                    api_key=provider_details["api_key"],
                    model=provider_details["model"],
                )
            elif self.provider.lower() == "deepseek":
                required_fields = ["model", "api_key"]
                self._validate_required_fields(provider_details, required_fields)

                self.client = DeepseekClient(
                    api_key=provider_details["api_key"],
                    model=provider_details["model"],
                )
            elif self.provider.lower() == "gemini":
                required_fields = ["model", "api_key"]
                self._validate_required_fields(provider_details, required_fields)

                self.client = GeminiClient(
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
    
    def generate_embeddings(self, text: str) -> list[float]:
        """Sends a request expecting a structured response using the initialized provider client."""
        return self.client.generate_embeddings(text)


# Example usage (similar to the original __main__ block)
if __name__ == "__main__":
    try:
        load_dotenv()

        # Example Azure OpenAI provider details
        azure_provider_details = {
            "provider": "AzureOpenAI",
            "deployment_name": os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4o"),  # Example default
            "model": os.getenv("AZURE_MODEL_NAME", "gpt-4o"),  # Example default
            "endpoint": os.getenv("AZURE_ENDPOINT"),
            "api_version": "2024-10-21",  # Matches hardcoded version in client
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        }

        # Initialize client with Azure OpenAI provider
        if all(azure_provider_details.values()):  # Basic check if env vars are set
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
            "model": os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),  # Example default
            "api_key": os.getenv("OPENAI_API_KEY"),  # Can be None if env var is set globally
        }

        # Initialize client with OpenAI provider
        if openai_provider_details["api_key"] or os.getenv("OPENAI_API_KEY"):  # Check if key is provided or set in env
            logger.info("--- Testing OpenAI Client ---")
            client_openai = LLMClient(openai_provider_details)
            logger.info("Testing LLM client with provider: %s", openai_provider_details["provider"])

            # Test single message
            prompt_openai = "Tell me a joke about programming."
            logger.info("Testing single message prompt...")
            response_openai = client_openai.send_request(prompt_openai)  # Usage info might not be returned consistently
            logger.info(f"Response: {response_openai}")
            logger.info("Single message test successful.")
        else:
            logger.warning("Skipping OpenAI tests - OPENAI_API_KEY not set.")

        # Example Grok provider details (Added Grok example)
        grok_provider_details = {"provider": "Grok", "model": os.getenv("GROK_MODEL_NAME", "grok-1"), "api_key": os.getenv("GROK_API_KEY")}  # Example default

        # Initialize client with Grok provider
        if grok_provider_details["api_key"]:  # Check if key is provided
            logger.info("--- Testing Grok Client ---")
            client_grok = LLMClient(grok_provider_details)
            logger.info("Testing LLM client with provider: %s", grok_provider_details["provider"])

            # Test single message
            prompt_grok = "Explain the concept of Mixture of Experts in LLMs."
            logger.info("Testing single message prompt...")
            response_grok, usage_grok = client_grok.send_request(prompt_grok)
            logger.info(f"Response: {response_grok}")
            if usage_grok and usage_grok.get("total_tokens") is not None:
                logger.info(f"Usage: {usage_grok}")
            logger.info("Single message test successful.")
        else:
            logger.warning("Skipping Grok tests - GROK_API_KEY not set.")

        # Example Deepseek provider details (Requires DEEPSEEK_API_KEY and DEEPSEEK_MODEL_NAME env vars)
        deepseek_provider_details = {"provider": "Deepseek", "model": os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat"), "api_key": os.getenv("DEEPSEEK_API_KEY")}  # Example default

        # Initialize client with Deepseek provider
        if deepseek_provider_details["api_key"]:  # Check if key is provided
            logger.info("--- Testing Deepseek Client ---")
            try:
                client_deepseek = LLMClient(deepseek_provider_details)
                logger.info("Testing LLM client with provider: %s", deepseek_provider_details["provider"])

                # Test single message
                prompt_deepseek = "What is Deepseek good at?"
                logger.info("Testing single message prompt...")
                response_deepseek, usage_deepseek = client_deepseek.send_request(prompt_deepseek)
                logger.info(f"Response: {response_deepseek}")
                logger.info(f"Usage: {usage_deepseek}")
                logger.info("Single message test successful.")
            except Exception as e:
                logger.error("Deepseek test failed during execution: %s", str(e), exc_info=True)
        else:
            logger.warning("Skipping Deepseek tests - DEEPSEEK_API_KEY not set.")

        # Example Gemini provider details (Requires GOOGLE_API_KEY and GEMINI_MODEL_NAME env vars)
        gemini_provider_details = {
            "provider": "Gemini",
            "model": os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash"),  # Example default
            "api_key": os.getenv("GOOGLE_API_KEY"),  # Google uses GOOGLE_API_KEY convention
        }

        # Initialize client with Gemini provider
        if gemini_provider_details["api_key"]:  # Check if key is provided
            logger.info("--- Testing Gemini Client ---")
            try:
                client_gemini = LLMClient(gemini_provider_details)
                logger.info("Testing LLM client with provider: %s", gemini_provider_details["provider"])

                # Test single message
                prompt_gemini = "Explain the concept of generative AI simply."
                logger.info("Testing single message prompt...")
                # Note: Gemini client currently returns None for usage details
                response_gemini, usage_gemini = client_gemini.send_request(prompt_gemini)
                logger.info(f"Response: {response_gemini}")
                logger.info(f"Usage: {usage_gemini}")  # Will show None values
                logger.info("Single message test successful.")
            except Exception as e:
                logger.error("Gemini test failed during execution: %s", str(e), exc_info=True)
        else:
            logger.warning("Skipping Gemini tests - GOOGLE_API_KEY not set.")

    except Exception as e:
        logger.error("Test failed: %s", str(e), exc_info=True)
        raise
