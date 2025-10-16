from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="Ukrainian Corrector Backend Test", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URL ML сервісу - ЗАМІНІТЬ на свій URL після деплою на HF
ML_SERVICE_URL = os.getenv(
    "ML_SERVICE_URL",
    "https://viacheslavfomenko-perom.hf.space/health"
)


class CheckRequest(BaseModel):
    text: str


@app.get("/")
def root():
    return {
        "message": "🇺🇦 Ukrainian Corrector Backend API",
        "status": "running",
        "version": "1.0.0",
        "ml_service": ML_SERVICE_URL
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/check")
async def check_text(request: CheckRequest):
    '''Перевірка тексту через ML сервіс'''

    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if len(request.text) > 5000:
        raise HTTPException(status_code=400, detail="Text is too long (max 5000 characters)")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"Sending request to ML service: {ML_SERVICE_URL}/check")

            response = await client.post(
                f"{ML_SERVICE_URL}/check",
                json={"text": request.text}
            )

            response.raise_for_status()
            result = response.json()

            print(f"ML service response: {result}")
            return result

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="ML service timeout. Please try again."
        )
    except httpx.HTTPError as e:
        print(f"Error calling ML service: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"ML service error: {str(e)}"
        )


@app.get("/api/test")
def test():
    '''Тестовий endpoint без виклику ML сервісу'''
    return {
        "message": "Backend працює!",
        "ml_service_url": ML_SERVICE_URL,
        "test": "success"
    }


@app.get("/api/test-ml")
async def test_ml():
    '''Тест підключення до ML сервісу'''
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ML_SERVICE_URL}/test")
            return {
                "backend": "OK",
                "ml_service": response.json(),
                "connection": "success"
            }
    except Exception as e:
        return {
            "backend": "OK",
            "ml_service": "ERROR",
            "error": str(e),
            "connection": "failed"
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)