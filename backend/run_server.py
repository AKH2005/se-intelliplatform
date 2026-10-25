import sys
import asyncio
import uvicorn
import uvicorn.loops.asyncio

if sys.platform == "win32":
    # Ensure uvicorn uses SelectorEventLoop for psycopg async compatibility on Windows
    uvicorn.loops.asyncio.asyncio_loop_factory = lambda use_subprocess=False: asyncio.SelectorEventLoop

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info", loop="asyncio")
