from typing import Optional


class EmailMessage:
    def __init__(
        self,
        subject: str,
        body: str,
        to: list[str],
        from_email: str,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        attachments: Optional[list[str]] = None,
        is_html: bool = False,
        links: Optional[list[str]] = None,
    ):
        self.subject = subject
        self.body = body
        self.to = to
        self.from_email = from_email
        self.cc = cc or []
        self.bcc = bcc or []
        self.attachments = attachments or []
        self.is_html = is_html
        self.links = links or []
