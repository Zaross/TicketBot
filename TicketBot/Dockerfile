FROM python:3.12-alpine

WORKDIR /app

COPY CustomModules ./CustomModules
COPY *.py .
COPY requirements.txt .

ENV TERM=xterm
ENV PYTHONUNBUFFERED=1

ARG TARGETPLATFORM
ARG BUILD_DATE
ARG COMMIT

RUN apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev libc-dev linux-headers rust cargo g++ && \
    apk add curl && \
    python -m pip install --upgrade pip && \
    pip install --upgrade setuptools wheel && \
    pip install -r requirements.txt && \
    apk del .build-deps && \
    find /usr/local \
    \( -type d -a -name test -o -name tests \) \
    -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
    -exec rm -rf '{}' + && \
    rm -rf /root/.cache/pip

LABEL maintainer="Discord: zaros. (411763301169496084)" \
      commit=$COMMIT \
      description="Basic discord ticketbot." \
      release=$BUILD_DATE \
      VERSION="1.0.0" \
      url="https://github.com/Zaross/TicketBot"

CMD ["python3", "main.py"]
