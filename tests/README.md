# Typesystem Test Suite

Comprehensive test suite for the `core.typesys` module of simpleton-computer.

## Test Structure

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── test_types_basic.py         # Basic Type class functionality  
├── test_types_containers.py    # Container type constructors
├── test_types_unification.py   # Unification algorithm
├── test_rows_basic.py          # Row type construction
├── test_rows_collection.py     # Row collection and manipulation
├── test_effects_basic.py       # Effect row construction
├── test_effects_advanced.py    # Advanced effect operations
└── README.md                   # This file
```

## Test Coverage

### Basic Types (`test_types_basic.py`)
- ✅ Type construction and properties
- ✅ Type equality and hashing  
- ✅ String representation
- ✅ Builtin types (Int, String, Bool, etc.)
- ✅ Type variables (TVar)
- ✅ Occurs check functionality

### Container Types (`test_types_containers.py`)
- ✅ Basic containers (List, Option, Set)
- ✅ Tuple types (empty, single, multiple elements)
- ✅ Function types (simple, higher-order)
- ✅ Map types (simple, nested)
- ✅ Record and Variant type constructors
- ✅ Range types with metadata
- ✅ Context type wrapper
- ✅ Effect types (IO, Network, UI)
- ✅ Pattern types (Maybe, Either, Stream, Promise)
- ✅ Complex type compositions

### Unification (`test_types_unification.py`)
- ✅ Basic unification (identical, different types)
- ✅ Top type unification (universal)
- ✅ Type variable unification
- ✅ Occurs check prevention of infinite types
- ✅ Parameterized type unification
- ✅ Function type unification
- ✅ Context unwrapping during unification
- ✅ Complex unification scenarios
- ✅ Edge cases and error conditions

### Row Types (`test_rows_basic.py`)
- ✅ RowEmpty construction
- ✅ RowExt construction and chaining
- ✅ Kind assertion enforcement
- ✅ Rec (record) syntactic sugar
- ✅ Case (variant) syntactic sugar
- ✅ Record vs Variant type differences
- ✅ Nested record/variant structures

### Row Operations (`test_rows_collection.py`)
- ✅ CollectedRow dataclass functionality
- ✅ collect_row function (closed and open rows)
- ✅ get_label_type field lookup
- ✅ row_subtract operation
- ✅ row_union operation  
- ✅ Error handling for malformed rows
- ✅ Integration between operations

### Effect System (`test_effects_basic.py`)
- ✅ EffEmpty construction
- ✅ EffExt construction and chaining
- ✅ collect_effects functionality
- ✅ has_effect checking
- ✅ Effect row helper functions
- ✅ Integration with type system

### Advanced Effects (`test_effects_advanced.py`)
- ✅ effect_union operations
- ✅ Open effect row handling
- ✅ Complex effect scenarios
- ✅ Polymorphic effects with type variables
- ✅ Effect subsumption
- ✅ Error handling and robustness

## Running Tests

### All Tests
```bash
python run_tests.py
```

### Specific Categories
```bash
python run_tests.py basic        # Basic type tests
python run_tests.py containers   # Container type tests
python run_tests.py unification  # Unification tests
python run_tests.py rows         # Row type tests
python run_tests.py effects      # Effect system tests
```

### With Coverage
```bash
python run_tests.py --coverage
```

### Using Pytest Directly
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_types_basic.py -v

# With markers
pytest tests/ -v -m "not slow"
```

## Test Philosophy

### Comprehensive Coverage
- Tests cover both happy path and error conditions
- Edge cases and boundary conditions are tested
- Integration between modules is verified

### Clear Structure
- Each test class focuses on a specific aspect
- Test methods have descriptive names and docstrings
- Related tests are grouped logically

### Robust Assertions
- Tests verify both primary behavior and side effects
- Error conditions are explicitly tested
- Type safety and invariants are checked

### Documentation Value
- Tests serve as executable documentation
- Complex scenarios are explained with comments
- Usage patterns are demonstrated

## Fixtures

The `conftest.py` provides common fixtures:

- `basic_types`: Common basic types (Int, String, Bool, Float)
- `type_vars`: Common type variables (a, b, c)
- `sample_rows`: Sample row structures
- `sample_effects`: Sample effect rows

## Notes

### Incomplete Features
- Subtyping functionality is stubbed out (`subtype.py`)
- Some effect operations (`effect_eq`) are incomplete
- Tests are designed to be extended as features are implemented

### Design Patterns
- Tests demonstrate proper usage of the type system
- Error handling patterns are shown
- Performance considerations are noted where relevant

### Future Extensions
- Property-based testing with Hypothesis
- Performance benchmarks
- Integration tests with larger type expressions
- Serialization/deserialization tests
