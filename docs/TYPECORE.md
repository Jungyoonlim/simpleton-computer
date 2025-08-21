# Type System Core

## `Type` dataclass

- `name: str` 
- `params: List[Type]`
- `metadata: Dict[str, Any]`
- `carrier` 
- `__str__/__repr__` 
- `__eq__/__hash__` 

## Base Types 

- `Unit`, `Bool`, `Int`, `String`, `Float`, `Bytes`, `Top` 
- `Top` acts as a supertype placeholder that currently "matches anything" in unification. 

## Type constructors (helpers)

- `List`, `Option`, `Tuple`, `Function`, `Map`, `Set`, `Range` build `Type` values with the right `name`/`params`

```python
Open = Function(String, IO(file))

ReadCSV = Function(file, IO(rows))

# Crop: (Image, Range[Int, Int]) -> Image
Crop = Function(Tuple(img, span), img)
```

## Context 

- `Context(T, **metadata)` wraps a type with ambient info
- Effects: `Effect`, `IO`, `Network`, `UI`: tag capabilities and outputs.

## Patterns and Utilities

- Data shapes: `Maybe`, `Either`, `Stream`, `Promise`
- Polymorphism: `TVar(varname)` creates a type variable. (e.g. `TVar('a')` with its logical name in `metadata["tvar"]`)
- Helpers: `is_tvar(t)` checks for `TVar`

```python
# DecodeImage: File -> Either[Error, Image]
DecodeImage = Function(file, Either(Type("Error"), img))

# Async pipeline: String -> Promise(Image)
DownloadImage = Function(String, Promise(img))

# Live data: Sensor -> Stream[Float]
Sensor = Type("Sensor")
ReadSensor = Function(Sensor, Stream(Float))
```

```python
# Polymorphism = reusable building blocks
# `Filter: (List[a], a->Bool) -> List[a]`
a = TVar('a')
Filter = Function(
    Tuple(List(a), Function(a, b)),
    List(b)
)

# Either for fallible ops: LoadSafe: String -> IO(Either[Error, File])
LoadSafe = Function(String, IO(Either(Type("Error"), file)))
```

## Occurs-check

```python
def occurs(var: str, t: Type, subst: dict) -> bool:
    if is_tvar(t):
        v = t.metadata["tvar"]
        if v == var: 
            return True
        return v in subst and occurs(var, subst[v], subst)
    return any(occurs(var, p, subst) for p in t.params)
```

## The unifier

```python
def unify(a: Type, b: Type, subst: Optional[dict]=None) -> Union[bool,dict]:
    subst = {} if subst is None else dict(subst)
```

### 1. Top matches anything 

```python 
if a.name == "Top" or b.name == "Top":
    return subst 
```

### 2. Peel `Context`

```python
if a.name == "Context" and a.params: 
    return unify(a.params[0], b, subst)
if b.name == "Context" and b.params: 
    return unify(a, b.params[0], subst)
```

### 3. Variable on the left 

```python
if is_tvar(a):
    key = a.metadata["tvar"]
    if key in subst: 
        return unify(subst[key], b, subst)
    if occurs(key, b, subst):
        return False 
    subst[key] = b
    return subst
```

### 4. Variable on the right 

```python 
if is_tvar(b):
    key = b.metadata["tvar"]
    if key in subst: 
        return unify(subst[key], a, subst)
    if occurs(key, a, subst):
        return False 
    subst[key] = a 
    return subst 
```

### 5. Rigid constructors must match 

```python 
if a.name != b.name or len(a.params) != len(b.params):
    return False
```

### 6. Recurse into parameters

```python 
for ap, bp in zip(a.params, b.params):
    subst = unify(ap, bp, subst)
    if subst is False:
        return False
return subst
```

