FROM python:3.12

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 172.17.0.1 is interface network of docker, ip addr show docker0
# 172.17.0.1:8080/stream --points to--> 0.0.0.0:8080/stream (or any ip the server is running on host)
CMD ["python", "scheduled_request.py", "--interval", "2", "--api", "http://172.17.0.1:8080/stream", "--project", "foo", "--ext", "drc"]