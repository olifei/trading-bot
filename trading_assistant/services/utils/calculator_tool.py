from decimal import Decimal, getcontext
from google.adk.tools import FunctionTool, ToolContext
from trading_assistant.schemas import CalculatorArgs, validate_args

getcontext().prec = 18  # High precision for crypto calculations

def calculate_precise(a: str, b: str, operation: str, tool_context: ToolContext = None) -> dict:
    """
    Perform a high-precision numerical calculation between two values.
    
    This tool supports precise calculations between two numbers, maintaining the high
    precision needed for cryptocurrency transactions. Suitable for calculating
    trading quantities, values, fees, and other mathematical operations.
    
    Args:
        a (str, required): First number as a string to preserve precision
        b (str, required): Second number as a string to preserve precision
        operation (str, required): Operation to perform:
            - "multiply"/"multiplication"/"*"/"times": Multiplication
            - "divide"/"division"/"/"/"divided by": Division
            - "add"/"addition"/"+"/"plus"/"sum": Addition
            - "subtract"/"subtraction"/"-"/"minus": Subtraction
        tool_context (ToolContext): The ADK tool context
        
    Returns:
        dict: Calculation result dictionary, containing:
            - status (str): "success" or "error"
            - result (str): The calculation result (only when successful)
            - message (str): Operation description or error message
    
    Notes:
        - Division by zero will return an error status
        - Input and output use string types to maintain numerical precision
        - Uses Python's Decimal library internally to ensure precise calculations
    """
    _model, err = validate_args(CalculatorArgs, {"a": a, "b": b, "operation": operation})
    if err:
        return {**err, "result": None}
    try:
        a_decimal = Decimal(a)
        b_decimal = Decimal(b)
        
        # Perform the operation
        if operation.lower() in ['multiply', 'multiplication', '*', 'times']:
            result = a_decimal * b_decimal
            operator_symbol = "*"
        elif operation.lower() in ['divide', 'division', '/', 'divided by']:
            if b_decimal == 0:
                return {"status": "error", "message": "Cannot divide by zero", "result": None}
            result = a_decimal / b_decimal
            operator_symbol = "/"
        elif operation.lower() in ['add', 'addition', '+', 'plus', 'sum']:
            result = a_decimal + b_decimal
            operator_symbol = "+"
        elif operation.lower() in ['subtract', 'subtraction', '-', 'minus']:
            result = a_decimal - b_decimal
            operator_symbol = "-"
        else:
            return {"status": "error", "message": f"Unknown operation: {operation}", "result": None}
        
        formatted_result = str(result)
        
        return {
            "status": "success",
            "result": formatted_result,
            "message": f"Calculation: {a} {operator_symbol} {b} = {formatted_result}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error in calculation: {str(e)}",
            "result": None
        }

def create_calculator_tool() -> FunctionTool:
    return FunctionTool(
        func=calculate_precise
    )
