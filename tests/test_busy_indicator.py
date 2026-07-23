import unittest

from busy_indicator import busy_cursor


class DummyApplication:
    current = object()
    events = []

    @classmethod
    def instance(cls):
        return cls.current

    @classmethod
    def setOverrideCursor(cls, cursor):
        cls.events.append(("set", cursor))

    @classmethod
    def restoreOverrideCursor(cls):
        cls.events.append(("restore", None))


class TestBusyCursor(unittest.TestCase):
    def setUp(self):
        DummyApplication.current = object()
        DummyApplication.events = []

    def test_cursor_is_set_and_restored(self):
        with busy_cursor(DummyApplication):
            self.assertEqual(DummyApplication.events[0][0], "set")

        self.assertEqual(
            [event[0] for event in DummyApplication.events],
            ["set", "restore"],
        )

    def test_cursor_is_restored_after_exception(self):
        with self.assertRaisesRegex(RuntimeError, "failed"):
            with busy_cursor(DummyApplication):
                raise RuntimeError("failed")

        self.assertEqual(DummyApplication.events[-1][0], "restore")

    def test_no_application_instance_is_a_no_op(self):
        DummyApplication.current = None

        with busy_cursor(DummyApplication):
            pass

        self.assertEqual(DummyApplication.events, [])


if __name__ == "__main__":
    unittest.main()
