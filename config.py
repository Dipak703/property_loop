"""
Configuration Module

Centralized configuration constants for the chatbot system.
"""

# OpenAI Model Configuration
DEFAULT_MODEL = "gpt-4o-mini"  # Cost-effective model
# Alternative models: "gpt-4", "gpt-3.5-turbo"

# LLM Temperature Settings
PLANNER_TEMPERATURE = 0.1  # Low temperature for deterministic query plans
EXPLAINER_TEMPERATURE = 0.3  # Slightly higher for more natural explanations

# Data Configuration
DEFAULT_DATA_FOLDER = './data'
ALLOWED_FILES = ['trades.csv', 'holdings.csv']

# Query Plan Constants
ALLOWED_OPERATIONS = ['count', 'aggregate', 'group_by', 'sort', 'filter', 'limit']
ALLOWED_AGGREGATIONS = ['sum', 'mean', 'min', 'max', 'count']
ALLOWED_FILTER_OPERATORS = ['==', '!=', '>', '<', '>=', '<=', 'in']

# Error Messages
ERROR_MESSAGE = "Sorry can not find the answer"
API_KEY_ERROR = "OpenAI API key required. Set OPENAI_API_KEY environment variable or pass api_key parameter."
