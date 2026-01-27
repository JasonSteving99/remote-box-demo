import asyncio
from remote import remote, E2B
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv(".env.local")


class Input(BaseModel):
    name: str


class Output(BaseModel):
    res: str


@remote(
    local_project_root=Path(__file__).parent,
    backend=E2B(template_prefix="test-remote-box1", template_version="0_1_1"),
)
async def main(input: Input) -> Output:
    return Output(res=f"Hello from {input.name}! (E2B ID: {os.getenv('E2B_SANDBOX_ID')}")


async def run() -> list[Output]:
    return await asyncio.gather(*(main(Input(name=f"remotesupercomputer {i}")) for i in range(5)))


if __name__ == "__main__":
    res = asyncio.run(run())

    print("\n".join(r_i.model_dump_json() for r_i in res))
