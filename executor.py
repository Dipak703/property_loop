"""
Query Executor Module

Python executor that validates and executes JSON query plans on CSV data.
This is the source of truth for all data operations.
"""

import pandas as pd
import os
from typing import Optional, Dict, Any, List


class QueryExecutor:
    """Python executor that validates and executes JSON query plans on CSV data."""
    
    ALLOWED_FILES = ['trades.csv', 'holdings.csv']
    ALLOWED_OPERATIONS = ['count', 'aggregate', 'group_by', 'sort', 'filter', 'limit']
    ALLOWED_AGGREGATIONS = ['sum', 'mean', 'min', 'max', 'count']
    
    def __init__(self, data_folder: str = './data'):
        """
        Initialize the executor with CSV data.
        
        Args:
            data_folder: Path to folder containing trades.csv and holdings.csv
        """
        self.data_folder = data_folder
        self.trades_df: Optional[pd.DataFrame] = None
        self.holdings_df: Optional[pd.DataFrame] = None
        self._load_data()
    
    def _load_data(self) -> None:
        """Load CSV files from the data folder."""
        trades_path = os.path.join(self.data_folder, 'trades.csv')
        holdings_path = os.path.join(self.data_folder, 'holdings.csv')
        
        try:
            if os.path.exists(trades_path):
                self.trades_df = pd.read_csv(trades_path)
            else:
                self.trades_df = None
            
            if os.path.exists(holdings_path):
                self.holdings_df = pd.read_csv(holdings_path)
            else:
                self.holdings_df = None
        except Exception as e:
            print(f"Error loading data: {e}")
            self.trades_df = None
            self.holdings_df = None
    
    def _get_dataframe(self, filename: str) -> Optional[pd.DataFrame]:
        """Get dataframe for a given filename."""
        if filename == 'trades.csv':
            return self.trades_df
        elif filename == 'holdings.csv':
            return self.holdings_df
        return None
    
    def _validate_plan(self, plan: Dict[str, Any]) -> tuple:
        """
        Validate the JSON query plan.
        
        Returns:
            (is_valid, error_message)
        """
        # Check required fields
        if 'files' not in plan:
            return False, "Missing 'files' field in plan"
        
        if 'operation' not in plan:
            return False, "Missing 'operation' field in plan"
        
        # Validate files
        files = plan['files']
        if not isinstance(files, list):
            return False, "'files' must be a list"
        
        for file in files:
            if file not in self.ALLOWED_FILES:
                return False, f"File '{file}' is not allowed. Allowed files: {self.ALLOWED_FILES}"
            
            # Check if file exists and is loaded
            df = self._get_dataframe(file)
            if df is None:
                return False, f"File '{file}' not found or could not be loaded"
        
        # Validate operation
        operation = plan['operation']
        if operation not in self.ALLOWED_OPERATIONS:
            return False, f"Operation '{operation}' not allowed. Allowed: {self.ALLOWED_OPERATIONS}"
        
        # Validate aggregation if present
        if operation == 'aggregate':
            if 'aggregation' not in plan:
                return False, "Operation 'aggregate' requires 'aggregation' field"
            if plan['aggregation'] not in self.ALLOWED_AGGREGATIONS:
                return False, f"Aggregation '{plan['aggregation']}' not allowed. Allowed: {self.ALLOWED_AGGREGATIONS}"
        
        # Validate columns exist
        for file in files:
            df = self._get_dataframe(file)
            if 'group_by' in plan and plan['group_by']:
                if plan['group_by'] not in df.columns:
                    return False, f"Column '{plan['group_by']}' not found in {file}"
            
            if 'metric' in plan and plan['metric']:
                if plan['metric'] not in df.columns:
                    return False, f"Column '{plan['metric']}' not found in {file}"
            
            if 'filters' in plan:
                for filter_item in plan['filters']:
                    if 'column' in filter_item and filter_item['column'] not in df.columns:
                        return False, f"Filter column '{filter_item['column']}' not found in {file}"
        
        return True, ""
    
    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a validated JSON query plan.
        
        Args:
            plan: JSON query plan dictionary
            
        Returns:
            Dictionary with 'success', 'result', and 'error' keys
        """
        # Validate plan
        is_valid, error_msg = self._validate_plan(plan)
        if not is_valid:
            return {
                "success": False,
                "error": error_msg,
                "result": None
            }
        
        try:
            # Load data from first file (for now, we support single file queries)
            filename = plan['files'][0]
            df = self._get_dataframe(filename)
            
            if df is None:
                return {
                    "success": False,
                    "error": f"File '{filename}' not loaded",
                    "result": None
                }
            
            # Apply filters if any
            if 'filters' in plan and plan['filters']:
                for filter_item in plan['filters']:
                    column = filter_item.get('column')
                    operator = filter_item.get('operator', '==')
                    value = filter_item.get('value')
                    
                    if operator == '==':
                        df = df[df[column] == value]
                    elif operator == '!=':
                        df = df[df[column] != value]
                    elif operator == '>':
                        df = df[df[column] > value]
                    elif operator == '<':
                        df = df[df[column] < value]
                    elif operator == '>=':
                        df = df[df[column] >= value]
                    elif operator == '<=':
                        df = df[df[column] <= value]
                    elif operator == 'in':
                        df = df[df[column].isin(value)]
            
            # Execute operation
            operation = plan['operation']
            
            if operation == 'count':
                if 'group_by' in plan and plan['group_by']:
                    result = df.groupby(plan['group_by']).size().to_dict()
                else:
                    result = len(df)
            
            elif operation == 'aggregate':
                metric = plan.get('metric')
                aggregation = plan.get('aggregation', 'sum')
                
                if 'group_by' in plan and plan['group_by']:
                    grouped = df.groupby(plan['group_by'])[metric]
                    
                    if aggregation == 'sum':
                        result = grouped.sum().to_dict()
                    elif aggregation == 'mean':
                        result = grouped.mean().to_dict()
                    elif aggregation == 'min':
                        result = grouped.min().to_dict()
                    elif aggregation == 'max':
                        result = grouped.max().to_dict()
                    elif aggregation == 'count':
                        result = grouped.count().to_dict()
                else:
                    if aggregation == 'sum':
                        result = df[metric].sum()
                    elif aggregation == 'mean':
                        result = df[metric].mean()
                    elif aggregation == 'min':
                        result = df[metric].min()
                    elif aggregation == 'max':
                        result = df[metric].max()
                    elif aggregation == 'count':
                        result = df[metric].count()
            
            # Apply sorting
            if 'sort' in plan and plan['sort']:
                if isinstance(result, dict):
                    # Sort dictionary by values
                    reverse = plan['sort'] == 'desc'
                    result = dict(sorted(result.items(), key=lambda x: x[1], reverse=reverse))
                elif isinstance(result, pd.Series):
                    result = result.sort_values(ascending=(plan['sort'] != 'desc'))
            
            # Apply limit
            if 'limit' in plan and plan['limit']:
                if isinstance(result, dict):
                    result = dict(list(result.items())[:plan['limit']])
                elif isinstance(result, pd.Series):
                    result = result.head(plan['limit'])
            
            return {
                "success": True,
                "result": result,
                "error": None,
                "plan": plan
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    def get_available_columns(self) -> Dict[str, List[str]]:
        """Get available columns for each file."""
        columns = {}
        if self.trades_df is not None:
            columns['trades.csv'] = list(self.trades_df.columns)
        if self.holdings_df is not None:
            columns['holdings.csv'] = list(self.holdings_df.columns)
        return columns
