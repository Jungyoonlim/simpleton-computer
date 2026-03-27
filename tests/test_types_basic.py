"""
Tests for basic Type class functionality.

Tests construction, equality, string representation, and basic properties.
"""
import pytest
from core.typesys.types import (
    Type, TVar, is_tvar, occurs,
    Unit, Bool, Int, String, Float, Bytes, Top, Doc, Comment, Task, Link, Date, Path
)
from core.typesys.kinds import K_TYPE


class TestTypeConstruction:
    """Test Type class construction and basic properties."""
    
    def test_simple_type_construction(self):
        """Test creating simple types without parameters."""
        t = Type("MyType")
        assert t.name == "MyType"
        assert t.params == []
        assert t.metadata == {}
        assert t.kind == K_TYPE
        
    def test_parameterized_type_construction(self):
        """Test creating types with parameters."""
        inner = Type("Inner")
        outer = Type("Outer", [inner])
        assert outer.name == "Outer"
        assert len(outer.params) == 1
        assert outer.params[0] == inner
        
    def test_type_with_metadata(self):
        """Test creating types with metadata."""
        t = Type("MyType", metadata={"py": int, "description": "Integer type"})
        assert t.metadata["py"] is int
        assert t.metadata["description"] == "Integer type"
        
    def test_carrier_property(self):
        """Test the carrier property returns Python type from metadata."""
        t = Type("Int", metadata={"py": int})
        assert t.carrier is int
        
        t_no_carrier = Type("SomeType")
        assert t_no_carrier.carrier is None


class TestTypeEquality:
    """Test Type equality and hashing."""
    
    def test_equal_simple_types(self):
        """Test equality for simple types."""
        t1 = Type("Int")
        t2 = Type("Int")
        assert t1 == t2
        assert hash(t1) == hash(t2)
        
    def test_unequal_simple_types(self):
        """Test inequality for simple types with different names."""
        t1 = Type("Int")
        t2 = Type("String")
        assert t1 != t2
        assert hash(t1) != hash(t2)
        
    def test_equal_parameterized_types(self):
        """Test equality for parameterized types."""
        inner1 = Type("Int")
        inner2 = Type("Int")
        t1 = Type("List", [inner1])
        t2 = Type("List", [inner2])
        assert t1 == t2
        assert hash(t1) == hash(t2)
        
    def test_unequal_parameterized_types_different_params(self):
        """Test inequality for parameterized types with different parameters."""
        t1 = Type("List", [Type("Int")])
        t2 = Type("List", [Type("String")])
        assert t1 != t2
        
    def test_unequal_parameterized_types_different_arity(self):
        """Test inequality for parameterized types with different arity."""
        t1 = Type("Pair", [Type("Int")])
        t2 = Type("Pair", [Type("Int"), Type("String")])
        assert t1 != t2
        
    def test_metadata_not_in_equality(self):
        """Test that metadata doesn't affect equality."""
        t1 = Type("Int", metadata={"py": int})
        t2 = Type("Int", metadata={"description": "integer"})
        t3 = Type("Int")
        assert t1 == t2 == t3
        
    def test_not_equal_to_non_type(self):
        """Test that Type is not equal to non-Type objects."""
        t = Type("Int")
        assert t != "Int"
        assert t != 42
        assert t is not None


class TestTypeStringRepresentation:
    """Test Type string representation."""
    
    def test_simple_type_str(self):
        """Test string representation of simple types."""
        t = Type("Int")
        assert str(t) == "Int"
        assert repr(t) == "Int"
        
    def test_parameterized_type_str(self):
        """Test string representation of parameterized types."""
        inner = Type("Int")
        t = Type("List", [inner])
        assert str(t) == "List[Int]"
        
    def test_multiple_params_str(self):
        """Test string representation with multiple parameters."""
        t1 = Type("Int")
        t2 = Type("String") 
        t = Type("Pair", [t1, t2])
        assert str(t) == "Pair[Int, String]"
        
    def test_nested_params_str(self):
        """Test string representation with nested parameters."""
        inner = Type("List", [Type("Int")])
        outer = Type("List", [inner])
        assert str(outer) == "List[List[Int]]"


class TestBuiltinTypes:
    """Test predefined builtin types."""
    
    def test_builtin_types_exist(self):
        """Test that all expected builtin types exist."""
        builtins = [Unit, Bool, Int, String, Float, Bytes, Top, Doc, Comment, Task, Link, Date, Path]
        for t in builtins:
            assert isinstance(t, Type)
            assert t.params == []
            assert t.kind == K_TYPE
            
    def test_builtin_types_unique(self):
        """Test that builtin types have unique names."""
        builtins = [Unit, Bool, Int, String, Float, Bytes, Top, Doc, Comment, Task, Link, Date, Path]
        names = [t.name for t in builtins]
        assert len(names) == len(set(names))  # All names should be unique


class TestTypeVariables:
    """Test type variables (TVar)."""
    
    def test_tvar_construction(self):
        """Test TVar construction."""
        tv = TVar("a")
        assert tv.name == "TVar(a)"
        assert tv.metadata["tvar"] == "a"
        assert tv.params == []
        
    def test_tvar_identity(self):
        """Test TVar identity and equality."""
        tv1 = TVar("a")
        tv2 = TVar("a")
        tv3 = TVar("b")
        
        # Same variable name should be equal
        assert tv1 == tv2
        assert hash(tv1) == hash(tv2)
        
        # Different variable names should not be equal
        assert tv1 != tv3
        
    def test_is_tvar_predicate(self):
        """Test is_tvar predicate function."""
        tv = TVar("a")
        regular = Type("Int")
        
        assert is_tvar(tv) is True
        assert is_tvar(regular) is False
        
    def test_tvar_str_representation(self):
        """Test TVar string representation."""
        tv = TVar("alpha")
        assert str(tv) == "TVar(alpha)"


class TestOccursCheck:
    """Test occurs check for type variables."""
    
    def test_occurs_direct(self):
        """Test occurs check for direct occurrence."""
        tv = TVar("a")
        assert occurs("a", tv, {}) is True
        
    def test_occurs_not_present(self):
        """Test occurs check when variable is not present."""
        t = Type("Int")
        assert occurs("a", t, {}) is False
        
    def test_occurs_in_parameters(self):
        """Test occurs check in type parameters."""
        tv = TVar("a")
        list_of_a = Type("List", [tv])
        assert occurs("a", list_of_a, {}) is True
        
    def test_occurs_through_substitution(self):
        """Test occurs check through substitution."""
        tv_a = TVar("a")
        tv_b = TVar("b")
        subst = {"b": tv_a}
        
        assert occurs("a", tv_b, subst) is True
        
    def test_occurs_nested_substitution(self):
        """Test occurs check through nested substitution."""
        tv_a = TVar("a")
        tv_b = TVar("b")
        tv_c = TVar("c")
        list_of_a = Type("List", [tv_a])
        subst = {"b": tv_c, "c": list_of_a}
        
        assert occurs("a", tv_b, subst) is True
        
    def test_occurs_no_infinite_loop(self):
        """Test occurs check doesn't create infinite loops."""
        tv_a = TVar("a")
        tv_b = TVar("b")
        # Circular substitution: a -> b, b -> a
        subst = {"a": tv_b, "b": tv_a}
        
        # This should not cause infinite recursion
        # The exact behavior might depend on implementation
        result = occurs("a", tv_a, subst)
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__])
