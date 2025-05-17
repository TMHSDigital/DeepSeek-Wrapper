# Code Highlighting UI Placeholder

**Note:** This document serves as a placeholder for the `code-highlighting.png` image that should be created and added to this directory.

## Recommended Screenshot Content

The code highlighting image should display an example of syntax-highlighted code in the DeepSeek Wrapper chat interface:

```
+------------------------------------------+
|                                          |
|  AI: Here's a Python function that       |
|  calculates Fibonacci numbers:           |
|                                          |
|  ```python                               |
|  def fibonacci(n):                       |
|      """                                 |
|      Calculate the nth Fibonacci number  |
|      using dynamic programming.          |
|      """                                 |
|      if n <= 0:                          |
|          return 0                        |
|      elif n == 1:                        |
|          return 1                        |
|                                          |
|      # Initialize array to store values  |
|      fib = [0] * (n + 1)                 |
|      fib[1] = 1                          |
|                                          |
|      # Bottom-up approach                |
|      for i in range(2, n + 1):           |
|          fib[i] = fib[i-1] + fib[i-2]    |
|                                          |
|      return fib[n]                       |
|  ```                                     |
|                                          |
|  You can use this function like this:    |
|  `result = fibonacci(10)`                |
|                                          |
+------------------------------------------+
```

## Annotation Guidelines

When creating the code highlighting screenshot:

1. Show these key features:
   - **1** - Distinct syntax highlighting for different code elements (keywords, strings, comments)
   - **2** - Language identification in the top-right of the code block
   - **3** - Copy button for the code block
   - **4** - Proper code formatting with indentation preserved

2. Use a clean, readable monospace font for code

3. Include sample code in a commonly used language (Python, JavaScript, etc.)

## Image Specifications

- **Format:** PNG
- **Resolution:** At least 1200 x 800 pixels
- **Size:** Keep under 300KB (optimize for web)
- **Filename:** `code-highlighting.png` 