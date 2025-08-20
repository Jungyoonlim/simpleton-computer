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