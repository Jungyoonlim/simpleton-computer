"""
Pytest configuration and common fixtures for typesystem tests.
"""
import pytest
import sys
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.typesys.types import TVar  # noqa: E402
from core.typesys.rows import RowEmpty, RowExt  # noqa: E402
from core.typesys.effects import EffEmpty, EffExt  # noqa: E402

@pytest.fixture
def basic_types():
    """Fixture providing common basic types for testing."""
    from core.typesys.types import Int, String, Bool, Float
    return {
        'int': Int,
        'string': String, 
        'bool': Bool,
        'float': Float
    }

@pytest.fixture  
def type_vars():
    """Fixture providing common type variables."""
    return {
        'a': TVar('a'),
        'b': TVar('b'), 
        'c': TVar('c')
    }

@pytest.fixture
def sample_rows():
    """Fixture providing sample row types."""
    from core.typesys.types import Int, String
    return {
        'empty': RowEmpty(),
        'single': RowExt('x', Int, RowEmpty()),
        'multi': RowExt('name', String, RowExt('age', Int, RowEmpty()))
    }

@pytest.fixture
def sample_effects():
    """Fixture providing sample effect rows."""
    return {
        'empty': EffEmpty(),
        'io': EffExt('IO', EffEmpty()),
        'io_net': EffExt('Network', EffExt('IO', EffEmpty()))
    }
