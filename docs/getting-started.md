# Getting Started with DeepSeek Wrapper

This guide will help you set up and run the DeepSeek Wrapper on your local machine.

## Prerequisites

- Python 3.8 or higher
- DeepSeek API key ([sign up here](https://platform.deepseek.com))
- Git (optional, for cloning the repository)

## Installation

1. Clone the repository or download the source code:
   ```bash
   git clone https://github.com/yourusername/DeepSeek-Wrapper.git
   cd DeepSeek-Wrapper
   ```

2. Create a virtual environment (recommended):
   ```bash
   # On Windows
   python -m venv .venv
   .\.venv\Scripts\activate

   # On macOS/Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy the `.env.example` file to `.env`
   - Open the `.env` file and add your DeepSeek API key:
     ```
     DEEPSEEK_API_KEY=your_api_key_here
     ```

## Running the Application

To start the web interface, run:

```bash
# On Windows
python -m src.deepseek_wrapper.main

# On macOS/Linux
python -m src.deepseek_wrapper.main
```

The application will start and be accessible at [http://localhost:8000](http://localhost:8000) by default.

## Verifying Installation

To check if your installation is working correctly:

1. Open your browser and navigate to [http://localhost:8000](http://localhost:8000)
2. Try sending a message in the chat interface
3. You should receive a response from the DeepSeek AI

## Next Steps

- Explore the [Web UI Guide](web-ui-guide.md) for details on using the interface
- Learn about all available [Features](features.md)
- For developers, check the [API Reference](api-reference.md)

## Troubleshooting

If you encounter any issues:

- Ensure your API key is correctly set in the `.env` file
- Check your internet connection
- Verify that you have the correct Python version (3.8+)
- Make sure all dependencies are installed properly

For more help, see the [FAQ](faq.md) or open an issue on GitHub. 