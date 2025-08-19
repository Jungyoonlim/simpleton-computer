import typing as t 

from .types import Type, List

def is_container_type(t_: Type) -> bool:
    """Check if a type is a container type"""
    return t_.name in {"List", "Set", "Map", "Option", "Tuple", "Stream"}

def get_element_type(t_: Type) -> bool:
    """Check if a type is a function type"""
    if t_.name in {"List", "Set", "Option", "Stream"} and t_.params:
        return t_.params[0]
    return None 

def is_function_type(t_: Type) -> bool: 
    """Check if a type is a function type"""    
    return t_.name == "Function" and len(t_.params) == 2 

def get_function_signature(t_: Type) -> t.Optional[t.Tuple[Type, Type]]:
    if is_function_type(t_):
        return (t_.params[0], t_.params[1])
    return None

def lift_to_list(t_: Type) -> Type:
    """Lift a type to a list type if not already"""
    if t_.name == "List":
        return t_
    return List(t_)

def type_complexity(t_: Type) -> int:
    """Calculate the complexity/depth of a type"""
    if not t_.params:
        return 1
    return 1 + max(type_complexity(p) for p in t_.params)