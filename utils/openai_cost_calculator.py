"""
Utility for calculating estimated OpenAI API costs based on token usage.
"""

# Cost per 1,000 tokens (as of Nov 2025)
OPENAI_PRICES = {
    "gpt-4o": {"prompt": 0.005, "completion": 0.015},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.00060},
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
    "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
}

def calculate_openai_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculate estimated cost for a given OpenAI model based on token usage.

    Args:
        model_name (str): Model identifier (e.g., 'gpt-4o', 'gpt-4o-mini', etc.)
        prompt_tokens (int): Number of input (prompt) tokens used.
        completion_tokens (int): Number of output (completion) tokens used.

    Returns:
        float: Estimated total cost in USD.
    """
    if model_name not in OPENAI_PRICES:
        raise ValueError(f"Unsupported model '{model_name}'. Please add it to OPENAI_PRICES.")

    rate = OPENAI_PRICES[model_name]
    prompt_cost = (prompt_tokens / 1000) * rate["prompt"]
    completion_cost = (completion_tokens / 1000) * rate["completion"]
    total_cost = prompt_cost + completion_cost

    return round(total_cost, 6)
