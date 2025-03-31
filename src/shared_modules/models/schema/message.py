from http import HTTPStatus

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    response: str
    status: HTTPStatus
