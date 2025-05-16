Create a Python wrapper for DeepSeek LLM that can run locally. Include the following:

1. Project structure with appropriate files and directories:
   - src/ directory with modular code
   - tests/ directory with comprehensive unit tests
   - README.md with clear documentation
   - requirements.txt for dependencies
   - setup.py for package installation

2. Core functionality:
   - Implement a client class that can interact with DeepSeek's API
   - Support for all main DeepSeek features (text generation, chat completion, etc.)
   - Async and sync methods for API calls
   - Proper error handling and retries
   - Type hints throughout the codebase

3. Configuration:
   - API key management (env variables and .env file support)
   - Customizable request parameters
   - Connection settings (timeout, retries, etc.)

4. Documentation:
   - Class and method docstrings
   - Usage examples
   - Installation instructions
   - API reference

5. Testing:
   - Unit tests with pytest
   - Mock responses for testing without API calls
   - Test coverage report

6. GitHub setup:
   - Initialize git repository
   - Create .gitignore file (include .env, __pycache__, etc.)
   - Add GitHub Actions workflow for CI/CD
   - Create LICENSE file (MIT license)

7. Additional files:
   - CONTRIBUTING.md with guidelines
   - .pre-commit-config.yaml for code quality checks

Please implement this project with clean, maintainable code following best practices for Python development.