"""
Defines the kinds of types our system recognizes. 

Kinds are meta-classifications of types:
- K_TYPE: ordinary types (int, functions, records)
- K_ROW: row types (open and closed collections of labeled fields) 
- K_EFFROW: Effect Rows
- K_INDEX: index terms (used for dependent typing, e.g. Vec[n])

To prevent mixing up incompatible structures
"""

K_TYPE = "Type"
K_ROW = "Row"
K_EFFROW = "EffRow"
K_INDEX = "Index"