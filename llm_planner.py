"""
LLM Query Planner Module

Uses OpenAI API to generate structured JSON query plans from natural language questions.
"""

import json
from typing import Dict, Any, Optional
from openai import OpenAI


class LLMPlanner:
    """Generates JSON query plans from natural language using LLM."""
    
    def __init__(self, client: OpenAI, model: str = "gpt-4o-mini"):
        """
        Initialize the LLM planner.
        
        Args:
            client: OpenAI client instance
            model: Model name to use (default: gpt-4o-mini)
        """
        self.client = client
        self.model = model
    
    def generate_plan(self, question: str, available_columns: Dict[str, list]) -> Optional[Dict[str, Any]]:
        """
        Use LLM to generate a JSON query plan from user question.
        
        Args:
            question: User's natural language question
            available_columns: Dictionary mapping filenames to their column lists
            
        Returns:
            JSON query plan dictionary or None if generation fails
        """
        system_prompt = """You are a query planner for a CSV analytics system. Your job is to understand user questions and generate structured JSON query plans.

Available files:
- trades.csv
- holdings.csv

Available columns:
""" + json.dumps(available_columns, indent=2) + """

You must generate a JSON plan in this exact format:
{
  "files": ["holdings.csv"],  // List of files to query (must be from allowed list)
  "operation": "aggregate",    // One of: count, aggregate, group_by, sort, filter, limit
  "group_by": "PortfolioName", // Optional: column to group by
  "metric": "PL_YTD",          // Optional: column for aggregation
  "aggregation": "sum",        // Required if operation=aggregate: sum, mean, min, max, count
  "filters": [],               // Optional: [{"column": "PortfolioName", "operator": "==", "value": "Fund A"}]
  "sort": "desc",              // Optional: "asc" or "desc"
  "limit": 5                   // Optional: number of results to return
}

Rules:
- files must be a subset of ["trades.csv", "holdings.csv"]
- operation must be one of: count, aggregate
- For count operations: count rows, optionally group_by
- For aggregate operations: must specify metric and aggregation
- filters support operators: ==, !=, >, <, >=, <=, in
- Only use columns that exist in the available_columns list
- If the question cannot be answered from the CSV files, return null

Respond ONLY with valid JSON, no other text.
"""

        user_prompt = f"User question: {question}\n\nGenerate the JSON query plan:"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for deterministic plans
                response_format={"type": "json_object"}
            )
            
            plan_text = response.choices[0].message.content
            plan = json.loads(plan_text)
            return plan
        
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {e}")
            return None
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None
