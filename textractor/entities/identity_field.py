class IdentityField:
    def __init__(self, key, value, confidence):
        self._key = key
        self._value = value
        self._confidence = confidence

    @property
    def key(self) -> str:
        return self._key

    @property
    def value(self) -> str:
        return self._value

    @property
    def confidence(self) -> float:
        return self._confidence

    def __repr__(self) -> str:
        return self.value
