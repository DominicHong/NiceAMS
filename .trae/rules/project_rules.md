# General Rules

## Key Principles
- **Terminal Commands**: Run command in Windows CMD terminal. Use Windows CMD commands. Do NOT use PowerShell commands.
- **Test Code**: Write test code in different files. Do not mix test code and functional code in one file.
- **Readability and Reproducibility**: Prioritize readability and reproducibility in all workflows.
- **Descriptive Variable Names**: Use descriptive variable names that reflect the data they contain.
- **Documentation**: Maintain clear and up-to-date documentation for all components.

# Frontend Rules

## Technology Stack
- **Framework**: Use Vue.js for building user interfaces
- **Language**: TypeScript for type-safe development
- **Build Tool**: Vite for development and production builds
- **State Management**: Pinia for application state management
- **Routing**: Vue Router for client-side routing

## Code Style
- Follow ESLint configuration defined in the project
- Props should be typed and have clear validation
- Use TypeScript interfaces for complex data structures

## Component Architecture
- Create reusable components in the `src/components` directory
- Use composition API with `<script setup>` syntax
- Separate business logic from presentation components
- Implement proper component communication patterns
- Follow Vue's single-file component best practices

## Performance
- Implement code splitting for route-based lazy loading
- Use Vue's built-in reactivity optimizations
- Implement virtual scrolling for long lists

## Testing
- Write unit tests for components using Vitest
- Implement component integration tests

# Backend Rules

## Technology Stack
- **Language**: Python 3.12+
- **Data Manipulation**: Pandas for data manipulation and analysis
- **Testing**: pytest for unit and integration testing
- **API Development**: FastAPI for building APIs 
- **Type Hints**: Use built-in type hints **without** importing from typing module when possible

## Code Style
- **PEP 8 Compliance**: Follow PEP 8 style for Python code formatting
- **Black Formatter**: Use Black for code formatting

## Data Analysis and Manipulation
- **Method Chaining**: Prefer method chaining for data transformations when possible
- **Vectorized Operations**: Use vectorized operations over explicit loops for better performance

## Error Handling and Data Validation
- Implement data quality checks at the beginning of analysis
- Handle missing data appropriately (imputation, removal, or flagging)
- Validate data types and ranges to ensure data integrity
- Use logging instead of print() statements

## Testing
- Write pytest files in the /tests directory
- Create separate test files for different modules
- Use fixtures for test data setup

## Documentation
- Add descriptive Google-style docstrings to all functions and classes
- Update existing docstrings when modifying functionality
- Document data sources, assumptions, and methodologies
- Include examples for complex functions and methods
