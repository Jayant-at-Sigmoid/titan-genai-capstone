import time
import math
from typing import Dict, Any

class FormattingHelpers:
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Converts bytes to human readable format (KB, MB)."""
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

    @staticmethod
    def calculate_cost(input_tokens: int, output_tokens: int, model_type: str = "fast") -> float:
        """
        Estimates Bedrock API invocation costs.
        'complex' = Sonnet, 'fast' = Haiku.
        """
        # Claude 3.5 Sonnet
        if model_type == "complex":
            return (input_tokens * 0.003 / 1000) + (output_tokens * 0.015 / 1000)
        # Claude 3 Haiku
        else:
            return (input_tokens * 0.00025 / 1000) + (output_tokens * 0.00125 / 1000)

class TimerContext:
    """Context manager to measure execution latency."""
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start
