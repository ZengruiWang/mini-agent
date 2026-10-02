from tools.base_tool import Tool


class Calculator(Tool):
    name = "calculator"
    description = (
        "Evaluates a mathematical expression and returns the numeric result. "
        "Use for arithmetic instead of computing in your head."
    )
    inputs = {
        "expression": {
            "type": "string",
            "description": (
                "A Python-style math expression to evaluate, e.g. '1 + 1' or '(3 + 4) * 2'. "
                "Supports +, -, *, /, **, and parentheses. "
                "Use 3.14159 for pi (not the π symbol)."
            ),
        }
    }
    output_type = "number"

    def execute(self, **arguments) -> float:
        expression = arguments.get("expression")
        if expression is None:
            raise ValueError("calculator requires an 'expression' argument")
        return eval(str(expression))
