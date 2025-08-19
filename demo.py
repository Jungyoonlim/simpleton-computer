#!/usr/bin/env python3
"""
Simple Computer Demo - Type → UI Pipeline Prototype
Demonstrates all features of the type-driven system
"""
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich import print as rprint

# Import our modules
from core.types import *
from core.actions import register_action
from fileio.files import load_doc, CommentValue
from ui_system import start_ui, TypedUI
from orchestration import (
    type_registry, CompositionEngine, 
    CurrencyValue, AmountValue, AccountValue
)
from llm_integration import (
    LLMSuggestionEngine, LLMTypeAdapter, 
    TypeConstrainedPrompt, suggest_comment_filters
)

console = Console()

def demo_1_basic_ui_pipeline():
    """Demo 1: Type → UI pipeline with Doc and Comment types"""
    console.print("\n[bold cyan]Demo 1: Basic Type → UI Pipeline[/bold cyan]")
    console.print("Loading document and showing type-driven UI...\n")
    
    # Load a document
    doc_type, doc_value = load_doc("sample_with_comments.md")
    
    # Start interactive UI
    console.print("Starting interactive UI. You can:")
    console.print("- Choose 'extract_comments' to get comments")
    console.print("- Chain filters on the comments")
    console.print("- Type ':quit' to exit this demo\n")
    
    ui = TypedUI()
    context = ui.run_interactive(doc_type, doc_value)
    
    return context

def demo_2_composition_flow():
    """Demo 2: Composition flow - chaining operations"""
    console.print("\n[bold cyan]Demo 2: Composition Flow[/bold cyan]")
    console.print("Demonstrating automatic action chaining...\n")
    
    # Create some test comments
    comments = [
        CommentValue("Alice", "2025-01-10", "TODO: Fix login bug", "test.md"),
        CommentValue("Bob", "2025-01-12", "DONE: Updated API docs", "test.md"),
        CommentValue("Alice", "2025-01-14", "TODO: Add unit tests", "test.md"),
        CommentValue("Charlie", "2025-01-13", "Review required here", "test.md"),
    ]
    
    # Register a custom filter
    @register_action("filter_todos", List(Comment), List(Comment))
    def filter_todos(comments_list):
        """Filter only TODO comments"""
        return [c for c in comments_list if "TODO" in c.text]
    
    # Show composition possibilities
    console.print("[yellow]Starting with List[Comment][/yellow]")
    console.print(f"Comments: {len(comments)} items\n")
    
    # Suggest chains
    chains = CompositionEngine.suggest_chains(List(Comment), max_depth=3)
    console.print("[green]Possible composition chains:[/green]")
    for i, chain in enumerate(chains[:5]):  # Show first 5
        console.print(f"  {i+1}. {' → '.join(chain)}")
    
    # Execute a chain
    console.print("\n[yellow]Executing chain: filter_todos → filter_author_me[/yellow]")
    
    # First register Alice as "me" for the demo
    @register_action("filter_alice", List(Comment), List(Comment)) 
    def filter_alice(comments_list):
        """Filter only Alice's comments"""
        return [c for c in comments_list if c.author == "Alice"]
    
    result_type, result_value = CompositionEngine.execute_chain(
        ["filter_todos", "filter_alice"], 
        comments
    )
    
    console.print(f"Result: {len(result_value)} comments")
    for comment in result_value:
        console.print(f"  - [{comment.author}] {comment.text}")

def demo_3_runtime_orchestration():
    """Demo 3: Runtime orchestration with type registry"""
    console.print("\n[bold cyan]Demo 3: Runtime Orchestration[/bold cyan]")
    console.print("Dynamic type registration and discovery...\n")
    
    # Register a new action at runtime
    @register_action("comment_to_task", Comment, Task)
    def comment_to_task(comment: CommentValue):
        """Convert a TODO comment to a Task"""
        return {
            "title": comment.text.replace("TODO:", "").strip(),
            "author": comment.author,
            "created": comment.date,
            "status": "pending"
        }
    
    console.print("[green]Registered new action: comment_to_task[/green]")
    
    # Show type registry capabilities
    console.print("\n[yellow]Type Registry Demo:[/yellow]")
    
    # Create values using type registry
    usd = type_registry.construct(Currency, code="USD")
    eur = type_registry.construct(Currency, code="EUR")
    
    console.print(f"Created currencies: {usd.code}, {eur.code}")
    
    # Show available actions for different types
    from core.actions import list_actions_for
    
    types_to_check = [Comment, List(Comment), Currency, Amount]
    for t in types_to_check:
        actions = list_actions_for(t)
        console.print(f"\n{t} → {list(actions.keys())}")

def demo_4_financial_domain():
    """Demo 4: Financial domain with type constraints"""
    console.print("\n[bold cyan]Demo 4: Financial Domain Types[/bold cyan]")
    console.print("FX quote flow with type-safe operations...\n")
    
    # Create accounts
    usd_account = AccountValue(
        id="ACC001",
        name="USD Account", 
        currency=CurrencyValue("USD"),
        balance=10000.0
    )
    
    eur_account = AccountValue(
        id="ACC002",
        name="EUR Account",
        currency=CurrencyValue("EUR"), 
        balance=5000.0
    )
    
    console.print(f"[green]Accounts created:[/green]")
    console.print(f"  - {usd_account.name}: {usd_account.balance} {usd_account.currency.code}")
    console.print(f"  - {eur_account.name}: {eur_account.balance} {eur_account.currency.code}")
    
    # Create amount to convert
    amount = AmountValue(value=1000.0, currency=CurrencyValue("USD"))
    console.print(f"\n[yellow]Converting: {amount.value} {amount.currency.code}[/yellow]")
    
    # Get FX quote
    from orchestration import create_fx_quote, convert_amount
    
    currencies_tuple = (amount.currency, CurrencyValue("EUR"))
    quote = create_fx_quote(currencies_tuple)
    console.print(f"FX Quote: 1 {quote.from_currency.code} = {quote.rate} {quote.to_currency.code}")
    
    # Convert amount
    converted = convert_amount((amount, quote))
    console.print(f"Converted: {converted.value:.2f} {converted.currency.code}")
    
    # Show type constraints in action
    console.print("\n[red]Type constraints demo:[/red]")
    try:
        # This should fail - wrong currency
        wrong_quote = create_fx_quote((CurrencyValue("GBP"), CurrencyValue("EUR")))
        convert_amount((amount, wrong_quote))  # USD amount with GBP->EUR quote
    except ValueError as e:
        console.print(f"✓ Type system caught error: {e}")

def demo_5_llm_integration():
    """Demo 5: LLM integration for type-safe suggestions"""
    console.print("\n[bold cyan]Demo 5: LLM Integration[/bold cyan]")
    console.print("Type-constrained suggestions and completions...\n")
    
    # Initialize suggestion engine
    llm_engine = LLMSuggestionEngine()
    
    # Demo 1: Suggest refinements for comments
    comments = [
        CommentValue("Dev1", "2025-01-10", "TODO: Fix authentication", "auth.py"),
        CommentValue("Dev2", "2025-01-12", "BUG: Memory leak in parser", "parser.py"),
        CommentValue("Dev1", "2025-01-14", "TODO: Add rate limiting", "api.py"),
    ]
    
    console.print("[yellow]Comment refinement suggestions:[/yellow]")
    suggestions = llm_engine.suggest_refinements(
        comments, 
        List(Comment),
        List(Comment),
        "3 comments from codebase"
    )
    
    for i, suggestion in enumerate(suggestions):
        console.print(f"{i+1}. {suggestion['description']}")
        console.print(f"   Preview: {suggestion['preview']}")
    
    # Demo 2: Type-safe completion
    console.print("\n[yellow]Type-safe value completion:[/yellow]")
    
    partial_comment = {
        "author": "System",
        "text": "Automated code review finding"
        # Missing: date, source_path
    }
    
    console.print("Partial comment:", partial_comment)
    
    completions = llm_engine.complete_partial_value(partial_comment, Comment)
    console.print("\nCompleted version:")
    for field, value in completions[0].items():
        console.print(f"  {field}: {value}")
    
    # Demo 3: Validate against type
    console.print("\n[yellow]Type validation:[/yellow]")
    
    test_values = [
        {"author": "Test", "date": "2025-01-14", "text": "Valid comment"},
        {"author": "Test", "date": "invalid-date", "text": "Bad date"},
        {"author": "Test"},  # Missing fields
    ]
    
    for value in test_values:
        valid, error = LLMTypeAdapter.validate_against_type(value, Comment)
        status = "[green]✓ Valid[/green]" if valid else f"[red]✗ Invalid: {error}[/red]"
        console.print(f"  {value} → {status}")
    
    # Demo 4: Type-constrained prompt
    console.print("\n[yellow]Type-constrained prompt example:[/yellow]")
    
    prompt = TypeConstrainedPrompt.build_prompt(
        "Extract key information from comments and create a summary comment",
        List(Comment),
        Comment,
        examples=[
            ([{"author": "Dev", "text": "Fix bug #123"}], 
             {"author": "Summary Bot", "date": "2025-01-14", 
              "text": "1 bug fix mentioned", "source_path": "generated"})
        ]
    )
    
    console.print(Panel(prompt[:500] + "...", title="Generated Prompt"))

def main():
    """Main demo runner"""
    console.print(Panel.fit(
        "[bold yellow]🔧 Simple Computer - Type → UI Pipeline Demo[/bold yellow]\n\n"
        "This demo showcases:\n"
        "1. Type-driven UI pipeline\n"
        "2. Composition flow for chaining operations\n" 
        "3. Runtime orchestration and type registry\n"
        "4. Financial domain types with constraints\n"
        "5. LLM integration for type-safe suggestions",
        border_style="cyan"
    ))
    
    demos = [
        ("Basic Type → UI Pipeline", demo_1_basic_ui_pipeline),
        ("Composition Flow", demo_2_composition_flow),
        ("Runtime Orchestration", demo_3_runtime_orchestration),
        ("Financial Domain Types", demo_4_financial_domain),
        ("LLM Integration", demo_5_llm_integration),
    ]
    
    while True:
        console.print("\n[bold]Available Demos:[/bold]")
        for i, (name, _) in enumerate(demos):
            console.print(f"  {i+1}. {name}")
        console.print("  0. Exit")
        
        choice = Prompt.ask("\nSelect demo", choices=[str(i) for i in range(len(demos)+1)])
        
        if choice == "0":
            break
        
        demo_idx = int(choice) - 1
        if 0 <= demo_idx < len(demos):
            try:
                demos[demo_idx][1]()
            except KeyboardInterrupt:
                console.print("\n[yellow]Demo interrupted[/yellow]")
            except Exception as e:
                console.print(f"\n[red]Demo error: {e}[/red]")
                import traceback
                traceback.print_exc()
        
        console.print("\n" + "="*60)
    
    console.print("\n[bold green]Thanks for exploring Simple Computer![/bold green]")

if __name__ == "__main__":
    main()

