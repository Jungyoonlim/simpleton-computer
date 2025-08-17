from typing import Callable, Dict, Tuple
from core.types import Type, unify

_registry: Dict[str, Tuple[Type, Type, Callable]] = {}

def register_action(name: str, input_t: Type, output_t: Type):
    def deco(fn: Callable):
        _registry[name] = (input_t, output_t, fn)
        return fn 
    return deco

def list_actions_for(t: Type):
    return {name: (inp, out) for name, (inp, out, _) in _registry.items() if unify(inp, t)}

def run(name: str, value):
    inp_t, out_t, fn = _registry[name]
    return out_t, fn(value)