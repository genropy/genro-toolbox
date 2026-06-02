"""Sentinel singletons for marking special argument states."""


class _Mandatory:
    """Sentinel: 'you must provide a value here'.

    Distinct from None (a legit value). Used as a parameter default to
    mark it mandatory while still allowing positional/keyword passing;
    the dispatch raises if the argument is left as MANDATORY.
    """

    _instance: "_Mandatory | None" = None

    def __new__(cls) -> "_Mandatory":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "MANDATORY"

    def __bool__(self) -> bool:
        return False


MANDATORY = _Mandatory()


if __name__ == "__main__":
    print(repr(MANDATORY))
    print(bool(MANDATORY))
    print(_Mandatory() is MANDATORY)
