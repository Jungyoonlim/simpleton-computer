# app.py
import sys
import argparse
from typing import Any, Iterable

from core.types import Type, Doc, List  # keep using your simple Type + List
from core.engine import suggest_actions, execute
from core.actions import register_action  # for builtin demo actions
from fileio.files import load_doc

# -----------------------
# Built-in demo actions
# -----------------------
@register_action("summarize", Doc, Doc)
def summarize(doc):
    return type("X", (object,), {"path": doc.path, "text": doc.text[:100] + "..."})

@register_action("extract_titles", Doc, List(Doc))
def extract_titles(doc):
    lines = [l.strip() for l in doc.text.splitlines() if l.strip().startswith("#")]
    return [type("X", (object,), {"path": doc.path, "text": l}) for l in lines]

# -----------------------
# Helpers
# -----------------------
def type_name(t: Type) -> str:
    if t.param:
        return f"{t.name}[{type_name(t.param)}]"
    return t.name

def print_handle(t: Type, v: Any):
    if t.name == "Doc" and hasattr(v, "text"):
        snippet = (v.text[:120] + "...") if len(v.text) > 120 else v.text
        print(f"→ Handle: {type_name(t)}  ({len(snippet)} chars)  from: {getattr(v, 'path', '—')}")
    elif t.name == "List":
        n = len(v) if isinstance(v, Iterable) else "?"
        print(f"→ Handle: {type_name(t)}  ({n} items)")
    else:
        print(f"→ Handle: {type_name(t)}")

def pretty_print(t: Type, v: Any):
    if t.name == "Doc" and hasattr(v, "text"):
        print(v.text)
    elif t.name == "List":
        # Try to show 'text' for each element, otherwise str(...)
        for i, item in enumerate(v):
            display = getattr(item, "text", str(item))
            print(f"- {display}")
    else:
        print(v)

def available_action_names(t: Type):
    acts = suggest_actions(t)
    return list(acts.keys())

def run_action_or_error(name: str, t: Type, v: Any):
    acts = suggest_actions(t)
    if name not in acts:
        valid = ", ".join(sorted(acts.keys())) or "(none)"
        raise TypeError(f"Action '{name}' not valid for handle {type_name(t)}. Valid: {valid}")
    out_t, out_v = execute(name, v)
    return out_t, out_v

def run_pipeline(pipe: str, t: Type, v: Any):
    """
    pipe string like: "summarize"  or  "extract_titles"
    (You can chain later once you add actions that match types across steps.)
    """
    steps = [p.strip() for p in pipe.split("|>") if p.strip()]
    curr_t, curr_v = t, v
    for step in steps:
        print(f"\n▶ {step} : {type_name(curr_t)} -> ?")
        curr_t, curr_v = run_action_or_error(step, curr_t, curr_v)
        print(f"   ✓ OutputType: {type_name(curr_t)}")
    return curr_t, curr_v

def repl(t: Type, v: Any):
    print("\nEntering REPL. Type an action name to run it.")
    print("Commands: ':q' to quit, ':ls' to list actions, ':type' to show current type.")
    curr_t, curr_v = t, v
    while True:
        try:
            cmd = input("sc> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if cmd in ("", None):
            continue
        if cmd == ":q":
            break
        if cmd == ":type":
            print_handle(curr_t, curr_v)
            continue
        if cmd == ":ls":
            print("Available:", ", ".join(sorted(available_action_names(curr_t))) or "(none)")
            continue
        # treat input as a pipeline "a |> b |> c"
        try:
            curr_t, curr_v = run_pipeline(cmd, curr_t, curr_v)
            print("\n--- Output ---")
            pretty_print(curr_t, curr_v)
            print("--------------")
        except Exception as e:
            print(f"Error: {e}")

# -----------------------
# Main
# -----------------------
def main():
    ap = argparse.ArgumentParser(description="Simpleton Computer – type-directed actions")
    ap.add_argument("file", help="Path to input file (e.g., sample.md)")
    ap.add_argument("--pipe", help="Pipeline like 'summarize' or 'extract_titles'", default=None)
    ap.add_argument("--repl", action="store_true", help="Run interactive REPL after initial load")
    args = ap.parse_args()

    t, v = load_doc(args.file)
    print_handle(t, v)

    acts = available_action_names(t)
    print("Available Actions:", acts or "(none)")

    if args.pipe:
        try:
            out_t, out_v = run_pipeline(args.pipe, t, v)
            print("\n=== Pipeline Output ===")
            pretty_print(out_t, out_v)
        except Exception as e:
            print(f"Pipeline error: {e}")

    if args.repl:
        repl(t, v)
    elif not args.pipe:
        # Default behavior: run each available action once (like your original demo)
        for name in acts:
            print(f"\n▶ {name}")
            out_t, out_v = run_action_or_error(name, t, v)
            print(f"OutputType: {type_name(out_t)}")
            pretty_print(out_t, out_v)

if __name__ == "__main__":
    main()
