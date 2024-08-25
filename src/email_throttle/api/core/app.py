from fastapi import FastAPI

from email_throttle.api.endpoints.hello import hello
from email_throttle.api.endpoints.emails import router as send_email


def create_api():
    api = FastAPI()

    api.include_router(hello.router)
    api.include_router(send_email.router, prefix="/email")

    return api
