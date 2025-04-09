import google.generativeai as genai
from .base import LLMBase, logger

class GeminiClient(LLMBase):
    def __init__(self, api_key, model, **kwargs):
        super().__init__(api_key=api_key, model=model, **kwargs)

        try:
            genai.configure(api_key=self.api_key)
            # Check if the model exists (optional, but good practice)
            # Note: genai library might not have a direct list_models or check function easily accessible here.
            # We'll rely on the generate_content call to validate the model later.
            self.client = genai.GenerativeModel(self.model)
            logger.info("Successfully configured Google Generative AI client for model: %s", self.model)
        except Exception as e:
            logger.error("Failed to configure Google Generative AI client: %s", str(e), exc_info=True)
            raise

    def send_request(self, prompt_or_messages, **kwargs):
        # Gemini API prefers a simple string prompt or specific content structures.
        # For simplicity, we'll handle string prompts directly.
        # Handling complex message lists might require conversion to Gemini's format.
        if isinstance(prompt_or_messages, list):
             # Attempt to convert a simple user/assistant list to a single prompt string
             # More complex conversions might be needed for multi-turn conversations
             logger.warning("Converting message list to a single string prompt for Gemini. Multi-turn history might be simplified.")
             prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in prompt_or_messages])
        elif isinstance(prompt_or_messages, str):
            prompt = prompt_or_messages
        else:
            error_msg = "Input must be a string or a list of messages"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Gemini specific parameters (refer to google-generativeai documentation)
        generation_config = genai.types.GenerationConfig(
            # candidate_count=1, # Default is 1
            # stop_sequences=['.'],
            max_output_tokens=kwargs.get("max_tokens", 8192), # Default varies by model
            temperature=kwargs.get("temperature", 0.7), # Default varies
            top_p=kwargs.get("top_p", 0.9), # Default varies
            # top_k=kwargs.get("top_k", 40) # Another common param
        )

        # Safety settings (optional, configure as needed)
        # safety_settings = [
        #     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        #     # Add other categories as needed
        # ]

        logger.debug("Sending request to Gemini API with prompt: %s...", prompt[:100]) # Log truncated prompt

        try:
            # Use generate_content for text generation
            response = self.client.generate_content(
                contents=prompt,
                generation_config=generation_config,
                # safety_settings=safety_settings
            )

            # Extract text and handle potential errors/blocks
            if response.candidates:
                content = response.text # response.text provides the combined text
            elif response.prompt_feedback and response.prompt_feedback.block_reason:
                 block_reason = response.prompt_feedback.block_reason
                 logger.error("Gemini request blocked due to: %s", block_reason)
                 raise ValueError(f"Gemini request blocked: {block_reason}")
            else:
                 logger.error("Gemini response did not contain candidates or block reason.")
                 raise ValueError("Invalid response structure from Gemini API")


            # Gemini API (v1) doesn't directly return token counts in the standard response object.
            # You might need to use client.count_tokens(prompt) separately if needed.
            logger.info("Request successful - Received response from Gemini.")
            usage = { # Placeholder for usage, as it's not directly available
                 "request_tokens": None,
                 "completion_tokens": None,
                 "total_tokens": None,
            }

            return content.strip(), usage

        except Exception as e:
            logger.error("Failed to send request to Gemini API: %s", str(e), exc_info=True)
            # Add specific error handling for google.api_core.exceptions if needed
            raise ConnectionError(f"Gemini API request failed: {e}") from e


    def send_request_w_structured_response(self, prompt_or_messages, response_format, **kwargs):
        # Gemini might support structured output via specific prompting techniques or function calling,
        # but not directly like OpenAI's response_format parameter.
        logger.warning("Structured response not directly implemented for Gemini provider via response_format.")
        raise NotImplementedError("Gemini provider does not support the 'response_format' parameter directly.")