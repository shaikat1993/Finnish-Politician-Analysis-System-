# UI Smoke Tests

## Purpose
Basic smoke tests to verify frontend components can be imported and initialized.

## What These Tests Do
- ✅ Test that frontend modules can be imported
- ✅ Test that components can be instantiated
- ✅ Test that required files exist
- ✅ Test API URL configuration

## What These Tests DON'T Do
- ❌ Don't start Streamlit server
- ❌ Don't require API to be running
- ❌ Don't render actual UI
- ❌ Don't make network requests

## Running the Tests

```bash
# Run UI smoke tests
pytest tests/ui/ -v

# Run with main test suite
pytest tests/ -v