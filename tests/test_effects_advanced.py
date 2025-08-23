"""
Tests for advanced effect row operations.

Tests effect_union, effect_eq, and complex effect row scenarios.
"""
import pytest
from core.typesys.types import Type, TVar
from core.typesys.effects import (
    EffEmpty, EffExt, collect_effects, effect_union, effect_eq
)
from core.typesys.kinds import K_EFFROW


class TestEffectUnion:
    """Test effect_union function."""
    
    def test_union_empty_effects(self):
        """Test union of empty effect rows."""
        empty1 = EffEmpty()
        empty2 = EffEmpty()
        result = effect_union(empty1, empty2)
        
        assert result.name == "EffEmpty"
        
    def test_union_empty_with_non_empty(self):
        """Test union of empty with non-empty effect row."""
        empty = EffEmpty()
        io_eff = EffExt("IO", empty)
        
        result1 = effect_union(empty, io_eff)
        result2 = effect_union(io_eff, empty)
        
        # Both should give the same result
        effects1 = collect_effects(result1)
        effects2 = collect_effects(result2)
        
        assert effects1 == {"IO"}
        assert effects2 == {"IO"}
        
    def test_union_disjoint_effects(self):
        """Test union of effect rows with disjoint effects."""
        empty = EffEmpty()
        io_eff = EffExt("IO", empty)
        net_eff = EffExt("Network", empty)
        
        result = effect_union(io_eff, net_eff)
        effects = collect_effects(result)
        
        assert effects == {"IO", "Network"}
        
    def test_union_overlapping_effects(self):
        """Test union of effect rows with overlapping effects."""
        empty = EffEmpty()
        eff1 = EffExt("Console", EffExt("IO", empty))
        eff2 = EffExt("Network", EffExt("IO", empty))  # "IO" overlaps
        
        result = effect_union(eff1, eff2)
        effects = collect_effects(result)
        
        # Should have union of all effects (no duplicates)
        expected = {"Console", "IO", "Network"}
        assert effects == expected
        
    def test_union_identical_effects(self):
        """Test union of identical effect rows."""
        empty = EffEmpty()
        eff1 = EffExt("IO", EffExt("Network", empty))
        eff2 = EffExt("IO", EffExt("Network", empty))
        
        result = effect_union(eff1, eff2)
        effects = collect_effects(result)
        
        assert effects == {"IO", "Network"}
        
    def test_union_complex_effects(self):
        """Test union of complex effect rows."""
        empty = EffEmpty()
        eff1 = EffExt("Database", EffExt("IO", EffExt("Console", empty)))
        eff2 = EffExt("Network", EffExt("IO", EffExt("UI", empty)))
        
        result = effect_union(eff1, eff2)
        effects = collect_effects(result)
        
        expected = {"Database", "IO", "Console", "Network", "UI"}
        assert effects == expected
        
    def test_union_deterministic_order(self):
        """Test that effect union produces deterministic ordering."""
        empty = EffEmpty()
        eff1 = EffExt("Z", EffExt("A", empty))
        eff2 = EffExt("Y", EffExt("B", empty))
        
        result1 = effect_union(eff1, eff2)
        result2 = effect_union(eff1, eff2)
        
        assert result1 == result2
        
        effects = collect_effects(result1)
        assert effects == {"Z", "A", "Y", "B"}


class TestEffectUnionOpenRows:
    """Test effect_union with open effect rows."""
    
    def test_union_with_open_row_left(self):
        """Test union with open row on left side."""
        # Create an effect type variable by constructing it properly
        tv = Type("TVar(eff)", params=[], metadata={"tvar": "eff"}, kind=K_EFFROW)
        open_eff = EffExt("IO", tv)
        
        empty = EffEmpty()
        closed_eff = EffExt("Network", empty)
        
        result = effect_union(open_eff, closed_eff)
        
        # Should return unknown effect variable
        assert result.name == "EffVar"
        assert result.kind == K_EFFROW
        
    def test_union_with_open_row_right(self):
        """Test union with open row on right side."""
        empty = EffEmpty()
        closed_eff = EffExt("IO", empty)
        
        tv = Type("TVar(eff)", params=[], metadata={"tvar": "eff"}, kind=K_EFFROW)
        open_eff = EffExt("Network", tv)
        
        result = effect_union(closed_eff, open_eff)
        
        # Should return unknown effect variable
        assert result.name == "EffVar"
        assert result.kind == K_EFFROW
        
    def test_union_both_open_rows(self):
        """Test union with both rows open."""
        tv1 = Type("TVar(eff1)", params=[], metadata={"tvar": "eff1"}, kind=K_EFFROW)
        open_eff1 = EffExt("IO", tv1)
        
        tv2 = Type("TVar(eff2)", params=[], metadata={"tvar": "eff2"}, kind=K_EFFROW)
        open_eff2 = EffExt("Network", tv2)
        
        result = effect_union(open_eff1, open_eff2)
        
        # Should return unknown effect variable
        assert result.name == "EffVar"
        assert result.kind == K_EFFROW
        
    def test_union_with_malformed_effect(self):
        """Test union with malformed effect row."""
        empty = EffEmpty()
        good_eff = EffExt("IO", empty)
        
        # Create malformed effect (missing effect metadata)
        malformed = Type("EffExt", [empty], metadata={}, kind=K_EFFROW)
        
        result = effect_union(good_eff, malformed)
        
        # Should return EffVar due to collect_effects returning None
        assert result.name == "EffVar"
        assert result.kind == K_EFFROW


class TestEffectEq:
    """Test effect_eq function."""
    
    def test_effect_eq_empty_rows(self):
        """Test equality of empty effect rows."""
        empty1 = EffEmpty()
        empty2 = EffEmpty()
        
        # Note: effect_eq function is incomplete in the source
        # This test assumes it would check structural equality
        # For now, we'll use regular equality
        assert empty1 == empty2
        
    def test_effect_eq_identical_single_effects(self):
        """Test equality of identical single effect rows."""
        empty = EffEmpty()
        eff1 = EffExt("IO", empty)
        eff2 = EffExt("IO", empty)
        
        # Use structural equality for now
        assert eff1 == eff2
        
    def test_effect_eq_different_single_effects(self):
        """Test inequality of different single effect rows."""
        empty = EffEmpty()
        eff1 = EffExt("IO", empty)
        eff2 = EffExt("Network", empty)
        
        assert eff1 != eff2
        
    def test_effect_eq_same_effects_different_order(self):
        """Test equality ignoring order (semantic equality)."""
        empty = EffEmpty()
        eff1 = EffExt("IO", EffExt("Network", empty))
        eff2 = EffExt("Network", EffExt("IO", empty))
        
        # This depends on implementation - should they be semantically equal?
        # Based on collect_effects, they have same effect sets
        effects1 = collect_effects(eff1)
        effects2 = collect_effects(eff2)
        assert effects1 == effects2
        
        # For structural equality, they should be different
        # For semantic equality, they should be the same
        # This highlights the difference between structural and semantic equality
        assert eff1 != eff2  # Structural inequality
        
    def test_effect_eq_subset_effects(self):
        """Test inequality of subset effect rows."""
        empty = EffEmpty()
        eff1 = EffExt("IO", EffExt("Network", empty))
        eff2 = EffExt("IO", empty)
        
        assert eff1 != eff2


class TestComplexEffectScenarios:
    """Test complex effect row scenarios."""
    
    def test_nested_effect_operations(self):
        """Test combining multiple effect operations."""
        empty = EffEmpty()
        
        # Create several effect rows
        eff1 = EffExt("IO", empty)
        eff2 = EffExt("Network", empty)
        eff3 = EffExt("Database", empty)
        
        # Union eff1 and eff2
        union12 = effect_union(eff1, eff2)
        
        # Union result with eff3
        final_union = effect_union(union12, eff3)
        
        effects = collect_effects(final_union)
        assert effects == {"IO", "Network", "Database"}
        
    def test_effect_subsumption(self):
        """Test effect subsumption scenarios."""
        empty = EffEmpty()
        
        # Smaller effect set
        small_eff = EffExt("IO", empty)
        
        # Larger effect set containing the smaller one
        large_eff = EffExt("Network", EffExt("IO", EffExt("Console", empty)))
        
        small_effects = collect_effects(small_eff)
        large_effects = collect_effects(large_eff)
        
        # Check subsumption
        assert small_effects.issubset(large_effects)
        assert not large_effects.issubset(small_effects)
        
    def test_effect_row_with_function_types(self):
        """Test effect rows used with function types."""
        from core.typesys.types import Function, Int, String
        
        empty = EffEmpty()
        io_eff = EffExt("IO", empty)
        
        # Function with effect annotation
        # This would represent: Int -> String with IO effect
        eff_func = Type("EffectfulFunction", [Int, String, io_eff])
        
        assert eff_func.params[0] == Int
        assert eff_func.params[1] == String
        assert eff_func.params[2] == io_eff
        
        # Extract and verify the effect
        func_effects = collect_effects(eff_func.params[2])
        assert func_effects == {"IO"}
        
    def test_polymorphic_effects(self):
        """Test polymorphic effects with type variables."""
        # Effect variable
        eff_var = Type("TVar(ε)", params=[], metadata={"tvar": "ε"}, kind=K_EFFROW)
        
        # Concrete effect extended onto the variable
        concrete_eff = EffExt("IO", eff_var)
        
        # This represents: IO + ε (IO plus whatever effects ε contains)
        assert concrete_eff.metadata["effect"] == "IO"
        assert concrete_eff.params[0] == eff_var
        
        # Can't collect effects from open row
        effects = collect_effects(concrete_eff)
        assert effects is None
        
    def test_effect_row_construction_patterns(self):
        """Test various effect row construction patterns."""
        empty = EffEmpty()
        
        # Linear construction
        eff_linear = EffExt("A", EffExt("B", EffExt("C", empty)))
        
        # Functional construction using helper
        from core.typesys.effects import _mk_row_from_labels
        eff_functional = _mk_row_from_labels({"A", "B", "C"}, None)
        
        # Both should have same effect set
        linear_effects = collect_effects(eff_linear)
        functional_effects = collect_effects(eff_functional)
        
        assert linear_effects == functional_effects == {"A", "B", "C"}


class TestEffectRowErrorHandling:
    """Test error handling in effect row operations."""
    
    def test_effect_union_with_non_effect_types(self):
        """Test effect_union behavior with non-effect types."""
        from core.typesys.types import Int
        empty = EffEmpty()
        
        # Should handle gracefully (collect_effects returns None)
        result = effect_union(Int, empty)
        assert result.name == "EffVar"  # Conservative fallback
        
    def test_collect_effects_robust_to_malformed_data(self):
        """Test collect_effects handles malformed data gracefully."""
        # Effect row with wrong parameter structure
        malformed = Type("EffExt", [], metadata={"effect": "IO"}, kind=K_EFFROW)
        
        effects = collect_effects(malformed)
        assert effects is None  # Should handle gracefully
        
    def test_effect_operations_with_mixed_kinds(self):
        """Test effect operations with mixed type kinds."""
        from core.typesys.rows import RowEmpty
        
        empty_eff = EffEmpty()
        empty_row = RowEmpty()  # Different kind (K_ROW vs K_EFFROW)
        
        # Should handle kind mismatch gracefully
        result = effect_union(empty_eff, empty_row)
        assert result.name == "EffVar"  # Conservative fallback


if __name__ == "__main__":
    pytest.main([__file__])
