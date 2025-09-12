from fastapi import FastAPI
from .routers import preprocess, summarize, questions, qa

app = FastAPI(title="J.A.R.V.I.S - Study Assistant", version="0.1")


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "CourseTA API is running"}



# Register Routers
app.include_router(preprocess.router)
app.include_router(summarize.router)
app.include_router(questions.router)
app.include_router(qa.router)