# Examples

This directory contains demonstration scripts showcasing the simpleton-computer type system and action engine.

## Demo Files

### `demo.py` - Comprehensive Demo
The main demonstration script that shows all major features:
- Extracting comments from documents
- Extracting tasks from documents
- Loading mixed content (comments, tasks, links)
- Using the plan and execution engine

Run with: `python -m examples.demo`

### `comments_demo.py` - Comment Extraction
Focused demonstration of comment extraction functionality.

Run with: `python -m examples.comments_demo`

### `tasks_demo.py` - Task Extraction
Focused demonstration of task extraction functionality.

Run with: `python -m examples.tasks_demo`

### `mixed_demo.py` - Mixed Content Loading
Simple demonstration of loading and displaying mixed content types.

Run with: `python -m examples.mixed_demo`

## Sample Data Files

- `sample_comments.txt` - Contains sample comment data in the format `[author|date] text`
- `sample_mixed_content.txt` - Contains mixed content including comments, tasks, and links

## Expected Output for Main Demo

When running `python -m examples.demo`, you should see:

1. **Extracted comments** - List of comment objects parsed from the document
2. **Extracted tasks** - List of task objects parsed from the document
3. **All mixed content** - Display of all content types found in the document
4. **Plan trace** - Shows the execution plan used by the engine
5. **Final value** - The resulting task list after planned execution