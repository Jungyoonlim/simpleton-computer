"""
Runtime Orchestration System
Dynamic registry and type-based action discovery
"""
import typing as t
from dataclasses import dataclass
from core.types import (
    Type, List, Currency, Account, Amount, FxQuote, Fee, 
    Transaction, Tuple, Function, String, Float
)
from core.actions import register_action

# Value classes for financial domain
@dataclass
class CurrencyValue:
    code: str  # USD, EUR, etc.

@dataclass  
class AmountValue:
    value: float
    currency: CurrencyValue

@dataclass
class AccountValue:
    id: str
    name: str
    currency: CurrencyValue
    balance: float

@dataclass
class FxQuoteValue:
    from_currency: CurrencyValue
    to_currency: CurrencyValue
    rate: float
    timestamp: str

@dataclass
class FeeValue:
    amount: AmountValue
    description: str

@dataclass
class TransactionValue:
    from_account: AccountValue
    to_account: AccountValue
    amount: AmountValue
    fee: t.Optional[FeeValue]
    timestamp: str

class TypeRegistry:
    """Enhanced registry with runtime type discovery"""
    def __init__(self):
        self._type_constructors: t.Dict[str, t.Callable] = {}
        self._type_validators: t.Dict[str, t.Callable] = {}
    
    def register_type_constructor(self, type_name: str, constructor: t.Callable):
        """Register a constructor for creating values of a type"""
        self._type_constructors[type_name] = constructor
    
    def register_type_validator(self, type_name: str, validator: t.Callable):
        """Register a validator for checking values of a type"""
        self._type_validators[type_name] = validator
    
    def construct(self, type_: Type, **kwargs) -> t.Any:
        """Construct a value of the given type"""
        constructor = self._type_constructors.get(type_.name)
        if constructor:
            return constructor(**kwargs)
        raise ValueError(f"No constructor for type {type_.name}")
    
    def validate(self, type_: Type, value: t.Any) -> bool:
        """Validate that a value matches the type"""
        validator = self._type_validators.get(type_.name)
        if validator:
            return validator(value)
        return True  # Default to accepting if no validator

# Global registry
type_registry = TypeRegistry()

# Register financial type constructors
type_registry.register_type_constructor("Currency", 
    lambda code: CurrencyValue(code=code))

type_registry.register_type_constructor("Amount",
    lambda value, currency: AmountValue(value=value, currency=currency))

type_registry.register_type_constructor("Account",
    lambda id, name, currency, balance: AccountValue(
        id=id, name=name, currency=currency, balance=balance))

# Financial domain actions
@register_action("create_fx_quote", Tuple(Currency, Currency), FxQuote)
def create_fx_quote(currencies: tuple) -> FxQuoteValue:
    """Create FX quote for currency pair"""
    from_curr, to_curr = currencies
    # Mock exchange rates
    rates = {
        ("USD", "EUR"): 0.85,
        ("EUR", "USD"): 1.18,
        ("USD", "GBP"): 0.73,
        ("GBP", "USD"): 1.37,
        ("EUR", "GBP"): 0.86,
        ("GBP", "EUR"): 1.16,
    }
    rate = rates.get((from_curr.code, to_curr.code), 1.0)
    import datetime
    return FxQuoteValue(
        from_currency=from_curr,
        to_currency=to_curr,
        rate=rate,
        timestamp=datetime.datetime.now().isoformat()
    )

@register_action("calculate_fee", Amount, Fee)
def calculate_fee(amount: AmountValue) -> FeeValue:
    """Calculate transaction fee (2% of amount)"""
    fee_amount = AmountValue(
        value=amount.value * 0.02,
        currency=amount.currency
    )
    return FeeValue(
        amount=fee_amount,
        description=f"2% transaction fee on {amount.value} {amount.currency.code}"
    )

@register_action("convert_amount", Tuple(Amount, FxQuote), Amount)
def convert_amount(data: tuple) -> AmountValue:
    """Convert amount using FX quote"""
    amount, quote = data
    if amount.currency.code != quote.from_currency.code:
        raise ValueError(f"Currency mismatch: {amount.currency.code} != {quote.from_currency.code}")
    
    converted_value = amount.value * quote.rate
    return AmountValue(
        value=converted_value,
        currency=quote.to_currency
    )

@register_action("create_transaction", Tuple(Account, Account, Amount), Transaction)
def create_transaction(data: tuple) -> TransactionValue:
    """Create a transaction between accounts"""
    from_acc, to_acc, amount = data
    
    # Validate sufficient balance
    if from_acc.balance < amount.value:
        raise ValueError(f"Insufficient balance: {from_acc.balance} < {amount.value}")
    
    # Calculate fee
    fee = calculate_fee(amount)
    
    import datetime
    return TransactionValue(
        from_account=from_acc,
        to_account=to_acc,
        amount=amount,
        fee=fee,
        timestamp=datetime.datetime.now().isoformat()
    )

# Composition helpers
@register_action("pair_currencies", List(Currency), Tuple(Currency, Currency))
def pair_currencies(currencies: t.List[CurrencyValue]) -> tuple:
    """Create currency pair from list (first two)"""
    if len(currencies) < 2:
        raise ValueError("Need at least 2 currencies")
    return (currencies[0], currencies[1])

@register_action("quote_and_convert", Tuple(Amount, Currency), Amount) 
def quote_and_convert(data: tuple) -> AmountValue:
    """Get FX quote and convert amount in one step"""
    amount, target_currency = data
    
    # Create quote
    currencies = (amount.currency, target_currency)
    quote = create_fx_quote(currencies)
    
    # Convert
    return convert_amount((amount, quote))

class CompositionEngine:
    """Handles action composition and chaining"""
    
    @staticmethod
    def can_compose(output_type: Type, input_type: Type) -> bool:
        """Check if output of one action can feed into another"""
        from core.types import unify
        return unify(output_type, input_type)
    
    @staticmethod
    def suggest_chains(start_type: Type, max_depth: int = 3) -> t.List[t.List[str]]:
        """Suggest possible action chains from a starting type"""
        from core.actions import _registry
        
        chains = []
        
        def explore(current_type: Type, chain: t.List[str], depth: int):
            if depth >= max_depth:
                return
            
            # Find actions that accept current type
            for name, (inp, out, _) in _registry.items():
                if CompositionEngine.can_compose(current_type, inp):
                    new_chain = chain + [name]
                    if len(new_chain) > 1:  # Only add chains with 2+ actions
                        chains.append(new_chain)
                    # Recursively explore from output type
                    explore(out, new_chain, depth + 1)
        
        explore(start_type, [], 0)
        return chains
    
    @staticmethod
    def execute_chain(actions: t.List[str], initial_value: t.Any) -> t.Tuple[Type, t.Any]:
        """Execute a chain of actions"""
        from core.actions import run
        
        current_value = initial_value
        current_type = None
        
        for action in actions:
            current_type, current_value = run(action, current_value)
        
        return current_type, current_value

