FROM debian:bookworm-slim

RUN \
    set -eux; \
    apt-get update; \
    apt-get install -y \
    --no-install-recommends \
    python3 \
    python3-pip \
    firefox-esr; \
    apt-get update && apt-get install -y locales \
	&& localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8; \
    rm -rf /var/lib/apt/lists/* 

RUN pip install -U pip && pip install -U wheel && pip install -U setuptools

WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt --no-cache-dir && rm -r requirements.txt

EXPOSE 5000
USER appuser
CMD ["python3", "app.py"]

ENV LANG en_US.utf8

HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:5000/ || exit 1