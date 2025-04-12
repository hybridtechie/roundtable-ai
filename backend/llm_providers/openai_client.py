from openai import OpenAI
from .base import LLMBase, logger


class OpenAIClient(LLMBase):
    def __init__(self, api_key, **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        try:
            # Assumes OPENAI_API_KEY environment variable is set if api_key is None
            self.client = OpenAI(api_key=api_key)
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
                max_tokens=kwargs.get("max_tokens", 10000),  # TODO: Check if this max_tokens is appropriate or should be configurable
                top_p=kwargs.get("top_p", 0.5),
            )
            logger.info("Successfully received response from OpenAI")

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("Failed to send request to OpenAI: %s", str(e), exc_info=True)
            raise

    def send_request_w_structured_response(self, prompt_or_messages, response_format, **kwargs):
        # TODO: Implement structured response logic for standard OpenAI if needed/supported
        error_msg = "OpenAI structured response logic not implemented"
        logger.error(error_msg)
        raise NotImplementedError(error_msg)
