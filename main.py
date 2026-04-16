from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.services.genderize import classify_name_with_genderize
from app.utils.exceptions import NoPredictionError, UpstreamServiceError
from app.utils.responses import fail_response, success_response


@asynccontextmanager
async def lifespan(app: FastAPI):
	# Reuse one async client across requests for lower overhead and better stability.
	app.state.http_client = httpx.AsyncClient(timeout=httpx.Timeout(2.5))
	try:
		yield
	finally:
		await app.state.http_client.aclose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
	detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
	return fail_response(status_code=exc.status_code, message=detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
	# Map query-parameter type issues to the required error structure and message.
	for err in exc.errors():
		if err.get("loc") and "name" in err["loc"]:
			return fail_response(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, message="name is not a string")
	return fail_response(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, message="Validation error")


@app.get("/health", include_in_schema=False)
async def health():
	return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "Genderize API",
        "docs": "/docs"
    }


@app.get("/api/classify")
async def classify_name(name: str | None = Query(default=None)):
	if name is None or not isinstance(name, str) or not name.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing or empty name parameter")

	cleaned_name = name.strip()
	client: httpx.AsyncClient = app.state.http_client

	try:
		result = await classify_name_with_genderize(client=client, name=cleaned_name)
	except NoPredictionError as exc:
		raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
	except UpstreamServiceError as exc:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

	return success_response(status_code=status.HTTP_200_OK, data=result)
