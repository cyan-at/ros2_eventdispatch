"""CompletionHarness: the generic completion -> decision ->
submission loop for a staged events module.

This loop is seam machinery, not boundary behavior, so it
lives in the carrier, parameterized by the staged events:
the events module provides a decider (its optional
make_decider(blackboard, node) factory — the phase's
decision wiring, e.g. a frozen policy reused by import),
and this class provides everything else:

  * consume the completions field (the CompletionLog the
    TrainingDispatch registers on the blackboard under
    "training_completions") by take() — the library's one
    read path;
  * hand each wake record to the decider; a decider return
    of None submits nothing;
  * submit a returned payload onto the dispatch's queue
    with the library's queue-and-notify producer pattern;
  * bootstrap: before any completion exists there is no
    record to decide from, so once the blackboard reports
    its first sensor input (blackboard["scan_seen"], set by
    the staged module's own hooks) the decider is called
    once with record=None.

Payloads are the dispatch's serialized form,
[class_name, *args] — for ROSEvent-staged modules the
5-element [class_name, string_tail, int_array, float_array,
hash] convention. The decider owns that shape; this class
only moves it.

No ROS imports: the harness is driven entirely off the
blackboard and the dispatch object, so it is testable
without rclpy.
"""
from __future__ import annotations

import threading

COMPLETIONS_KEY = "training_completions"


class CompletionHarness:
    """take() -> decider -> queue-and-notify, on a thread."""

    def __init__(self, blackboard, dispatch, decider):
        self.blackboard = blackboard
        self.dispatch = dispatch
        self.decider = decider
        self.bootstrapped = False
        self.records_seen = 0
        self._stop = threading.Event()
        self._thread = None

    # -- submission (the library's producer pattern) -------------
    def submit(self, payload):
        bb, ed = self.blackboard, self.dispatch
        with bb[ed.cv_name]:
            bb[ed.queue_name].append(payload)
            bb[ed.cv_name].notify(1)

    # -- one pass ---------------------------------------------------
    def step_once(self, timeout=0.0):
        """Drain the completions field once and decide on each
        record. Returns the records consumed. Also performs
        the bootstrap call when its precondition first holds."""
        log = self.blackboard[COMPLETIONS_KEY]
        records = log.take(timeout=timeout)
        for record in records:
            self.records_seen += 1
            if not record.get("wake", True):
                continue
            payload = self.decider(record)
            if payload is not None:
                self.submit(payload)
        if not self.bootstrapped \
                and self.blackboard.get("scan_seen"):
            self.bootstrapped = True
            payload = self.decider(None)
            if payload is not None:
                self.submit(payload)
        return records

    # -- thread ------------------------------------------------------
    def run(self):
        while not self._stop.is_set():
            self.step_once(timeout=0.5)

    def start(self):
        if self._thread is None:
            self._thread = threading.Thread(
                target=self.run, daemon=True,
                name="completion_harness")
            self._thread.start()
        return self._thread

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
