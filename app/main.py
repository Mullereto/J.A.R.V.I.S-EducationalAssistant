from fastapi import FastAPI
from app.routers import preprocess

app = FastAPI(title="Study Assistant", version="0.1")


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "CourseTA API is running"}



# Register Routers
app.include_router(preprocess.router)
