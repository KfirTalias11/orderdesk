from importlib.util import find_spec


def test_application_service_exists():
    assert find_spec('app.main') is not None, 'Order API is not implemented yet'
