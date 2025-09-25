# ruff: noqa
def test():
    a = "abc"
    "def"
    pass


def main():
    """Just a docstring."""
    test()

    """
    Allowed multi-line comment!
    """

    b = "zzz"
    f"yyy"
    z = 2
    assert True, "multi-line "
    f"assertion string {z}"

    c = 5

    """What about single-line comments with triples."""

    d = 5


main()
# should put 3 issues (line 4, 17 and 20)
