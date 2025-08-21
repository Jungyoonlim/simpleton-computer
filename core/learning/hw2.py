from core.typesys.types import TVar, List, Function, Int, Bool, unify

A = TVar("A")

print("Unify List(A) with List(Int):")
result1 = unify(List(A), List(Int))
print(result1)

print("Unify Function(A, A) with Function(Int, Bool):")
result2 = unify(Function(A, A), Function(Int, Bool))
print(result2)

