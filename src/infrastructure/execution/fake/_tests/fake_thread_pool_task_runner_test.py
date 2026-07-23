"""Tests for FakeThreadPoolTaskRunner — verifies Fake respects IAsyncTaskRunner contract."""

import unittest

from infrastructure.execution.fake.fake_thread_pool_task_runner import FakeThreadPoolTaskRunner


class TestFakeThreadPoolTaskRunner(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = FakeThreadPoolTaskRunner()

    def test_submit_executes_callable_synchronously(self) -> None:
        called = []
        self.runner.submit(lambda: called.append(1))
        self.assertEqual(called, [1])

    def test_task_handle_is_not_running_after_submit(self) -> None:
        handle = self.runner.submit(lambda: None)
        self.assertFalse(handle.is_running())

    def test_wait_on_completed_handle_is_noop(self) -> None:
        handle = self.runner.submit(lambda: None)
        handle.wait(timeout=0.0)  # must not raise or block

    def test_multiple_submits_execute_in_order(self) -> None:
        order = []
        self.runner.submit(lambda: order.append("a"))
        self.runner.submit(lambda: order.append("b"))
        self.runner.submit(lambda: order.append("c"))
        self.assertEqual(order, ["a", "b", "c"])

    def test_callable_exception_propagates(self) -> None:
        def boom():
            raise ValueError("test error")

        with self.assertRaises(ValueError):
            self.runner.submit(boom)


if __name__ == "__main__":
    unittest.main()
