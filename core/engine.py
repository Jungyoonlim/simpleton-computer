from __future__ import annotations


from core.actions import list_actions_for, run 


def suggest_actions(handle_type):
    return list_actions_for(handle_type)

def execute(action_name, handle):
    return run(action_name, handle)