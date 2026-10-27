"""Anywhere Stack — entry point for Replit and local development."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("anywhere.api:app", host="0.0.0.0", port=8080, reload=False)
