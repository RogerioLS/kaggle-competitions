# 02 — Python Standards & Clean Code

## Standards
1. **Line Length**: Max 100 characters (enforced by Black, Flake8, and Ruff).
2. **Type Hints**: All functions, methods, and classes must have complete type annotations.
3. **Docstrings**: Google or NumPy style docstrings for all modules, classes, and public functions.
4. **Error Handling**: Use explicit exceptions; do not use bare `except:`.
5. **No Spaghetti Notebooks in Production**: Exploratory work can use notebooks, but core logic, agents, and harnesses must live in pure Python modules.
