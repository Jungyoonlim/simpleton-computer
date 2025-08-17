import sys
from core.types import Doc, List
from core.actions import register_action
from fileio.files import load_doc
from core.engine import suggest_actions, execute

@register_action("summarize", Doc, Doc)
def summarize(doc):
    return type("X", (object,), {"path": doc.path, "text": doc.text[:100] + "..."})

@register_action("extract_titles", Doc, List(Doc))
def extract_titles(doc):
    lines = [l.strip() for l in doc.text.splitlines() if l.strip().startswith("#")]
    return [type("X", (object,), {"path": doc.path, "text": l}) for l in lines]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app.py <file>")
        sys.exit(1)

    t, v = load_doc(sys.argv[1])
    print("Handle:", t.name, "->", v.path)
    actions = suggest_actions(t)
    print("Available Actions:", list(actions.keys()))

    for name in actions.keys():
        out_t, out_v = execute(name, v)
        print(f"\nAction: {name}")
        print("OutputType:", out_t.name)
        if isinstance(out_v, list):
            for item in out_v:
                print("-", item.text)
        else:
            print(out_v.text)