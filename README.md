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
- 