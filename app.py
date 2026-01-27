from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from remote import remote, E2B
from dotenv import load_dotenv
from io import StringIO
import traceback
from contextlib import redirect_stdout


load_dotenv(".env.local")

app = FastAPI(title="Remote Code Execution Demo")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


class CodeInput(BaseModel):
    code: str


class CodeOutput(BaseModel):
    output: str
    error: str | None = None


@app.get("/")
async def index():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


async def get_flights():
    return ["Flight 1", "Flight 2", "Flight 3"]


@remote(
    local_project_root=Path(__file__).parent,
    backend=E2B(template_prefix="test-remote-box1", template_version="0_1_5"),
    timeout_millis=10_000,  # 10 seconds
)
async def execute_remote_code(input: CodeInput) -> CodeOutput:
    """Execute user-provided code in a sandboxed environment."""
    output_buffer = StringIO(newline="")

    with redirect_stdout(output_buffer):
        try:
            # Create a namespace with explicitly allowed functions/variables
            namespace = {
                "get_flights": get_flights,
                # Add other safe functions/modules here as needed
                # "requests": requests,
                # "json": json,
            }

            # Wrap the user's code in an async function
            wrapped_code = "async def __async_exec():\n"
            for line in input.code.split("\n"):
                wrapped_code += f"    {line}\n"

            # Execute to define the async function in the namespace
            exec(wrapped_code, namespace)

            # Call the function and await the result
            await namespace["__async_exec"]()
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return CodeOutput(output=output_buffer.getvalue(), error=error_msg)

    return CodeOutput(output=output_buffer.getvalue(), error=None)


@app.post("/execute", response_model=CodeOutput)
async def execute_code(request: CodeInput):
    """Execute Python code in a remote sandboxed environment."""
    try:
        return await execute_remote_code(request)
    except Exception as e:
        return CodeOutput(output="", error=f"Execution failed: {type(e).__name__}: {str(e)}")
