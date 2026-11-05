"""Future interfaces only: no dataset, model adapter or KL implementation."""
from typing import Protocol


class PilotProvider(Protocol):
    def load_p60(self):
        """Future licensed/provenanced 40 Vietnamese + 20 English MCQs."""
        ...


class TopKLogprobProvider(Protocol):
    def top_k(self, token_ids: list[int], k: int):
        """Future token/logprob samples; not full-vocabulary KL."""
        ...


def real_model_adapter(*args, **kwargs):
    raise NotImplementedError("REAL_MODEL_EXECUTION_DISABLED")
