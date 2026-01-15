"""
LLM Result Explainer Module

Uses OpenAI API to explain query execution results in natural language.
"""

import json
from typing import Dict, Any
from openai import OpenAI


class LLMExplainer:
    """Explains query execution results in natural language using LLM."""
    
    def __init__(self, client: OpenAI, model: str = "gpt-4o-mini"):
        """
        Initialize the LLM explainer.
        
        Args:
            client: OpenAI client instance
            model: Model name to use (default: gpt-4o-mini)
        """
        self.client = client
        self.model = model
    
    def explain_results(
        self, 
        question: str, 
        plan: Dict[str, Any], 
        execution_result: Dict[str, Any]
    ) -> str:
        """
        Use LLM to explain the execution results.
        
        Args:
            question: Original user question
            plan: The query plan that was executed
            execution_result: Results from query execution
            
        Returns:
            Natural language explanation
        """
        if not execution_result.get("success"):
            return "Sorry can not find the answer"
        
        result = execution_result.get("result")
        
        system_prompt = """You are an explanation generator for a CSV analytics system. Your job is to explain query results in natural language.

Rules:
- Only explain what the data shows, never invent or hallucinate values
- Be concise and clear
- Format numbers appropriately (e.g., 1000.50)
- If results are empty, say "Sorry can not find the answer"
- Explain how the answer was derived from the data"""

        user_prompt = f"""User question: {question}

Query plan executed:
{json.dumps(plan, indent=2)}

Results:
{json.dumps(result, indent=2, default=str)}

Provide a clear, natural language explanation of these results:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            explanation = response.choices[0].message.content
            return explanation
        
        except Exception as e:
            print(f"Error generating explanation: {e}")
            # Fallback to simple explanation
            return self._simple_explanation(result, plan)
    
    def _simple_explanation(self, result: Any, plan: Dict[str, Any]) -> str:
        """Fallback simple explanation if LLM fails."""
        if isinstance(result, dict):
            response = "Results:\n"
            for key, value in result.items():
                if isinstance(value, (int, float)):
                    response += f"  {key}: {value:,.2f}\n"
                else:
                    response += f"  {key}: {value}\n"
            return response
        elif isinstance(result, (int, float)):
            return f"Result: {result:,.2f}"
        else:
            return f"Result: {result}"
