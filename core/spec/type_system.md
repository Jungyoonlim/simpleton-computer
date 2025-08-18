# Simple Computer Type System Specification

## 1. Core Type Language

### 1.1 Base Types
```
τ ::= Unit                    -- No meaningful value
    | Bool                    -- Boolean values
    | Int                     -- Integer values
    | String                  -- Text values
    | τ₁ → τ₂                -- Function type
    | τ₁ × τ₂                -- Product type (tuples)
    | τ₁ + τ₂                -- Sum type (variants)
    | List[τ]                 -- Homogeneous lists
    | Stream[τ]               -- Infinite sequences
    | Ref[τ]                  -- Mutable references
    | IO[τ]                   -- I/O computations
```

### 1.2 Domain Types
```
Document      ::= { path: String, content: String, metadata: Meta }
Image         ::= { path: String, pixels: Array[Pixel], format: Format }
Audio         ::= { samples: Stream[Float], rate: Int }
Event         ::= { time: Timestamp, data: τ }
Task          ::= { description: String, status: Status, deadline: Time? }
```

### 1.3 Context Types
```
Context[τ] ::= { value: τ, 
                 confidence: Float,        -- AI confidence level
                 permissions: Set[Perm],   -- Required permissions
                 cost: Cost,              -- Computational cost
                 provenance: Source }     -- Data origin
```



## 2. Type Classes (Capabilities)

### 2.1 Basic Type Classes
```
class Showable[τ] where
  show :: τ → String

class Parseable[τ] where
  parse :: String → Maybe[τ]

class Serializable[τ] where
  serialize :: τ → Bytes
  deserialize :: Bytes → Maybe[τ]
```

### 2.2 Compositional Type Classes
```
class Transformable[α, β] where
  transform :: α → β

class Filterable[τ] where
  filter :: (τ → Bool) → List[τ] → List[τ]

class Aggregatable[τ, ρ] where
  aggregate :: List[τ] → ρ
```

### 2.3 Effect Type Classes
```
class Executable[τ] where
  execute :: τ → IO[Unit]

class Undoable[τ] where
  undo :: τ → Maybe[τ]
  redo :: τ → Maybe[τ]
```

## 3. Composition Rules

### 3.1 Sequential Composition
```
If  f :: α → β  and  g :: β → γ
Then  g ∘ f :: α → γ
```

### 3.2 Parallel Composition
```
If  f :: α → β  and  g :: γ → δ
Then  f ⊗ g :: (α × γ) → (β × δ)
```

### 3.3 Conditional Composition
```
If  p :: α → Bool,  f :: α → β,  g :: α → β
Then  if p then f else g :: α → β
```

## 4. Type Inference Rules

### 4.1 Function Application
```
Γ ⊢ f : τ₁ → τ₂    Γ ⊢ x : τ₁
─────────────────────────────
      Γ ⊢ f(x) : τ₂
```

### 4.2 Let Binding
```
Γ ⊢ e₁ : τ₁    Γ, x : τ₁ ⊢ e₂ : τ₂
──────────────────────────────────
    Γ ⊢ let x = e₁ in e₂ : τ₂
```

### 4.3 Pipeline Composition
```
Γ ⊢ e : τ₁    Γ ⊢ f : τ₁ → τ₂
──────────────────────────────
    Γ ⊢ e |> f : τ₂
```

## 5. Subtyping and Variance

### 5.1 Subtyping Rules
```
τ <: τ                          (Reflexivity)

τ₁ <: τ₂    τ₂ <: τ₃
─────────────────────           (Transitivity)
     τ₁ <: τ₃

Context[τ] <: τ                 (Context stripping)
```

### 5.2 Variance Annotations
```
List[+τ]     -- Covariant
Ref[-τ]      -- Contravariant
Function[-τ₁, +τ₂]  -- Contravariant in input, covariant in output
```

## 6. Effect System

### 6.1 Effect Types
```
ε ::= Pure                   -- No effects
    | Read[Resource]         -- Read from resource
    | Write[Resource]        -- Write to resource
    | Network               -- Network access
    | UI                    -- User interface
    | ε₁ ∪ ε₂              -- Effect union
```

### 6.2 Effect Inference
```
Γ ⊢ e : τ ! ε
```
Means: Expression `e` has type `τ` with effects `ε`

## 7. Examples

### 7.1 Simple Pipeline
```
load_doc    :: String → IO[Document]
summarize   :: Document → Document
send_email  :: Document → IO[Unit]

pipeline = load_doc |> summarize |> send_email
         :: String → IO[Unit]
```

### 7.2 Conditional Pipeline
```
analyze     :: Document → Analysis
is_urgent   :: Analysis → Bool
notify_now  :: Document → IO[Unit]
queue_later :: Document → IO[Unit]

pipeline = load_doc 
        |> (doc => let analysis = analyze(doc) in
                   if is_urgent(analysis) 
                   then notify_now(doc)
                   else queue_later(doc))
```

## 8. Safety Guarantees

1. **Type Safety**: Well-typed programs don't go wrong
2. **Effect Safety**: Effects are tracked in types
3. **Permission Safety**: Capabilities require explicit permissions
4. **Composition Safety**: Only type-compatible capabilities compose

## 9. Future Extensions

- Dependent types for finer-grained specifications
- Linear types for resource management
- Session types for protocol specifications
- Gradual typing for dynamic capabilities
