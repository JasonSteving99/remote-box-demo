# Remote Code Execution Demo

A minimal web application demonstrating safe arbitrary Python code execution in sandboxed E2B environments using the `@remote` decorator.

## Features

- 🎨 Clean, modern web interface
- 🐍 Python syntax highlighting
- 🔒 Safe code execution in isolated E2B sandboxes
- ⚡ Real-time output display
- 🚀 FastAPI backend

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Create a `.env.local` file with your E2B configuration:
```bash
E2B_API_KEY=your_api_key_here
```

## Running the Application

Start the FastAPI server:

```bash
fastapi dev app.py
```

Then open your browser to [http://localhost:8000](http://localhost:8000)

## How It Works

The application consists of:

1. **Frontend**: A simple HTML interface with a code editor and output panel
2. **Backend**: FastAPI server that accepts Python code via POST request
3. **Sandbox Execution**: Code is executed inside a function decorated with `@remote`, which runs it in an isolated E2B sandbox environment

### Example Code to Try

```python
import os
import sys

print('Hello from E2B sandbox!')
print(f'Python version: {sys.version}')
print(f'Sandbox ID: {os.getenv("E2B_SANDBOX_ID")}')

# Try some computation
result = sum(range(100))
print(f'Sum of 0-99: {result}')
```

## Security

All code execution happens in isolated E2B sandbox environments, making it safe to run arbitrary user code without compromising the host system.
