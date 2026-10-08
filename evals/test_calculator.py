import pytest

from evals.assertions import assert_expectations
from evals.runner import run_case
from resources.loader import load_cases

CASES = load_cases("evals/cases/calculator.yaml")


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_calculator(case, make_agent):
    agent = make_agent()
    reply, messages = run_case(agent, case)
    assert_expectations(reply, messages, case["expect"])
