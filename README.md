# Simpleton Computer 

A prototype of type-directed computing 

## Aug 17 
Takes a piece of data, checks its type, shows only the actions that make sense for that type. 

### Steps
1. Load a file 
2. Suggest actions
- Because the handle is a Doc, the system looks up the registry and lists only the actions that unify w/ Doc. 
3. Run the action 
4. Output is typed 
- The system can now decide what to do next based on the type 

### Type-theoretic machine in embryo
- Objects = types (Doc, List[Doc], Event)
- Morphisms = actions (Summarize, Extract_titles, Schedule)
- Composition = pipelines
- Pullbacks = reindexing context 
- Σ = exposing all contextualized variants (browse the whole menu of (context, action))
- Π = design guarantees (system ensures universal consistency: every type has at least one valid action, every doc can be summarized, etc.)

So Σ view: explore all possible actions or data-context pairs at once. 
Π-panel: see which global constraints are being enforced.
A pullback lens: shift perspective. Reindex the same data by a different context. 

## Why Type Theory?
- Can enforce a type discipline on every action, every resource, and every effect.
- Lets you: 
    - Filter out nonsense plans before they even run.
    - Offer provable guarantees 
    - Interop multiple LLMs 
- Adaptive UI as a first-class effect
    - Instead of AI bolted on top of an OS, the system is the compositor 

- Resource + Capability security model 
    - Most AI agents are unsafe. 
    - Baking in a linear/affine resource discipline and explicit permit tokens. 
- Planner + Heuristics tuned for human-scaled OS
    - Move towards A with type distance heuristics + caching + learned preferences (from brute force BFS or ReAct)
    - Cheap enough to run on device 