import math
import re
import ast
import logging
from typing import Dict, Any, Union, Optional
import operator as op

from .base import Tool, ToolResult

logger = logging.getLogger(__name__)

class CalculatorTool(Tool[Dict[str, Any]]):
    """Tool for performing mathematical calculations."""
    
    name = "calculator"
    description = "Perform mathematical calculations and return the result"
    parameters = {
        "expression": {
            "type": "string",
            "description": "The mathematical expression to evaluate (e.g., '2 + 2', 'sin(0.5)', 'sqrt(16)')"
        }
    }
    required_params = ["expression"]
    
    # Supported operators
    OPERATORS = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
        ast.FloorDiv: op.floordiv,
        ast.Mod: op.mod,
        ast.USub: op.neg,  # Unary negation
    }
    
    # Supported functions with their implementations
    FUNCTIONS = {
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        "exp": math.exp,
        "log": math.log,
        "log10": math.log10,
        "sqrt": math.sqrt,
        "abs": abs,
        "round": round,
        "floor": math.floor,
        "ceil": math.ceil,
        "degrees": math.degrees,
        "radians": math.radians,
        "factorial": math.factorial
    }
    
    # Constants
    CONSTANTS = {
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
        "inf": math.inf,
        "nan": math.nan
    }
    
    def _run(self, expression: str) -> Dict[str, Any]:
        """Evaluate a mathematical expression.
        
        Args:
            expression: The mathematical expression to evaluate
            
        Returns:
            Dictionary containing the result and metadata
        """
        self.logger.info(f"Evaluating expression: {expression}")
        
        try:
            # Preprocess the expression to handle functions
            processed_expr = self._preprocess_expression(expression)
            
            # Parse the expression into an AST
            node = ast.parse(processed_expr, mode='eval').body
            
            # Evaluate the AST safely
            result = self._safe_eval(node)
            
            return {
                "expression": expression,
                "result": result,
                "formatted_result": self._format_number(result)
            }
        
        except Exception as e:
            self.logger.error(f"Error evaluating expression '{expression}': {str(e)}", exc_info=True)
            return {
                "expression": expression,
                "error": str(e),
                "result": None
            }
    
    def _preprocess_expression(self, expression: str) -> str:
        """Preprocess the expression to handle common mathematical notations."""
        # Remove whitespace and convert to lowercase for constant names
        expr = expression.strip()
        
        # Safety check: Limit expression length
        if len(expr) > 500:
            raise ValueError("Expression is too long (max 500 characters)")
        
        # Replace constants with their values
        for name, value in self.CONSTANTS.items():
            pattern = r'\b' + name + r'\b'
            expr = re.sub(pattern, str(value), expr, flags=re.IGNORECASE)
        
        return expr
    
    def _safe_eval(self, node: ast.AST) -> Union[int, float]:
        """Safely evaluate the AST node for a mathematical expression."""
        # Handle numbers directly
        if isinstance(node, ast.Num):
            return node.n
        
        # Handle names (variables)
        elif isinstance(node, ast.Name):
            if node.id.lower() in [c.lower() for c in self.CONSTANTS]:
                return self.CONSTANTS[node.id.lower()]
            raise NameError(f"Name '{node.id}' is not defined")
        
        # Handle unary operations (like -x)
        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                return -self._safe_eval(node.operand)
            raise TypeError(f"Unsupported unary operator: {type(node.op).__name__}")
        
        # Handle binary operations (like x + y)
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type in self.OPERATORS:
                left = self._safe_eval(node.left)
                right = self._safe_eval(node.right)
                
                # Extra safety checks for specific operations
                if op_type == ast.Div and right == 0:
                    raise ZeroDivisionError("Division by zero")
                if op_type == ast.Pow:
                    # Limit exponentiation to avoid DoS
                    if abs(right) > 1000:
                        raise ValueError("Exponent too large (max 1000)")
                    if abs(left) > 1e10:
                        raise ValueError("Base too large for exponentiation")
                
                return self.OPERATORS[op_type](left, right)
            
            raise TypeError(f"Unsupported binary operator: {type(node.op).__name__}")
        
        # Handle function calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id.lower()
                if func_name in [f.lower() for f in self.FUNCTIONS]:
                    # Get the function with case-insensitive matching
                    for name, func in self.FUNCTIONS.items():
                        if name.lower() == func_name:
                            func_impl = func
                            break
                    
                    # Evaluate all arguments
                    args = [self._safe_eval(arg) for arg in node.args]
                    
                    # Special handling for functions with domain restrictions
                    if func_name == "sqrt" and args[0] < 0:
                        raise ValueError("Cannot calculate square root of a negative number")
                    if func_name in ["log", "log10"] and args[0] <= 0:
                        raise ValueError(f"Cannot calculate logarithm of a non-positive number")
                    if func_name == "factorial" and (args[0] < 0 or not float(args[0]).is_integer()):
                        raise ValueError("Factorial is only defined for non-negative integers")
                    if func_name in ["asin", "acos"] and abs(args[0]) > 1:
                        raise ValueError(f"{func_name} domain error: input must be between -1 and 1")
                    
                    try:
                        return func_impl(*args)
                    except Exception as e:
                        raise ValueError(f"Error in function {func_name}: {str(e)}")
                
                raise NameError(f"Function '{node.func.id}' is not supported")
            
            raise TypeError("Unsupported function call")
        
        # Reject any other node types
        raise TypeError(f"Unsupported operation: {type(node).__name__}")
    
    def _format_number(self, value: Union[int, float]) -> str:
        """Format a number for human-readable output."""
        if isinstance(value, int):
            return str(value)
        
        # Format float to avoid excessive decimal places
        if value.is_integer():
            return str(int(value))
        
        # Use scientific notation for very large/small numbers
        abs_value = abs(value)
        if abs_value > 1e6 or (abs_value < 1e-6 and abs_value > 0):
            return f"{value:.10e}"
        
        # Regular float format with up to 10 decimal places
        return f"{value:.10g}" 