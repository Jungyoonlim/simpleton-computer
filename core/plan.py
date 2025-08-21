from __future__ import annotations
import heapq
import typing as t 

from core.typesys.types import Type, unify 
from core.actions import list_actions_for

# A* walks the type graph to get from a start type to a goal type using your unify 
def type_distance(a: Type, b: Type) -> float: 
    """
    Cheap structural distance: 0 means identical 
    """
    d = 0.0
    if a.name != b.name: 
        d += 1.0
    d += abs(len(a.params) - len(b.params)) * 0.25
    for ap, bp in zip(a.params, b.params):
        d += 0.5 * type_distance(ap, bp)
    return d 


def find_chain(from_t: Type, to_t: Type, toolspace: t.Callable[[Type], dict], max_depth: int=5):
    """
    A* on types. `toolspace(t)` should return actions applicable to t. (name -> Action)
    Returns: list[Action] or None
    """
    start = from_t 
    pq = [(type_distance(start, to_t), 0.0, start, [])]
    seen: dict[str, float] = {repr(start): 0.0}

    while pq: 
        f, g, cur_t, path = heapq.heappop(pq)

        if type_distance(cur_t, to_t) == 0.0:
            return path if path else []
    
        if len(path) >= max_depth: 
            continue 

        for name, act in toolspace(cur_t).items():
            out_t = act.output_t 
            g2 = g + float(getattr(act, "cost", 1.0))
            key = repr(out_t)
            if seen.get(key, 1e9) <= g2: 
                continue 
            seen[key] = g2 
            h = type_distance(out_t, to_t)
            heapq.heappush(pq, (g2 + h, g2, out_t, path + [act]))
    return None 

def plan_and_run(start_t: Type, start_v: t.Any, goal_t: Type, *, max_depth=5):
    """
    Compute a chain of actions from start_t to goal_t then execute it. 
    Returns (final_type, final_value, trace_of_action_names)
    """
    actions = find_chain(start_t, goal_t, list_actions_for, max_depth=max_depth)
    if actions is None:
        raise RuntimeError(f"No plan found from {repr(start_t)} to {repr(goal_t)} (depth ≤ {max_depth})")

    from core.engine import execute
    curr_t, curr_v = start_t, start_v
    trace: list[str] = []

    for act in actions: 
        curr_t, curr_v = execute(act.name, curr_v)
        trace.append(act.name)
    
    return curr_t, curr_v, trace 