"""
Tests for container type constructors and composite types.

Tests List, Option, Tuple, Function, Map, Set, Record, Variant, Range, Context,
Effect types (IO, Network, UI), and pattern types (Maybe, Either, Stream, Promise).
"""
import pytest
from core.typesys.types import (
    Type, Int, String, Bool, Float, Top,
    List, Option, Tuple, Function, Map, Set, Record, Variant, Range, Context,
    IO, Network, UI, Effect,
    Maybe, Either, Stream, Promise
)


class TestBasicContainerTypes:
    """Test basic container type constructors."""
    
    def test_list_constructor(self):
        """Test List type constructor."""
        int_list = List(Int)
        assert int_list.name == "List"
        assert len(int_list.params) == 1
        assert int_list.params[0] == Int
        assert str(int_list) == "List[Int]"
        
    def test_option_constructor(self):
        """Test Option type constructor."""
        string_opt = Option(String)
        assert string_opt.name == "Option"
        assert len(string_opt.params) == 1
        assert string_opt.params[0] == String
        assert str(string_opt) == "Option[String]"
        
    def test_set_constructor(self):
        """Test Set type constructor."""
        bool_set = Set(Bool)
        assert bool_set.name == "Set"
        assert len(bool_set.params) == 1
        assert bool_set.params[0] == Bool
        assert str(bool_set) == "Set[Bool]"


class TestTupleTypes:
    """Test Tuple type constructor."""
    
    def test_empty_tuple(self):
        """Test empty tuple construction."""
        empty = Tuple()
        assert empty.name == "Tuple"
        assert empty.params == []
        assert str(empty) == "Tuple"
        
    def test_single_tuple(self):
        """Test single element tuple."""
        single = Tuple(Int)
        assert single.name == "Tuple"
        assert len(single.params) == 1
        assert single.params[0] == Int
        assert str(single) == "Tuple[Int]"
        
    def test_pair_tuple(self):
        """Test two element tuple."""
        pair = Tuple(Int, String)
        assert pair.name == "Tuple"
        assert len(pair.params) == 2
        assert pair.params[0] == Int
        assert pair.params[1] == String
        assert str(pair) == "Tuple[Int, String]"
        
    def test_triple_tuple(self):
        """Test three element tuple."""
        triple = Tuple(Int, String, Bool)
        assert triple.name == "Tuple"
        assert len(triple.params) == 3
        assert str(triple) == "Tuple[Int, String, Bool]"


class TestFunctionTypes:
    """Test Function type constructor."""
    
    def test_simple_function(self):
        """Test simple function type."""
        int_to_string = Function(Int, String)
        assert int_to_string.name == "Function"
        assert len(int_to_string.params) == 2
        assert int_to_string.params[0] == Int
        assert int_to_string.params[1] == String
        assert str(int_to_string) == "Function[Int, String]"
        
    def test_function_with_container_types(self):
        """Test function with container types."""
        list_int = List(Int)
        option_string = Option(String)
        func = Function(list_int, option_string)
        assert str(func) == "Function[List[Int], Option[String]]"
        
    def test_higher_order_function(self):
        """Test higher-order function (function returning function)."""
        inner_func = Function(Int, String)
        outer_func = Function(Bool, inner_func)
        assert str(outer_func) == "Function[Bool, Function[Int, String]]"


class TestMapTypes:
    """Test Map type constructor."""
    
    def test_simple_map(self):
        """Test simple map type."""
        string_to_int = Map(String, Int)
        assert string_to_int.name == "Map"
        assert len(string_to_int.params) == 2
        assert string_to_int.params[0] == String
        assert string_to_int.params[1] == Int
        assert str(string_to_int) == "Map[String, Int]"
        
    def test_nested_map(self):
        """Test nested map type."""
        inner_map = Map(String, Int)
        outer_map = Map(Bool, inner_map)
        assert str(outer_map) == "Map[Bool, Map[String, Int]]"


class TestRecordAndVariantTypes:
    """Test Record and Variant type constructors."""
    
    def test_record_constructor(self):
        """Test Record type constructor."""
        # Record takes a row type as parameter
        from core.typesys.rows import RowEmpty
        empty_row = RowEmpty()
        rec = Record(empty_row)
        assert rec.name == "Record"
        assert len(rec.params) == 1
        assert rec.params[0] == empty_row
        
    def test_variant_constructor(self):
        """Test Variant type constructor."""
        from core.typesys.rows import RowEmpty
        empty_row = RowEmpty()
        var = Variant(empty_row)
        assert var.name == "Variant"
        assert len(var.params) == 1
        assert var.params[0] == empty_row


class TestRangeTypes:
    """Test Range type constructor."""
    
    def test_default_range(self):
        """Test Range with default parameters."""
        range_type = Range()
        assert range_type.name == "Range"
        assert len(range_type.params) == 2
        assert range_type.params[0] == Int  # default start
        assert range_type.params[1] == Int  # default end
        assert "description" in range_type.metadata
        
    def test_custom_range(self):
        """Test Range with custom parameters."""
        range_type = Range(Float, Float)
        assert range_type.params[0] == Float
        assert range_type.params[1] == Float
        
    def test_partial_range(self):
        """Test Range with one custom parameter."""
        range_type = Range(start_t=Float)
        assert range_type.params[0] == Float
        assert range_type.params[1] == Int  # default end


class TestContextTypes:
    """Test Context type wrapper."""
    
    def test_context_constructor(self):
        """Test Context type constructor."""
        ctx_int = Context(Int)
        assert ctx_int.name == "Context"
        assert len(ctx_int.params) == 1
        assert ctx_int.params[0] == Int
        
    def test_context_with_metadata(self):
        """Test Context with metadata."""
        ctx_string = Context(String, source="user_input", validated=True)
        assert ctx_string.metadata["source"] == "user_input"
        assert ctx_string.metadata["validated"] is True


class TestEffectTypes:
    """Test effect type constructors."""
    
    def test_base_effect(self):
        """Test base Effect type."""
        assert Effect.name == "Effect"
        assert Effect.params == []
        
    def test_io_effect_default(self):
        """Test IO effect with default parameter."""
        io_eff = IO()
        assert io_eff.name == "IO"
        assert len(io_eff.params) == 1
        assert io_eff.params[0] == Top
        
    def test_io_effect_custom(self):
        """Test IO effect with custom type."""
        io_string = IO(String)
        assert io_string.params[0] == String
        
    def test_network_effect(self):
        """Test Network effect."""
        net_eff = Network(Int)
        assert net_eff.name == "Network"
        assert net_eff.params[0] == Int
        
    def test_ui_effect(self):
        """Test UI effect."""
        ui_eff = UI(Bool)
        assert ui_eff.name == "UI"
        assert ui_eff.params[0] == Bool


class TestPatternTypes:
    """Test pattern/utility type constructors."""
    
    def test_maybe_alias(self):
        """Test Maybe as alias for Option."""
        maybe_int = Maybe(Int)
        option_int = Option(Int)
        assert maybe_int == option_int
        
    def test_either_constructor(self):
        """Test Either type constructor."""
        either_int_string = Either(Int, String)
        assert either_int_string.name == "Either"
        assert len(either_int_string.params) == 2
        assert either_int_string.params[0] == Int
        assert either_int_string.params[1] == String
        
    def test_stream_constructor(self):
        """Test Stream type constructor."""
        stream_int = Stream(Int)
        assert stream_int.name == "Stream"
        assert len(stream_int.params) == 1
        assert stream_int.params[0] == Int
        
    def test_promise_constructor(self):
        """Test Promise type constructor."""
        promise_string = Promise(String)
        assert promise_string.name == "Promise"
        assert len(promise_string.params) == 1
        assert promise_string.params[0] == String


class TestComplexCompositions:
    """Test complex type compositions."""
    
    def test_list_of_functions(self):
        """Test list of functions."""
        func_type = Function(Int, String)
        list_of_funcs = List(func_type)
        assert str(list_of_funcs) == "List[Function[Int, String]]"
        
    def test_function_returning_list(self):
        """Test function returning list."""
        list_type = List(Int)
        func = Function(String, list_type)
        assert str(func) == "Function[String, List[Int]]"
        
    def test_map_of_options(self):
        """Test map with option values."""
        opt_int = Option(Int)
        map_type = Map(String, opt_int)
        assert str(map_type) == "Map[String, Option[Int]]"
        
    def test_either_with_containers(self):
        """Test Either with container types."""
        list_int = List(Int)
        set_string = Set(String)
        either_type = Either(list_int, set_string)
        assert str(either_type) == "Either[List[Int], Set[String]]"
        
    def test_deeply_nested_types(self):
        """Test deeply nested type structures."""
        # Promise[Either[List[Int], Option[String]]]
        list_int = List(Int)
        opt_string = Option(String)
        either_type = Either(list_int, opt_string)
        promise_type = Promise(either_type)
        expected = "Promise[Either[List[Int], Option[String]]]"
        assert str(promise_type) == expected


class TestTypeEquality:
    """Test equality for container types."""
    
    def test_same_container_types_equal(self):
        """Test that same container types are equal."""
        list1 = List(Int)
        list2 = List(Int)
        assert list1 == list2
        
    def test_different_container_types_unequal(self):
        """Test that different container types are unequal."""
        list_int = List(Int)
        set_int = Set(Int)
        assert list_int != set_int
        
    def test_same_function_types_equal(self):
        """Test that same function types are equal."""
        func1 = Function(Int, String)
        func2 = Function(Int, String)
        assert func1 == func2
        
    def test_swapped_function_params_unequal(self):
        """Test that swapped function parameters are unequal."""
        func1 = Function(Int, String)
        func2 = Function(String, Int)
        assert func1 != func2


if __name__ == "__main__":
    pytest.main([__file__])
