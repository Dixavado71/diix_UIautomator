from ui_automator.element_finder import ElementFinder


class DummyElement:
    def __init__(self):
        self.wait_calls = 0

    def wait(self, timeout=0):
        self.wait_calls += 1
        return self.wait_calls >= 2

    @property
    def exists(self):
        return self.wait_calls >= 2

    def click(self):
        return True

    @property
    def info(self):
        return {"text": "ready"}


class DummyDevice:
    def __init__(self):
        self.element = DummyElement()

    def __call__(self, **kwargs):
        return self.element


def test_find_waits_for_transient_element():
    finder = ElementFinder(DummyDevice())
    element = finder.find({"text": "ready"}, timeout=2)

    assert element is not None
    assert element.wait_calls >= 2
    assert element.exists is True


def test_find_tries_next_selector_candidate():
    class CandidateDevice:
        def __init__(self):
            self.element = DummyElement()

        def __call__(self, **kwargs):
            if kwargs.get("text") == "ready":
                return self.element
            raise RuntimeError("not found")

    finder = ElementFinder(CandidateDevice())
    element = finder.find([{"resourceId": "missing-id"}, {"text": "ready"}], timeout=1)

    assert element is not None
