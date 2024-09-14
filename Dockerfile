FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.authors="SlothCroissant"
LABEL org.opencontainers.image.url="https://github.com/SlothCroissant/proxmox-auto-installer-server"
LABEL org.opencontainers.image.source="https://github.com/SlothCroissant/proxmox-auto-installer-server"
LABEL org.opencontainers.image.title="Proxmox Auto-Install Server"
LABEL org.opencontainers.image.description="HTTP server for Proxmox 8.2+ Automated Install via HTTP/URL, written in Python."
LABEL org.opencontainers.image.vendor="SlothCroissant"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.base.name="library/python:3.12-slim-bookworm"

COPY app /app
WORKDIR /app

RUN apt-get update
RUN apt-get install -y \
    gcc

RUN pip install -r requirements.txt

ARG PUID=1000
ARG PGID=1000

RUN groupadd -g "${PGID}" python \
  && useradd --create-home --no-log-init -u "${PUID}" -g "${PGID}" python

USER python

CMD ["python3", "server.py"]