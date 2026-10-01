import uvicorn


def main():
    """Development entrypoint to start the FastAPI server."""
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
