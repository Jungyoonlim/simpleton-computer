from fileio.files import load_doc
from core.plan import plan_and_run
from core.types import List, Comment

doc_t, doc_v = load_doc("examples/sample_comments.txt")
goal_t = List(Comment)

final_t, final_v, trace = plan_and_run(doc_t, doc_v, goal_t)
print("Plan trace:", trace)
for c in final_v:  # pretty because CommentValue.__str__
    print(c)
