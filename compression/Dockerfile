FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    git cmake g++ make python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install redis

WORKDIR /app

RUN git clone --depth 1 --branch 1.5.7 https://github.com/google/draco.git && cd draco \
    && mkdir build_dir && cd build_dir \
    && cmake ../ \
    && make -j$(nproc)

# Set environment variables
ENV PATH="/app/draco/build_dir:$PATH"

COPY compress.sh /app/compress.sh
COPY store_to_redis.py /app/store_to_redis.py

RUN chmod +x /app/compress.sh

ENV REDIS_HOST=redis
ENV REDIS_PORT=6379

ENTRYPOINT ["/app/compress.sh"]