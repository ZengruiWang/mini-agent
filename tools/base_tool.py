from typing import Any


class Tool:
    name: str
    description: str
    inputs: dict[str, dict[str, str | type | bool]]
    output_type: str

    def execute(self, **arguments: Any) -> Any:
        raise NotImplementedError(f"{self.name} does not implement execute()")
