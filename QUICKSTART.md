# Simple Computer - Quick Start Guide

## 🔧 Type → UI Pipeline Prototype

This prototype demonstrates a type-driven UI system where types determine available actions and enable safe composition.

## Installation

```bash
# Install dependencies (using uv)
uv sync

# Or with pip
pip install rich
```

## Running the Demo

```bash
# Run the interactive demo
python demo.py

# Or run the original CLI
python app.py sample_with_comments.md --repl
```

## Features Demonstrated

### 1. Type → UI Pipeline
- Load documents and see type-driven actions
- Interactive UI shows only valid operations for each type
- Visual feedback with icons and descriptions

### 2. Composition Flow  
- Chain multiple operations on typed values
- Example: `Doc → List[Comment] → List[Comment] (filtered) → Unit (delete)`
- Type system ensures only compatible operations can chain

### 3. Runtime Orchestration
- Dynamic action registration
- Type registry for creating and validating values
- Discover available actions for any type

### 4. Financial Domain Types
- Currency, Account, Amount, FxQuote types
- Type-safe FX conversion flow
- Constraints prevent invalid operations

### 5. LLM Integration
- Type schemas guide LLM suggestions
- Validate LLM outputs against type constraints  
- Generate type-safe prompts

## Key Concepts

- **Types drive the UI**: The system shows only actions that accept the current type
- **Composition is type-safe**: Can only chain operations where output→input types match
- **LLM outputs are constrained**: Type system validates all LLM suggestions
- **Domain modeling**: Add new types (Currency, Account) with specific constraints

## Architecture

```
core/
  types.py      - Type system with unification
  actions.py    - Action registry and execution
  
ui_system.py    - Interactive type-driven UI
orchestration.py - Runtime type management  
llm_integration.py - Type-safe LLM features
```

## Extending

1. Add new types in `core/types.py`
2. Register actions with `@register_action` 
3. Types automatically appear in UI with valid actions
4. LLM will respect type constraints
