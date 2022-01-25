FROM python:3.8.12-slim-bullseye AS builder

RUN useradd -u 1001 -G root app && \
    chgrp -R 0 /etc/passwd && \
    chmod -R g=u /etc/passwd && \
    mkdir /app && \
    chgrp -R 0 /app && \
    chmod -R g=u /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libgeos-3.9.0 \
        libproj19

ARG PIP_VERSION="pip==21.3.1"
ARG SETUPTOOL_VERSION="setuptools==60.5.0"
COPY setup.py setup.cfg README.rst LICENSE CHANGELOG.md /app/
COPY cjio /app/cjio
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN cd /app && \
    python3 -m pip install ${PIP_VERSION} ${SETUPTOOL_VERSION} && \
    pip install .[export,validate,reproject] && \
    rm -rf /tmp/* && \
    rm -rf /user/local/man && \
    cjio --version

FROM python:3.8.12-slim AS cjio
LABEL org.opencontainers.image.authors="b.dukai@tudelft.nl"
LABEL maintainer.email="b.dukai@tudelft.nl" maintainer.name="Balázs Dukai"
LABEL description="cjio, or CityJSON/io"

RUN useradd -u 1001 -G root -s /bin/bash app && \
    chgrp -R 0 /etc/passwd && \
    chmod -R g=u /etc/passwd && \
    mkdir /app && \
    chgrp -R 0 /app && \
    chmod -R g=u /app

COPY --from=builder /opt/venv /opt/venv

COPY --chown=1001:0 uid_entrypoint.sh /usr/local/bin/
ENV PATH="/opt/venv/bin:$PATH"

RUN mkdir /data && \
     chown 1001 /data && \
     chgrp 0 /data && \
     chmod g=u /data

WORKDIR /data

ENV LANG="C.UTF-8"

USER 1001

ENTRYPOINT ["/usr/local/bin/uid_entrypoint.sh"]

CMD ["cjio"]