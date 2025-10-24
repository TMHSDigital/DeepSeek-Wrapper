# Getting Started with DeepSeek Wrapper

<div style="padding: 20px; background: #f8f9fa; border-radius: 8px; margin-bottom: 25px;">
  <p style="margin-top: 0;"><strong>This guide will help you set up and run the DeepSeek Wrapper on your local machine.</strong></p>
</div>

## Prerequisites

<div style="display: flex; flex-wrap: wrap; gap: 15px; margin: 20px 0;">
  <div style="flex: 1; min-width: 200px; padding: 15px; background: #E8F4FD; border-radius: 8px;">
    <strong>Python 3.8+</strong><br>
    <small>Required to run the application</small>
  </div>
  <div style="flex: 1; min-width: 200px; padding: 15px; background: #E8F4FD; border-radius: 8px;">
    <strong>DeepSeek API Key</strong><br>
    <small><a href="https://platform.deepseek.com">Sign up here</a></small>
  </div>
  <div style="flex: 1; min-width: 200px; padding: 15px; background: #E8F4FD; border-radius: 8px;">
    <strong>Git</strong><br>
    <small>Optional, for cloning the repository</small>
  </div>
</div>

## Installation

<div style="padding: 0; border-left: 4px solid #4A90E2;">
  <div style="padding: 10px 15px;">
    <p><strong>1. Clone the repository or download the source code</strong></p>
    
    ```bash
    git clone https://github.com/TMHSDigital/DeepSeek-Wrapper.git
    cd DeepSeek-Wrapper
    ```
  </div>
</div>

<div style="padding: 0; border-left: 4px solid #4A90E2; margin-top: 15px;">
  <div style="padding: 10px 15px;">
    <p><strong>2. Create a virtual environment (recommended)</strong></p>
    
    ```bash
    # On Windows
    python -m venv .venv
    .\.venv\Scripts\activate

    # On macOS/Linux
    python -m venv .venv
    source .venv/bin/activate
    ```
  </div>
</div>

<div style="padding: 0; border-left: 4px solid #4A90E2; margin-top: 15px;">
  <div style="padding: 10px 15px;">
    <p><strong>3. Install the required dependencies</strong></p>
    
    ```bash
    pip install -r requirements.txt
    ```
  </div>
</div>

<div style="padding: 0; border-left: 4px solid #4A90E2; margin-top: 15px; margin-bottom: 25px;">
  <div style="padding: 10px 15px;">
    <p><strong>4. Set up environment variables</strong></p>
    <ul>
      <li>Copy the <code>.env.example</code> file to <code>.env</code> (if present), or create a new <code>.env</code> file</li>
      <li>Open the <code>.env</code> file and add your DeepSeek API key:</li>
    </ul>
    
    ```
    DEEPSEEK_API_KEY=your_api_key_here
    ```
    
    Windows PowerShell quickstart to create <code>.env</code>:
    
    ```powershell
    "DEEPSEEK_API_KEY=sk-your-key" | Out-File -FilePath .env -Encoding ascii
    ```
  </div>
</div>

## Running the Application

<div style="padding: 15px; background: #F5FFF7; border-radius: 8px; border-left: 4px solid #50C878; margin-bottom: 25px;">
  <p style="margin-top: 0;"><strong>To start the web interface, run:</strong></p>
  
  ```bash
  # On Windows, macOS, or Linux
  uvicorn src.deepseek_wrapper.web:app --reload
  ```
  
  <p>The application will start and be accessible at <a href="http://localhost:8000">http://localhost:8000</a> by default.</p>
</div>

## Verifying Installation

<div style="counter-reset: step;">
  <div style="display: flex; margin-bottom: 10px; align-items: center;">
    <div style="background: #4A90E2; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; margin-right: 10px; flex-shrink: 0;">1</div>
    <div>Open your browser and navigate to <a href="http://localhost:8000">http://localhost:8000</a></div>
  </div>
  
  <div style="display: flex; margin-bottom: 10px; align-items: center;">
    <div style="background: #4A90E2; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; margin-right: 10px; flex-shrink: 0;">2</div>
    <div>Try sending a message in the chat interface</div>
  </div>
  
  <div style="display: flex; margin-bottom: 20px; align-items: center;">
    <div style="background: #4A90E2; color: white; border-radius: 50%; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; margin-right: 10px; flex-shrink: 0;">3</div>
    <div>You should receive a response from the DeepSeek AI</div>
  </div>
</div>

## Next Steps

<div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0;">
  <a href="web-ui-guide.md" style="flex: 1; min-width: 200px; padding: 15px; background: #F5F9FF; border-radius: 8px; text-decoration: none; color: inherit;">
    <strong style="color: #4A90E2;">Web UI Guide</strong><br>
    Details on using the interface
  </a>
  <a href="features.md" style="flex: 1; min-width: 200px; padding: 15px; background: #F5F9FF; border-radius: 8px; text-decoration: none; color: inherit;">
    <strong style="color: #4A90E2;">Features</strong><br>
    Learn about all features
  </a>
  <a href="api-reference.md" style="flex: 1; min-width: 200px; padding: 15px; background: #F5F9FF; border-radius: 8px; text-decoration: none; color: inherit;">
    <strong style="color: #4A90E2;">API Reference</strong><br>
    Documentation for developers
  </a>
</div>

## Troubleshooting

<div style="padding: 15px; background: #FFF5F5; border-radius: 8px; border-left: 4px solid #FF6B6B; margin-top: 20px;">
  <p style="margin-top: 0;"><strong>Common Issues</strong></p>
  <ul>
    <li>Ensure your API key is correctly set in the <code>.env</code> file</li>
    <li>Check your internet connection</li>
    <li>Verify that you have the correct Python version (3.8+)</li>
    <li>Make sure all dependencies are installed properly</li>
  </ul>
  <p>For more help, see the <a href="faq.md">FAQ</a> or open an issue on GitHub.</p>
</div> 