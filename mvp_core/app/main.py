from fastapi import FastAPI

app = FastAPI(title="Ketter 3.0 MVP Core")

@app.get("/health")
def health():
    return {"status": "ok", "component": "api"}
