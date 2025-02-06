FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    git cmake g++ make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone --depth 1 --branch 1.5.7 https://github.com/google/draco.git && cd draco \
    && mkdir build_dir && cd build_dir \
    && cmake ../ \
    && make -j$(nproc)

# Set environment variables
ENV PATH="/app/draco/build_dir:$PATH"

COPY compress.sh /app/compress.sh
RUN chmod +x /app/compress.sh

# Set entrypoint to run the script
# ENTRYPOINT ["/app/compress.sh"]

