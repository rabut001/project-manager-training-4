FROM mcr.microsoft.com/devcontainers/javascript-node:24-bookworm

# 問題冊子の問番号の位置を探すのに使う
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-jpn \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /uvx /usr/local/bin/

ENV UV_PYTHON=3.13 \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    UV_LINK_MODE=copy

RUN uv python install 3.13 && chmod -R a+rX /opt/uv-python
