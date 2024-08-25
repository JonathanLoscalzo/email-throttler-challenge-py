
FROM python:3.12
WORKDIR /code
COPY ./pyproject.toml /code/pyproject.toml
COPY ./requirements.txt /code/requirements.txt
COPY ./src /code/src

RUN pip install -e .
RUN pip install "uvicorn[standard]"
CMD ["uvicorn", "src.email_throttle.api.main:api", "--host", "0.0.0.0", "--port", "80"]
