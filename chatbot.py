"""
LLM-Assisted CSV-Based Fund Analytics Chatbot

Main chatbot class that orchestrates the Plan → Execute → Explain pattern.
"""

import os
from typing import Optional
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

from executor import QueryExecutor
from llm_planner import LLMPlanner
from llm_explainer import LLMExplainer
from config import DEFAULT_MODEL, ERROR_MESSAGE, API_KEY_ERROR


class FundAnalyticsChatbot:
    """LLM-assisted chatbot for analyzing fund data from CSV files."""
    
    def __init__(self, data_folder: str = './data', api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        """
        Initialize the chatbot.
        
        Args:
            data_folder: Path to folder containing trades.csv and holdings.csv
            api_key: OpenAI API key. If None, will try to get from OPENAI_API_KEY env var.
            model: OpenAI model to use (default: gpt-4o-mini)
        """
        self.data_folder = data_folder
        self.executor = QueryExecutor(data_folder)
        
        # Initialize OpenAI client
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(API_KEY_ERROR)
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
        # Initialize LLM components
        self.planner = LLMPlanner(self.client, model)
        self.explainer = LLMExplainer(self.client, model)
    
    def answer_question(self, question: str) -> str:
        """
        Answer user question using Plan → Execute → Explain pattern.
        
        Args:
            question: User's natural language question
            
        Returns:
            Formatted answer string
        """
        # Step 1: Plan - Generate JSON query plan using LLM
        available_columns = self.executor.get_available_columns()
        plan = self.planner.generate_plan(question, available_columns)
        
        if plan is None:
            return ERROR_MESSAGE
        
        # Step 2: Execute - Run the plan using Python executor
        execution_result = self.executor.execute_plan(plan)
        
        if not execution_result.get("success"):
            return ERROR_MESSAGE
        
        # Step 3: Explain - Generate natural language explanation using LLM
        explanation = self.explainer.explain_results(question, plan, execution_result)
        
        return explanation
