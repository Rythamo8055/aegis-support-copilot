from aegis import __version__


def test_package_imports() -> None:
    assert isinstance(__version__, str)
    assert __version__ == "0.1.0"


def test_langgraph_importable() -> None:
    import langgraph

    assert langgraph is not None
