import os
import logging

logger = logging.getLogger(__name__)

async def create_module(filename: str, code: str):
    """
    Creates a new python module in modules/ directory.
    filename: e.g. "math_utils.py"
    code: The python code.
    """
    if ".." in filename or filename.startswith("/"):
        return "Error: Invalid filename."

    filepath = os.path.join("modules", filename)
    with open(filepath, "w") as f:
        f.write(code)

    return f"Module {filename} created. You may need to restart or reload to use it."
