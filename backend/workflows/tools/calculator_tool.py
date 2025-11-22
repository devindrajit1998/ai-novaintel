"""
Calculator tool for mathematical and financial calculations.
"""
from typing import Any, Dict, Optional
from workflows.tools.base_tool import BaseTool, ToolResult
import math
import sys


class CalculatorTool(BaseTool):
    """Tool for performing mathematical and financial calculations."""
    
    def __init__(self):
        """Initialize calculator tool."""
        super().__init__(
            name="calculator",
            description="Perform mathematical and financial calculations (arithmetic, percentage, ROI, NPV, etc.)"
        )
        print("[OK] Calculator Tool initialized", file=sys.stderr, flush=True)
    
    def execute(self, expression: str, calculation_type: str = "arithmetic") -> ToolResult:
        """
        Execute calculation.
        
        Args:
            expression: Mathematical expression or calculation parameters
            calculation_type: "arithmetic", "percentage", "roi", "npv", "compound_interest"
        
        Returns:
            ToolResult with calculation result
        """
        try:
            if calculation_type == "arithmetic":
                result = self._calculate_arithmetic(expression)
            elif calculation_type == "percentage":
                result = self._calculate_percentage(expression)
            elif calculation_type == "roi":
                result = self._calculate_roi(expression)
            elif calculation_type == "npv":
                result = self._calculate_npv(expression)
            elif calculation_type == "compound_interest":
                result = self._calculate_compound_interest(expression)
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Unknown calculation type: {calculation_type}"
                )
            
            return ToolResult(
                success=True,
                result=result,
                metadata={"calculation_type": calculation_type, "expression": expression}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Calculation failed: {str(e)}"
            )
    
    def _calculate_arithmetic(self, expression: str) -> Dict[str, Any]:
        """Evaluate arithmetic expression safely."""
        # Sanitize expression (only allow safe characters)
        allowed_chars = set("0123456789+-*/.() %,")
        if not all(c in allowed_chars or c.isspace() for c in expression):
            raise ValueError("Expression contains invalid characters")
        
        # Replace common math functions
        expression = expression.replace("sqrt", "math.sqrt")
        expression = expression.replace("pow", "math.pow")
        expression = expression.replace("log", "math.log")
        expression = expression.replace("exp", "math.exp")
        
        # Evaluate safely
        result = eval(expression, {"__builtins__": {}}, {"math": math})
        
        return {
            "expression": expression,
            "result": float(result) if isinstance(result, (int, float)) else result,
            "formatted": f"{result:,.2f}" if isinstance(result, (int, float)) else str(result)
        }
    
    def _calculate_percentage(self, expression: str) -> Dict[str, Any]:
        """Calculate percentage (e.g., "45% of 1000" or "50 increase by 20%")."""
        # Parse common percentage expressions
        parts = expression.lower().split()
        
        if "%" in expression:
            # Extract numbers and percentage
            import re
            numbers = [float(x) for x in re.findall(r'\d+\.?\d*', expression)]
            
            if "of" in parts:
                # Percentage of number
                percentage = numbers[0]
                number = numbers[1] if len(numbers) > 1 else 0
                result = (percentage / 100) * number
                return {
                    "expression": expression,
                    "result": result,
                    "formatted": f"{percentage}% of {number} = {result:,.2f}"
                }
            elif "increase" in parts or "decrease" in parts:
                # Percentage increase/decrease
                base = numbers[0]
                percentage = numbers[1] if len(numbers) > 1 else 0
                change = (percentage / 100) * base
                result = base + change if "increase" in parts else base - change
                return {
                    "expression": expression,
                    "result": result,
                    "formatted": f"{base} {'increased' if 'increase' in parts else 'decreased'} by {percentage}% = {result:,.2f}"
                }
        
        raise ValueError(f"Could not parse percentage expression: {expression}")
    
    def _calculate_roi(self, expression: str) -> Dict[str, Any]:
        """Calculate ROI (Return on Investment)."""
        # Parse: "roi initial investment gain" or "roi 100000 125000"
        import re
        numbers = [float(x) for x in re.findall(r'\d+\.?\d*', expression)]
        
        if len(numbers) >= 2:
            initial_investment = numbers[0]
            gain = numbers[1] - initial_investment if len(numbers) == 2 else numbers[2]
            roi = (gain / initial_investment) * 100
            
            return {
                "expression": expression,
                "result": roi,
                "formatted": f"ROI: {roi:.2f}% (Investment: {initial_investment:,.2f}, Gain: {gain:,.2f})"
            }
        
        raise ValueError(f"Could not parse ROI expression: {expression}")
    
    def _calculate_npv(self, expression: str) -> Dict[str, Any]:
        """Calculate NPV (Net Present Value)."""
        # Parse: "npv rate cashflows" or "npv 0.1 -1000 300 300 300"
        import re
        numbers = [float(x) for x in re.findall(r'-?\d+\.?\d*', expression)]
        
        if len(numbers) >= 3:
            rate = numbers[0]
            cashflows = numbers[1:]
            npv = sum(cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cashflows))
            
            return {
                "expression": expression,
                "result": npv,
                "formatted": f"NPV: {npv:,.2f} (Rate: {rate*100:.2f}%, Cashflows: {len(cashflows)})"
            }
        
        raise ValueError(f"Could not parse NPV expression: {expression}")
    
    def _calculate_compound_interest(self, expression: str) -> Dict[str, Any]:
        """Calculate compound interest."""
        # Parse: "compound principal rate years" or "compound 1000 0.05 10"
        import re
        numbers = [float(x) for x in re.findall(r'\d+\.?\d*', expression)]
        
        if len(numbers) >= 3:
            principal = numbers[0]
            rate = numbers[1]
            years = int(numbers[2])
            compound_frequency = int(numbers[3]) if len(numbers) > 3 else 1
            
            amount = principal * (1 + rate / compound_frequency) ** (compound_frequency * years)
            interest = amount - principal
            
            return {
                "expression": expression,
                "result": amount,
                "interest": interest,
                "formatted": f"Compound Interest: {amount:,.2f} (Principal: {principal:,.2f}, Interest: {interest:,.2f}, Rate: {rate*100:.2f}%, Years: {years})"
            }
        
        raise ValueError(f"Could not parse compound interest expression: {expression}")
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get JSON schema for parameters."""
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression or calculation parameters"
                },
                "calculation_type": {
                    "type": "string",
                    "enum": ["arithmetic", "percentage", "roi", "npv", "compound_interest"],
                    "description": "Type of calculation to perform",
                    "default": "arithmetic"
                }
            },
            "required": ["expression"]
        }


# Global instance
calculator_tool = CalculatorTool()

