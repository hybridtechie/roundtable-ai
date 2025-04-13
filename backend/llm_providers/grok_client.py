import requests
import os
from .base import LLMBase, logger


class GrokClient(LLMBase):
    def __init__(self, api_key, model, **kwargs):
        super().__init__(api_key=api_key, model=model, **kwargs)
        self.base_url = "https://api.x.ai/v1"
        if not api_key:
            logger.error("Grok API key is required.")
            raise ValueError("Grok API key is required.")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        logger.info("Successfully initialized Grok client for model: %s", model)

    def send_request(self, prompt_or_messages, **kwargs):
        if isinstance(prompt_or_messages, str):
            messages = [{"role": "user", "content": prompt_or_messages}]
        elif isinstance(prompt_or_messages, list):
            messages = prompt_or_messages
        else:
            error_msg = "Input must be a string or a list of messages"
            logger.error(error_msg)
            raise ValueError(error_msg)

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.5),
            "top_p": kwargs.get("top_p", 0.5),
            "max_tokens": kwargs.get("max_tokens", 8000),  # Adjust max_tokens as needed for Grok
            # Add other Grok-specific parameters if known
        }

        endpoint = f"{self.base_url}/chat/completions"
        logger.debug("Sending request to Grok API endpoint: %s with payload: %s", endpoint, payload)

        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            completion = response.json()
            logger.debug("Received response from Grok API: %s", completion)

            # Assuming Grok response structure is similar to OpenAI's
            content = completion.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            # Grok might not return usage details in the same way. Handle potential absence.
            usage = completion.get("usage", {})
            request_tokens = usage.get("prompt_tokens")
            completion_tokens = usage.get("completion_tokens")
            total_tokens = usage.get("total_tokens")

            if total_tokens is not None:
                logger.info("Request successful - Tokens used: %d (prompt: %d, completion: %d)", total_tokens, request_tokens or 0, completion_tokens or 0)
            else:
                logger.info("Request successful. Usage data not fully available in response.")

            return content, {
                "request_tokens": request_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            }

        except requests.exceptions.RequestException as e:
            logger.error("Failed to send request to Grok API: %s", str(e), exc_info=True)
            # Attempt to get more details from the response if available
            error_details = None
            if e.response is not None:
                try:
                    error_details = e.response.json()
                    logger.error("Grok API error details: %s", error_details)
                except ValueError:  # Handle cases where response is not JSON
                    logger.error("Grok API raw error response: %s", e.response.text)
            raise  # Re-raise the original exception

        except Exception as e:
            logger.error("An unexpected error occurred during Grok API request: %s", str(e), exc_info=True)
            raise

    def send_request_w_structured_response(self, prompt_or_messages, response_format, **kwargs):
        logger.warning("Structured response is not implemented for the Grok provider.")
        raise NotImplementedError("Structured response is not implemented for the Grok provider.")
