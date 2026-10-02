"""One deadline over every LLM call of one evaluation test (issue #80).

The number comes from the Design Document (#69): 5 minutes, its assumption D.
The module is given a fake client and a fake clock as arguments. No test waits,
calls a real LLM or patches a global.
"""

import math
from types import SimpleNamespace

import httpx2
import openai
import pytest

from mathutrice.llm_deadline import (
    EVALUATION_DEADLINE_SECONDS,
    DeadlineExceeded,
    LLMDeadline,
)

FIVE_MINUTES = 300
QUESTIONS_IN_THE_LONGEST_TEST = 20
FAST_ANSWER_SECONDS = 2.3  # the Design Document's B, measured


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class FakeLLM:
    """Stands in for the OpenAI client, with the library's own defaults.

    Unless the caller says otherwise, a call may take 600 s and is retried
    twice, as with the real client. The fake advances the clock by what a call
    takes, or by the timeout it was given when the answer comes later than that.
    """

    def __init__(self, clock, seconds_for_call, *, timeout=600, max_retries=2, state=None):
        self.clock = clock
        self.timeout = timeout
        self.max_retries = max_retries
        # Shared by every copy made through with_options.
        self.state = state or SimpleNamespace(
            seconds_for_call=seconds_for_call, calls=0, attempt_starts=[]
        )
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    @property
    def attempt_starts(self):
        return self.state.attempt_starts

    def with_options(self, *, timeout=None, max_retries=None):
        return FakeLLM(
            self.clock,
            None,
            timeout=self.timeout if timeout is None else timeout,
            max_retries=self.max_retries if max_retries is None else max_retries,
            state=self.state,
        )

    def _create(self, *, model, messages, timeout=None, **_):
        seconds = self.state.seconds_for_call(self.state.calls)
        self.state.calls += 1
        allowed = self.timeout if timeout is None else timeout
        for _attempt in range(1 + self.max_retries):
            self.state.attempt_starts.append(self.clock.now)
            if seconds <= allowed:
                self.clock.now += seconds
                message = SimpleNamespace(content=f"answer {self.state.calls}")
                return SimpleNamespace(choices=[SimpleNamespace(message=message)])
            self.clock.now += allowed
        raise openai.APITimeoutError(request=httpx2.Request("POST", "http://localhost"))


def ask_the_longest_test(deadline):
    return [
        deadline.complete([{"role": "user", "content": f"question {number}"}])
        for number in range(QUESTIONS_IN_THE_LONGEST_TEST)
    ]


def test_the_deadline_is_five_minutes():
    assert EVALUATION_DEADLINE_SECONDS == FIVE_MINUTES


@pytest.mark.parametrize(
    "seconds_for_call",
    [
        pytest.param(lambda call: 20, id="20 s per answer"),
        pytest.param(lambda call: 60, id="one minute per answer"),
        pytest.param(lambda call: math.inf if call == 0 else 1, id="the first call hangs"),
    ],
)
def test_a_slow_llm_stops_the_test_at_five_minutes(seconds_for_call):
    clock = FakeClock()
    llm = FakeLLM(clock, seconds_for_call)
    deadline = LLMDeadline(llm, "dummy-model", clock=clock)

    with pytest.raises(DeadlineExceeded):
        ask_the_longest_test(deadline)

    assert clock.now == pytest.approx(FIVE_MINUTES)  # stopped at 5 minutes, not before
    assert all(start < FIVE_MINUTES for start in llm.attempt_starts)  # no call after


def test_a_fast_llm_returns_all_the_questions():
    clock = FakeClock()
    llm = FakeLLM(clock, lambda call: FAST_ANSWER_SECONDS)
    deadline = LLMDeadline(llm, "dummy-model", clock=clock)

    answers = ask_the_longest_test(deadline)

    assert len(answers) == QUESTIONS_IN_THE_LONGEST_TEST
