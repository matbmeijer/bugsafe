---
description: Testing conventions for bugsafe
paths: tests/**/*.py
---

# Testing Conventions

## Test Structure

- One test file per module: `test_<module>.py`
- Group related tests in classes: `class TestFeatureName`
- Use descriptive test names: `test_<action>_<condition>_<expectation>`

## Fixtures

- Use pytest fixtures for setup/teardown
- Prefer function-scoped fixtures
- Use `tmp_path` for temporary files

## Assertions

- Use plain `assert` statements (pytest rewrites them)
- One logical assertion per test
- Use `pytest.raises` for exception testing

## Property Testing

- Use `hypothesis` for property-based tests
- Define strategies in `tests/conftest.py`
- Mark slow tests with `@pytest.mark.slow`

## Coverage

- Maintain high coverage on `src/bugsafe/`
- Exclude `if TYPE_CHECKING:` blocks
- Exclude `if __name__ == "__main__":` blocks
