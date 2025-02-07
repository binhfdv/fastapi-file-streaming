FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    git cmake g++ make \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y unzip

WORKDIR /app

RUN git clone --depth 1 --branch 1.5.7 https://github.com/google/draco.git && cd draco \
    && mkdir build_dir && cd build_dir \
    && cmake ../ \
    && make -j$(nproc)

# Set environment variables
ENV PATH="/app/draco/build_dir:$PATH"

COPY depress.sh /app/depress.sh
RUN chmod +x /app/depress.sh

# Set entrypoint to run the script
ENTRYPOINT ["/app/depress.sh"]

