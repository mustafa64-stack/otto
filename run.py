import uvicorn
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"Starting Otto Gateway on http://{host}:{port}")
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)

