## Key Principles
- **Terminal Commands**: Use Windows PowerShell commands.
- **Test Code**: Write test code in different files. Do not mix test code and functional code in one file. Pytest files in the /tests directory are preferred.
- **Readability and Reproducibility**: Prioritize readability and reproducibility in data analysis workflows.
- **Vectorized Operations**: Prefer vectorized operations over explicit loops for better performance.
- **Descriptive Variable Names**: Use descriptive variable names that reflect the data they contain.

## Code Style
- **PEP 8 Compliance**: Follow PEP 8 style for Python code formatting.
- **Black Formatter Compliance**: Follow Black Formatter style for Python code formatting.

## Data Analysis and Manipulation
- **Pandas**: Use **Pandas** for data manipulation and analysis.
- **Method Chaining**: Prefer method chaining for data transformations when possible.

## Visualization
- **Informative Plots**: Create informative and visually appealing plots with proper labels, titles, and legends.
- **Color Schemes**: Use appropriate color schemes and consider color-blindness accessibility.
- **Reusable Plotting Functions**: Create reusable plotting functions for consistent visualizations.

## Error Handling and Data Validation
- **Data Quality Checks**: Implement data quality checks at the beginning of analysis.
- **Missing Data**: Handle missing data appropriately (imputation, removal, or flagging).
- **Error-Prone Operations**: Use try-except blocks for error-prone operations, especially when reading external data.
- **Logging**: Capture context in logs for better debugging. Use logging instead of print().
- **Data Validation**: Validate data types and ranges to ensure data integrity.
- **Typing Annotation** Always add typing annotations to each function or class, including return types when necessary.
- **Type Hints**: Use built-in type hints without importing from **typing** module as long as possible.

## Performance Optimization
- **Vectorized Operations**: Use vectorized operations in Pandas and NumPy for improved performance.
- **Efficient Data Structures**: Utilize efficient data structures (e.g., categorical data types for low-cardinality string columns).
- **Code Profiling**: Profile code to identify and optimize bottlenecks.

## Dependencies
- **Pandas**: For data manipulation and analysis.
- **Matplotlib**: For plotting and visualization.
- **Seaborn**: For statistical visualizations.
- **Scikit-learn**: For machine learning tasks.

## Documentation
- Document data sources, assumptions, and methodologies clearly.
- **Add descriptive docstrings** to all Python functions and classes.
- **Update existing docstrings** if necessary.
- **Docstring Style**: Google.

## References
Refer to the official documentation of Pandas, Matplotlib for best practices and up-to-date APIs.
