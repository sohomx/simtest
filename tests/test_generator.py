import pytest
from simtest.seedgen.generator import SeedGenerator, CostReport
from simtest.seeds.loader import Seed

@pytest.fixture
def fake_openai(monkeypatch):
    class FakeCompletion:
        def __init__(self, content: str):
            self.choices = [type("Msg", (), {"message": type("MsgContent", (), {"content": content})()})()]

    def fake_create(*args, **kwargs):
        return FakeCompletion("This is a fake seed input.")

    monkeypatch.setattr("openai.chat.completions.create", fake_create)

def test_generate_3_seeds_under_cost(fake_openai):
    gen = SeedGenerator(suite="analyze", n=3)
    seeds, cost = gen.generate()

    assert isinstance(seeds, list)
    assert all(isinstance(s, Seed) for s in seeds)
    assert len(seeds) == 3
    assert isinstance(cost, CostReport)
    assert cost.total_cost <= 1.00
    assert cost.total_tokens > 0
