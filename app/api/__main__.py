"""python -m app.api → uvicorn :8765"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host="127.0.0.1", port=8765, reload=False)
