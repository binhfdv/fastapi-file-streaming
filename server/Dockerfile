FROM python:3.12

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

CMD ["python", "pydash.py", "--host", "0.0.0.0", "--port", "8080", "--datadir", "./media"]