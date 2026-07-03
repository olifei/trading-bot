DEFAULT_CONFIG = {
    "model": "gemini-2.5-flash",
    "temperature": 0.1,
    "max_output_tokens": 8192,
    "top_p": 0.95,
    "top_k": 40,
}

ROOT_AGENT_CONFIG = {
    **DEFAULT_CONFIG,
    "temperature": 0.2,
}

SPOT_AGENT_CONFIG = {
    **DEFAULT_CONFIG,
    "model": "gemini-2.5-flash",
    "temperature": 0.05,
}

CONVERT_AGENT_CONFIG = {
    **DEFAULT_CONFIG,
    "model": "gemini-2.5-flash",
    "temperature": 0.05,
}

PORTFOLIO_AGENT_CONFIG = {
    **DEFAULT_CONFIG,
    "temperature": 0.1,
}

MARKET_DATA_AGENT_CONFIG = {
    **DEFAULT_CONFIG,
    "temperature": 0.1,
}