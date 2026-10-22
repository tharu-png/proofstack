

from fastapi import FastAPI

from app.api.documents import router as documents_router


app = FastAPI(
    title="ProofStack API",
    description="An evidence-grounded AI research engine",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "proofstack-api",
        "version": "0.1.0",
    }


app.include_router(documents_router)
