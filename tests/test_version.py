"""Basic test to ensure the package can be imported."""

import capstone_finance


def test_version():
    """Test that the package has a version."""
    assert hasattr(capstone_finance, "__version__")
    assert capstone_finance.__version__ == "0.0.0"


def test_imports():
    """Test that the package can be imported."""
    assert capstone_finance.VERSION == "0.0.0"
