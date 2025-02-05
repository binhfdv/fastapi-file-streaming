FROM python:3.12

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

CMD ["python", "scheduled_request.py", "--interval", "2", "--api", "http://172.17.0.1:8080/stream", "--project", "foo", "--ext", "drc"]