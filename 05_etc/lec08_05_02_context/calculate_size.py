import json

import tiktoken
from litellm.types.completion import ChatCompletionMessageParam

completion_enc = tiktoken.get_encoding("o200k_base")


def calculate_context_size(messages: list[ChatCompletionMessageParam]) -> int:
    """
    Calculate the total token count for messages.

    Safely overestimate by including all fields in JSON serialization of messages,
    even if those fields might not actually be inserted into the LLM.
    """
    return calculate_num_tokens("\n".join([json.dumps(msg) for msg in messages]))


def calculate_num_tokens(
    text: str
) -> int:
    return len(completion_enc.encode(text, allowed_special={"<|endoftext|>", "<|endofprompt|>"}))
