import os
import uvicorn
from google.adk.cli.fast_api import get_fast_api_app

# Cloud Run provides the PORT environment variable
port = int(os.environ.get("PORT", 8080))

# Fixed: Added web=True (required) and plural agents_dir
app = get_fast_api_app(
    agents_dir=".", 
    web=True
)

if __name__ == "__main__":
    # Host 0.0.0.0 is mandatory for Cloud Run
    uvicorn.run(app, host="0.0.0.0", port=port)

