"""
LLM Integration for Type-Safe Fill-ins
Uses type system to constrain and validate LLM outputs
"""
import typing as t
import json
from dataclasses import dataclass
from core.types import Type, List, String, Int, Float, Comment
from fileio.files import CommentValue

@dataclass
class TypeSchema:
    """Schema representation for a type"""
    type_name: str
    fields: t.Dict[str, t.Any]
    constraints: t.List[str]

class LLMTypeAdapter:
    """Adapts between types and LLM-friendly schemas"""
    
    @staticmethod
    def type_to_schema(type_: Type) -> TypeSchema:
        """Convert a Type to a schema the LLM can understand"""
        if type_.name == "Comment":
            return TypeSchema(
                type_name="Comment",
                fields={
                    "author": "string",
                    "date": "string (ISO format YYYY-MM-DD)",
                    "text": "string",
                    "source_path": "string"
                },
                constraints=[
                    "date must be valid ISO date",
                    "author cannot be empty",
                    "text cannot be empty"
                ]
            )
        elif type_.name == "Currency":
            return TypeSchema(
                type_name="Currency",
                fields={"code": "string (3-letter ISO code)"},
                constraints=["Must be valid ISO 4217 currency code"]
            )
        elif type_.name == "Amount":
            return TypeSchema(
                type_name="Amount",
                fields={
                    "value": "number (positive)",
                    "currency": "Currency object"
                },
                constraints=["value must be positive"]
            )
        elif type_.name == "List" and type_.params:
            element_schema = LLMTypeAdapter.type_to_schema(type_.params[0])
            return TypeSchema(
                type_name=f"List[{element_schema.type_name}]",
                fields={"elements": f"array of {element_schema.type_name}"},
                constraints=[f"Each element must satisfy: {element_schema.constraints}"]
            )
        else:
            return TypeSchema(
                type_name=str(type_),
                fields={},
                constraints=[]
            )
    
    @staticmethod
    def validate_against_type(value: t.Any, type_: Type) -> t.Tuple[bool, t.Optional[str]]:
        """Validate that a value conforms to a type"""
        if type_.name == "Comment":
            if not isinstance(value, dict):
                return False, "Comment must be a dict"
            required = ["author", "date", "text"]
            for field in required:
                if field not in value:
                    return False, f"Missing required field: {field}"
            # Validate date format
            import re
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", value["date"]):
                return False, "Date must be in YYYY-MM-DD format"
            return True, None
        
        elif type_.name == "Currency":
            if not isinstance(value, dict) or "code" not in value:
                return False, "Currency must have 'code' field"
            if len(value["code"]) != 3:
                return False, "Currency code must be 3 letters"
            return True, None
        
        elif type_.name == "List" and type_.params:
            if not isinstance(value, list):
                return False, "Expected a list"
            element_type = type_.params[0]
            for i, elem in enumerate(value):
                valid, error = LLMTypeAdapter.validate_against_type(elem, element_type)
                if not valid:
                    return False, f"Element {i}: {error}"
            return True, None
        
        # Default: accept
        return True, None

class LLMSuggestionEngine:
    """Provides LLM-based suggestions constrained by types"""
    
    def __init__(self):
        # In a real implementation, this would connect to an LLM API
        self.mock_mode = True
    
    def suggest_refinements(self, 
                          current_value: t.Any,
                          current_type: Type,
                          target_type: Type,
                          context: str) -> t.List[t.Dict[str, t.Any]]:
        """Suggest refinements or transformations"""
        
        if self.mock_mode:
            return self._mock_suggestions(current_value, current_type, target_type, context)
        
        # Real implementation would:
        # 1. Create prompt with type schemas
        # 2. Include current value and context
        # 3. Request suggestions that conform to target_type
        # 4. Validate all suggestions before returning
        
    def _mock_suggestions(self, current_value, current_type, target_type, context):
        """Mock suggestions for demo"""
        suggestions = []
        
        if current_type.name == "List" and current_type.params[0].name == "Comment":
            # Suggest comment filters
            suggestions.extend([
                {
                    "action": "filter_by_keyword",
                    "description": "Filter comments containing 'TODO'",
                    "preview": f"Would keep comments with 'TODO' ({len([c for c in current_value if 'TODO' in c.text])} matches)"
                },
                {
                    "action": "filter_by_date_range", 
                    "description": "Keep only last 7 days",
                    "preview": "Filter to recent comments"
                }
            ])
        
        elif target_type.name == "Comment":
            # Suggest comment templates
            suggestions.extend([
                {
                    "action": "create_comment",
                    "template": {
                        "author": "AI Assistant",
                        "date": "2025-01-14",
                        "text": f"Automated summary: Found {context}",
                        "source_path": "generated"
                    }
                }
            ])
        
        return suggestions
    
    def complete_partial_value(self, 
                             partial_value: t.Dict[str, t.Any],
                             target_type: Type) -> t.List[t.Dict[str, t.Any]]:
        """Complete a partial value to match target type"""
        
        schema = LLMTypeAdapter.type_to_schema(target_type)
        completions = []
        
        if target_type.name == "Comment":
            # Fill in missing fields
            base = partial_value.copy()
            if "author" not in base:
                base["author"] = "System"
            if "date" not in base:
                import datetime
                base["date"] = datetime.date.today().isoformat()
            if "text" not in base:
                base["text"] = "[Generated comment]"
            if "source_path" not in base:
                base["source_path"] = "llm_generated"
            
            completions.append(base)
        
        elif target_type.name == "Currency":
            # Suggest common currencies
            if "code" not in partial_value:
                for code in ["USD", "EUR", "GBP", "JPY"]:
                    completions.append({"code": code})
        
        return completions

class TypeConstrainedPrompt:
    """Build prompts that respect type constraints"""
    
    @staticmethod
    def build_prompt(instruction: str, 
                    input_type: Type,
                    output_type: Type,
                    examples: t.List[t.Tuple[t.Any, t.Any]] = None) -> str:
        """Build a type-constrained prompt"""
        
        input_schema = LLMTypeAdapter.type_to_schema(input_type)
        output_schema = LLMTypeAdapter.type_to_schema(output_type)
        
        prompt = f"""
{instruction}

Input Type: {input_schema.type_name}
Schema: {json.dumps(input_schema.fields, indent=2)}
Constraints: {', '.join(input_schema.constraints)}

Output Type: {output_schema.type_name}
Schema: {json.dumps(output_schema.fields, indent=2)}
Constraints: {', '.join(output_schema.constraints)}
"""
        
        if examples:
            prompt += "\n\nExamples:\n"
            for inp, out in examples:
                prompt += f"Input: {json.dumps(inp, indent=2)}\n"
                prompt += f"Output: {json.dumps(out, indent=2)}\n\n"
        
        prompt += "\nProvide output as valid JSON matching the output schema."
        
        return prompt

# Specific suggestion functions
def suggest_comment_filters(comments: t.List[CommentValue]) -> t.List[t.Callable]:
    """Suggest filters based on comment content"""
    suggestions = []
    
    # Analyze comments
    authors = {c.author for c in comments}
    keywords = set()
    for c in comments:
        words = c.text.lower().split()
        keywords.update(w for w in words if len(w) > 4)
    
    # Create filter suggestions
    if len(authors) > 1:
        for author in authors:
            suggestions.append(
                lambda cs, a=author: [c for c in cs if c.author == a]
            )
    
    common_keywords = [k for k in keywords if 
                      sum(1 for c in comments if k in c.text.lower()) > 1]
    
    for keyword in common_keywords[:5]:  # Top 5 keywords
        suggestions.append(
            lambda cs, k=keyword: [c for c in cs if k in c.text.lower()]
        )
    
    return suggestions

