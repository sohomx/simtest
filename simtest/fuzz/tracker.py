from typing import List
from simtest.fuzz.sandbox import Trace

class BudgetExceeded(Exception):
    def __init__(self, total_cost: float, limit: float):
        super().__init__(f"Budget exceeded: ${total_cost:.2f} > ${limit}")
        self.total_cost = total_cost

class CostTracker:
    INPUT_RATE = 0.0005
    OUTPUT_RATE = 0.0015

    def __init__(self, max_dollars: float = 3.00):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.max_dollars = max_dollars

    def consume_trace(self, trace: List[Trace]):
        for step in trace:
            self.total_input_tokens += step["input_tokens"]
            self.total_output_tokens += step["output_tokens"]

        total_cost = self.compute_cost()
        if total_cost > self.max_dollars:
            raise BudgetExceeded(total_cost, self.max_dollars)

    def compute_cost(self) -> float:
        return (
            (self.total_input_tokens / 1000) * self.INPUT_RATE +
            (self.total_output_tokens / 1000) * self.OUTPUT_RATE
        )
