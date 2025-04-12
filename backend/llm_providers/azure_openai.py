from openai import AzureOpenAI
from .base import LLMBase, logger


class AzureOpenAIClient(LLMBase):
    def __init__(self, api_key, azure_endpoint, **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.azure_endpoint = azure_endpoint

        try:
            # TODO: Make api_version configurable
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
                "max_tokens": kwargs.get("max_tokens", 10000),  # TODO: Check if this max_tokens is appropriate or should be configurable
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
