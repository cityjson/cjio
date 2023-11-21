FROM python:3.8.12-slim-bullseye AS builder

RUN useradd -u 1001 -G root app && \
    chgrp -R 0 /etc/passwd && \
    chmod -R g=u /etc/passwd && \
    mkdir /app && \
    chgrp -R 0 /app && \
    chmod -R g=u /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        gcc

ARG PIP_VERSION="pip==22.3.0"
ARG SETUPTOOL_VERSION="setuptools==65.5.0"
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN python3 -m pip install ${PIP_VERSION} ${SETUPTOOL_VERSION}

# --- cjvalpy build from source because https://github.com/cityjson/cjio/issues/146
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"
RUN pip install maturin

ARG CJVALPY_VERSION="0.4.1"
RUN curl -L -o cjvalpy.tar.gz https://github.com/cityjson/cjvalpy/archive/refs/tags/${CJVALPY_VERSION}.tar.gz && \
    tar -xvf cjvalpy.tar.gz && \
    cd cjvalpy-${CJVALPY_VERSION} && \
    maturin build --release && \
    cd ./target/wheels/
ARG WHEEL="cjvalpy-${CJVALPY_VERSION}/target/wheels/*.whl"
RUN pip install ${WHEEL} && \
    pip uninstall -y maturin
# ---

COPY setup.py setup.cfg README.rst LICENSE CHANGELOG.md /app/
COPY cjio /app/cjio
RUN cd /app && \
    pip install .[export,validate,reproject] && \
    rm -rf /tmp/* && \
    rm -rf /user/local/man && \
    cjio --version

FROM python:3.8.12-slim AS cjio
LABEL org.opencontainers.image.authors="Balázs Dukai <balazs.dukai@3dgi.nl>"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.url="https://github.com/cityjson/cjio"
LABEL org.opencontainers.image.description="Python CLI to process and manipulate CityJSON files. The different operators can be chained to perform several processing operations in one step, the CityJSON model goes through them and different versions of the CityJSON model can be saved as files along the pipeline."
LABEL org.opencontainers.image.title="cjio"

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