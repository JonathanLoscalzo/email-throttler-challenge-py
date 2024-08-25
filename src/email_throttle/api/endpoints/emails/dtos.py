from pydantic import BaseModel


class EmailDto(BaseModel):
    subject: str
    body: str
    to: list[str]
    from_email: str
