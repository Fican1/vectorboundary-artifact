FROM debian:trixie
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc-riscv64-linux-gnu g++-riscv64-linux-gnu \
    qemu-user \
    cmake ninja-build git python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
