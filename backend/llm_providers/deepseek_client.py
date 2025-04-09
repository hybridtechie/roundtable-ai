import requests
import json
from .base import LLMBase, logger

class DeepseekClient(LLMBase):
    def __init__(self, api_key, model, **kwargs):
        super().__init__(api_key=api_key, model=model, **kwargs)
        self.api_url = "https://api.deepseek.com/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        logger.info("Successfully initialized Deepseek client for model: %s", self.model)

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
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.5),
            "top_p": kwargs.get("top_p", 0.9), # Deepseek default might differ, using common value
            "max_tokens": kwargs.get("max_tokens", 2048), # Adjust as needed
            # Add other Deepseek specific parameters if necessary
        }

        logger.debug("Sending request to Deepseek API with payload: %s", payload)

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            completion = response.json()
            content = completion['choices'][0]['message']['content'].strip()

            # Extract usage info if available (structure might vary)
            usage = {}
            if 'usage' in completion:
                usage = {
                    "request_tokens": completion['usage'].get('prompt_tokens'),
                    "completion_tokens": completion['usage'].get('completion_tokens'),
                    "total_tokens": completion['usage'].get('total_tokens'),
                }
                logger.info(
                    "Request successful - Tokens used: %s (prompt: %s, completion: %s)",
                    usage.get("total_tokens", "N/A"),
                    usage.get("request_tokens", "N/A"),
                    usage.get("completion_tokens", "N/A")
                )
            else:
                 logger.info("Request successful - Usage info not available in response.")


            return content, usage

        except requests.exceptions.RequestException as e:
            logger.error("Failed to send request to Deepseek API: %s", str(e), exc_info=True)
            # Attempt to get more details from response if available
            error_details = ""
            try:
                error_details = response.text
            except Exception:
                pass # Ignore if response text is not available
            logger.error("Deepseek API error details: %s", error_details)
            raise ConnectionError(f"Deepseek API request failed: {e}") from e
        except (KeyError, IndexError) as e:
             logger.error("Failed to parse Deepseek API response: %s", str(e), exc_info=True)
             logger.error("Deepseek API raw response: %s", response.text)
             raise ValueError(f"Invalid response format from Deepseek API: {e}") from e
        except Exception as e:
            logger.error("An unexpected error occurred during Deepseek request: %s", str(e), exc_info=True)
            raise

    def send_request_w_structured_response(self, prompt_or_messages, response_format, **kwargs):
        # Deepseek might not support structured responses like OpenAI's beta feature.
        # Raise NotImplementedError or adapt if Deepseek offers a similar feature.
        logger.warning("Structured response not implemented for Deepseek provider.")
        raise NotImplementedError("Deepseek provider does not support structured responses currently.")