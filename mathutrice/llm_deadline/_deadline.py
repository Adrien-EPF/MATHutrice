"""One deadline over every LLM call of one evaluation test.

The client is given by the caller, never imported here. Each call is given only
the time left, through the client's timeout, and no retry: a retry would start
its own timeout over and the deadline would no longer hold.
"""

import time

from openai import APITimeoutError

# Five minutes: assumption D of the Design Document, how long a student waits
# before giving up.
EVALUATION_DEADLINE_SECONDS = 300


class DeadlineExceeded(Exception):
    """The test's deadline has passed, or a call ran out of the time left."""


class LLMDeadline:
    def __init__(self, client, model, *, clock=time.monotonic):
        self._client = client
        self._model = model
        self._clock = clock
        self._deadline = clock() + EVALUATION_DEADLINE_SECONDS

    def complete(self, messages) -> str:
        remaining = self._deadline - self._clock()
        if remaining <= 0:
            raise DeadlineExceeded("The evaluation test's deadline has passed.")
        client = self._client.with_options(timeout=remaining, max_retries=0)
        try:
            response = client.chat.completions.create(
                model=self._model, messages=messages
            )
        except APITimeoutError as error:
            raise DeadlineExceeded("A call ran out of the time left.") from error
        return response.choices[0].message.content
