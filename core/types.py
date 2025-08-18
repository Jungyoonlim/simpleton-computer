from __future__ import annotations

from dataclasses import dataclass, field
import typing as t   # <-- avoid shadowing; use t.Any, t.Dict, etc.

@dataclass(frozen=True)
class Type:
    name: str
    params: t.List['Type'] = field(default_factory=list)     # <-- 'Type' as string
    metadata: t.Dict[str, t.Any] = field(default_factory=dict)  # <-- t.Any

    def __str__(self):
        if not self.params:
            return self.name
        param_str = ", ".join(str(p) for p in self.params)
        return f"{self.name}[{param_str}]"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if not isinstance(other, Type):
            return False
        return (self.name == other.name and
                self.params == other.params)

    def __hash__(self):
        return hash((self.name, tuple(self.params)))

# Base Types
Unit = Type("Unit")
Bool = Type("Bool")
Int = Type("Int")
String = Type("String")
Float = Type("Float")
Bytes = Type("Bytes")
Top = Type("Top")   # <-- rename from Any to avoid collision

# Container Types
def List(t_: Type) -> Type:
    return Type("List", [t_])

def Option(t_: Type) -> Type:
    return Type("Option", [t_])

def Tuple(*types: Type) -> Type:
    return Type("Tuple", list(types))

def Function(input_t: Type, output_t: Type) -> Type:
    return Type("Function", [input_t, output_t])

def Map(key_t: Type, value_t: Type) -> Type:   # <-- rename from Dict to avoid shadowing typing.Dict
    return Type("Map", [key_t, value_t])

def Set(t_: Type) -> Type:
    return Type("Set", [t_])

# Domain Types
Doc = Type("Doc", metadata={"icon": "📄", "description": "A text document"})
Comment = Type("Comment", metadata={"icon": "💬", "description": "A comment or annotation"})
Image = Type("Image", metadata={"icon": "🖼️", "description": "An image file"})
Audio = Type("Audio", metadata={"icon": "🎵", "description": "Audio content"})
Video = Type("Video", metadata={"icon": "🎬", "description": "Video content"})
Table = Type("Table", metadata={"icon": "📊", "description": "Tabular data"})
Code = Type("Code", metadata={"icon": "💻", "description": "Source code"})
Email = Type("Email", metadata={"icon": "📧", "description": "Email message"})
Event = Type("Event", metadata={"icon": "📅", "description": "Calendar event"})
Task = Type("Task", metadata={"icon": "✅", "description": "A task or todo item"})
Note = Type("Note", metadata={"icon": "📝", "description": "A note or memo"})

# UI/Interaction Types
Selection = Type("Selection", metadata={"ui_hint": "user_selection", "icon": "👆"})
Cursor = Type("Cursor", metadata={"ui_hint": "cursor_position", "icon": "➤"})

def Range(start_t: Type | None = None, end_t: Type | None = None) -> Type:
    start_t = start_t or Int
    end_t = end_t or Int
    return Type("Range", [start_t, end_t], metadata={"description": "A range of positions"})

# Context wrapper
def Context(t_: Type, **metadata) -> Type:
    return Type("Context", [t_], metadata)

# Effect types
Effect = Type("Effect")

def IO(t_: Type | None = None) -> Type:
    return Type("IO", [t_ or Top])

def Network(t_: Type | None = None) -> Type:
    return Type("Network", [t_ or Top])

def UI(t_: Type | None = None) -> Type:
    return Type("UI", [t_ or Top])

# Patterns
def Maybe(t_: Type) -> Type:
    return Option(t_)

def Either(left_t: Type, right_t: Type) -> Type:
    return Type("Either", [left_t, right_t])

def Stream(t_: Type) -> Type:
    return Type("Stream", [t_])

def Promise(t_: Type) -> Type:
    return Type("Promise", [t_])

# Unification
def unify(a: Type, b: Type) -> bool:
    """Check if type 'a' can unify with type 'b'"""
    # Handle Top type
    if a.name == "Top" or b.name == "Top":
        return True
    
    # Handle Context unwrapping
    if a.name == "Context" and a.params:
        return unify(a.params[0], b)
    if b.name == "Context" and b.params:
        return unify(a, b.params[0])
    
    # Basic name check
    if a.name != b.name:
        return False
    
    # Check parameters
    if len(a.params) != len(b.params):
        return False
    
    # Recursively unify parameters
    return all(unify(ap, bp) for ap, bp in zip(a.params, b.params))

# Helper functions
def is_container_type(t_: Type) -> bool:
    """Check if a type is a container type"""
    return t_.name in {"List", "Set", "Map", "Option", "Tuple", "Stream"}

def get_element_type(t_: Type) -> t.Optional[Type]:
    """Get the element type of a container"""
    if t_.name in {"List", "Set", "Option", "Stream"} and t_.params:
        return t_.params[0]
    return None

def is_function_type(t_: Type) -> bool:
    """Check if a type is a function type"""
    return t_.name == "Function" and len(t_.params) == 2

def get_function_signature(t_: Type) -> t.Optional[t.Tuple[Type, Type]]:
    """Get input and output types of a function"""
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