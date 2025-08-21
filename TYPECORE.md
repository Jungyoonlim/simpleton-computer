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


```