from core.typesys.types import List, Task
from fileio.files import load_doc, load_mixed, print_list
from core.engine import execute
from core.plan import plan_and_run

# Load document
doc_t, doc_v = load_doc("examples/sample_mixed_content.txt")

# 1. Direct single action for comments (will find only comment lines)
out_t, out_v = execute("extract_comments", doc_v)
print("Extracted comments:", out_v)

# 2. Direct single action for tasks (will find only task lines)
task_t, task_v = execute("extract_tasks", doc_v)
print("\nExtracted tasks:", task_v)

# 3. Use mixed loader to get all content
print("\nAll mixed content:")
vals = load_mixed(doc_v.path)
print_list(vals)

# 4. Planned chain: Doc -> List(Task)
goal_t = List(Task)
final_t, final_v, trace = plan_and_run(doc_t, doc_v, goal_t)
print("\nPlan trace for tasks:", trace)
print("Final value:", final_v)