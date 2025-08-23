"""
Tests for basic row type construction.

Tests RowEmpty, RowExt, Rec (record sugar), and Case (variant sugar) constructors.
"""
import pytest
from core.typesys.types import Type, Int, String, Bool, Float, Record, Variant
from core.typesys.rows import (
    RowEmpty, RowExt, Rec, Case, _assert_row_kind
)
from core.typesys.kinds import K_ROW


class TestRowEmpty:
    """Test RowEmpty constructor."""
    
    def test_row_empty_construction(self):
        """Test RowEmpty creates correct type."""
        empty = RowEmpty()
        assert empty.name == "RowEmpty"
        assert empty.params == []
        assert empty.kind == K_ROW
        assert empty.metadata == {}
        
    def test_row_empty_equality(self):
        """Test RowEmpty equality."""
        empty1 = RowEmpty()
        empty2 = RowEmpty()
        assert empty1 == empty2
        assert hash(empty1) == hash(empty2)
        
    def test_row_empty_string_representation(self):
        """Test RowEmpty string representation."""
        empty = RowEmpty()
        assert str(empty) == "RowEmpty"


class TestRowExt:
    """Test RowExt constructor."""
    
    def test_row_ext_construction(self):
        """Test RowExt creates correct type."""
        empty = RowEmpty()
        ext = RowExt("x", Int, empty)
        
        assert ext.name == "RowExt"
        assert ext.kind == K_ROW
        assert len(ext.params) == 2
        assert ext.params[0] == Int  # field type
        assert ext.params[1] == empty  # tail
        assert ext.metadata["label"] == "x"
        
    def test_row_ext_chaining(self):
        """Test chaining multiple RowExt constructions."""
        empty = RowEmpty()
        row1 = RowExt("x", Int, empty)
        row2 = RowExt("y", String, row1)
        
        assert row2.metadata["label"] == "y"
        assert row2.params[0] == String
        assert row2.params[1] == row1
        
    def test_row_ext_kind_assertion(self):
        """Test that RowExt enforces tail to be Row kind."""
        # This should work - tail is Row kind
        empty = RowEmpty()
        RowExt("x", Int, empty)  # Should not raise
        
        # This should fail - tail is not Row kind
        with pytest.raises(AssertionError):
            RowExt("x", Int, Int)  # Int has K_TYPE kind, not K_ROW
            
    def test_row_ext_equality(self):
        """Test RowExt equality."""
        empty = RowEmpty()
        ext1 = RowExt("x", Int, empty)
        ext2 = RowExt("x", Int, empty)
        ext3 = RowExt("y", Int, empty)  # different label
        ext4 = RowExt("x", String, empty)  # different type
        
        assert ext1 == ext2
        assert ext1 != ext3
        assert ext1 != ext4


class TestAssertRowKind:
    """Test the _assert_row_kind helper function."""
    
    def test_assert_row_kind_success(self):
        """Test _assert_row_kind with valid Row kind."""
        empty = RowEmpty()
        _assert_row_kind(empty)  # Should not raise
        
        ext = RowExt("x", Int, empty)
        _assert_row_kind(ext)  # Should not raise
        
    def test_assert_row_kind_failure(self):
        """Test _assert_row_kind with invalid kind."""
        with pytest.raises(AssertionError):
            _assert_row_kind(Int)  # Int has K_TYPE kind
            
        with pytest.raises(AssertionError):
            from core.typesys.effects import EffEmpty
            _assert_row_kind(EffEmpty())  # EffEmpty has K_EFFROW kind


class TestRecSugar:
    """Test Rec (record) syntactic sugar."""
    
    def test_empty_record(self):
        """Test empty record construction."""
        rec = Rec()
        assert rec.name == "Record"
        assert len(rec.params) == 1
        
        # The parameter should be a RowEmpty
        row = rec.params[0]
        assert row.name == "RowEmpty"
        assert row.kind == K_ROW
        
    def test_single_field_record(self):
        """Test single field record."""
        rec = Rec(x=Int)
        assert rec.name == "Record"
        
        # Should create Record(RowExt("x", Int, RowEmpty()))
        row = rec.params[0]
        assert row.name == "RowExt"
        assert row.metadata["label"] == "x"
        assert row.params[0] == Int
        assert row.params[1].name == "RowEmpty"
        
    def test_multi_field_record(self):
        """Test multi-field record construction."""
        rec = Rec(name=String, age=Int, active=Bool)
        row = rec.params[0]
        
        # Should be nested RowExt structures
        assert row.name == "RowExt"
        
        # Collect all labels by traversing the row
        labels = []
        current = row
        while current.name == "RowExt":
            labels.append(current.metadata["label"])
            current = current.params[1]
        
        # Should have all three labels (order might vary due to dict iteration)
        assert set(labels) == {"name", "age", "active"}
        assert current.name == "RowEmpty"
        
    def test_record_field_types(self):
        """Test that record preserves field types correctly."""
        rec = Rec(x=Int, y=String)
        
        # Extract field information by walking the row
        fields = {}
        current = rec.params[0]
        while current.name == "RowExt":
            label = current.metadata["label"]
            field_type = current.params[0]
            fields[label] = field_type
            current = current.params[1]
            
        assert fields["x"] == Int
        assert fields["y"] == String
        
    def test_record_deterministic_order(self):
        """Test that record construction is deterministic."""
        # Due to reversed() in implementation, should be deterministic
        rec1 = Rec(a=Int, b=String)
        rec2 = Rec(a=Int, b=String)
        assert rec1 == rec2


class TestCaseSugar:
    """Test Case (variant) syntactic sugar."""
    
    def test_empty_variant(self):
        """Test empty variant construction."""
        var = Case({})
        assert var.name == "Variant"
        assert len(var.params) == 1
        
        # The parameter should be a RowEmpty
        row = var.params[0]
        assert row.name == "RowEmpty"
        assert row.kind == K_ROW
        
    def test_single_case_variant(self):
        """Test single case variant."""
        var = Case({"Just": Int})
        assert var.name == "Variant"
        
        # Should create Variant(RowExt("Just", Int, RowEmpty()))
        row = var.params[0]
        assert row.name == "RowExt"
        assert row.metadata["label"] == "Just"
        assert row.params[0] == Int
        assert row.params[1].name == "RowEmpty"
        
    def test_multi_case_variant(self):
        """Test multi-case variant construction."""
        var = Case({"Left": Int, "Right": String, "Middle": Bool})
        row = var.params[0]
        
        # Should be nested RowExt structures
        assert row.name == "RowExt"
        
        # Collect all cases by traversing the row
        cases = {}
        current = row
        while current.name == "RowExt":
            label = current.metadata["label"]
            case_type = current.params[0]
            cases[label] = case_type
            current = current.params[1]
            
        # Should have all three cases
        assert set(cases.keys()) == {"Left", "Right", "Middle"}
        assert cases["Left"] == Int
        assert cases["Right"] == String
        assert cases["Middle"] == Bool
        assert current.name == "RowEmpty"
        
    def test_variant_deterministic_order(self):
        """Test that variant construction is deterministic."""
        var1 = Case({"A": Int, "B": String})
        var2 = Case({"A": Int, "B": String})
        assert var1 == var2


class TestRecordVsVariantTypes:
    """Test integration between records, variants, and type system."""
    
    def test_record_is_record_type(self):
        """Test that Rec creates Record type."""
        rec = Rec(x=Int)
        assert isinstance(rec, Type)
        assert rec.name == "Record"
        
    def test_variant_is_variant_type(self):
        """Test that Case creates Variant type."""
        var = Case({"A": Int})
        assert isinstance(var, Type)
        assert var.name == "Variant"
        
    def test_record_variant_different(self):
        """Test that records and variants with same fields are different."""
        rec = Rec(x=Int)
        var = Case({"x": Int})
        assert rec != var
        assert rec.name == "Record"
        assert var.name == "Variant"
        
    def test_nested_record_variant(self):
        """Test records containing variants and vice versa."""
        # Record with variant field
        var_field = Case({"A": Int, "B": String})
        rec_with_var = Rec(choice=var_field, id=Int)
        
        assert rec_with_var.name == "Record"
        
        # Extract the variant field type
        row = rec_with_var.params[0]
        choice_field = None
        current = row
        while current.name == "RowExt":
            if current.metadata["label"] == "choice":
                choice_field = current.params[0]
                break
            current = current.params[1]
            
        assert choice_field is not None
        assert choice_field.name == "Variant"


class TestRowStringRepresentation:
    """Test string representations of row types."""
    
    def test_row_ext_string_representation(self):
        """Test RowExt string representation."""
        empty = RowEmpty()
        ext = RowExt("x", Int, empty)
        # String representation will depend on Type.__str__ implementation
        assert "RowExt" in str(ext)
        
    def test_record_string_representation(self):
        """Test Record string representation."""
        rec = Rec(x=Int, y=String)
        assert "Record" in str(rec)
        
    def test_variant_string_representation(self):
        """Test Variant string representation."""
        var = Case({"A": Int, "B": String})
        assert "Variant" in str(var)


if __name__ == "__main__":
    pytest.main([__file__])
