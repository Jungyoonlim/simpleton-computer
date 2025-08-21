from core.types import Doc, List, Comment, Unit, Option
from fileio.files import load_doc
from core.engine import execute
from core.plan import plan_and_run

# Load document
doc_t, doc_v = load_doc("examples/sample.txt")

# 1. Direct single action
out_t, out_v = execute("extract_comments", doc_v)
print("Extracted comments:", out_v)

# 2. Planned chain: Doc -> List(Comment)
goal_t = List(Comment)  # get filtered comments
final_t, final_v, trace = plan_and_run(doc_t, doc_v, goal_t)
print("Plan trace:", trace)
print("Final value:", final_v)

# 3. Three approaches for deletion/single comment access:

# Option 1: Keep List[Comment] and explicitly call delete_all
print("\nOption 1: Explicit delete_all")
execute("delete_all", final_v)

# Option 2: Plan directly to Unit (if you add a direct Doc->Unit action)
# Currently not possible without adding new actions

# Option 3: Get single comment using head_comment
print("\nOption 3: Get single comment")
single_t, single_v = execute("head_comment", final_v)
print(f"First comment (Option[Comment]): {single_v}")