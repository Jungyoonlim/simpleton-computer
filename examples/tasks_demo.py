from fileio.files import load_doc
from core.plan import plan_and_run
from core.typesys.types import List, Task

doc_t, doc_v = load_doc("examples/sample_mixed_content.txt")
goal_t = List(Task)

final_t, final_v, trace = plan_and_run(doc_t, doc_v, goal_t)
print("Plan trace:", trace)
print(f"Found {len(final_v)} tasks:")
for t in final_v:  # pretty because TaskValue.__str__
    print(t)
