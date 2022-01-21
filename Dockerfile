FROM ubuntu:20.04
LABEL org.opencontainers.image.authors="b.dukai@tudelft.nl"
LABEL maintainer.email="b.dukai@tudelft.nl" maintainer.name="Balázs Dukai"
LABEL description="cjio, or CityJSON/io"

RUN useradd -u 1001 -G root -s /bin/bash app && \
    chgrp -R 0 /etc/passwd && \
    chmod -R g=u /etc/passwd && \
    mkdir /app && \
    chgrp -R 0 /app && \
    chmod -R g=u /app

RUN echo 'deb http://archive.ubuntu.com/ubuntu focal universe' >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y \
        gcc \
        g++ \
        libgeos-3.8.0 \
        libproj15 \
        python3 \
        python3-pip

ARG PIP_VERSION="pip==21.3.1"
ARG SETUPTOOL_VERSION="setuptools==60.5.0"
COPY setup.py setup.cfg README.rst LICENSE CHANGELOG.md /app/
COPY cjio /app/cjio
RUN cd /app && \
    python3 -m pip install ${PIP_VERSION} ${SETUPTOOL_VERSION} && \
    pip install .[export,validate,reproject] && \
    rm -rf /tmp/* && \
    rm -rf /user/local/man && \
    cjio --version

COPY --chown=1001:0 uid_entrypoint.sh /usr/local/bin/

RUN mkdir /data && \
     chown 1001 /data && \
     chgrp 0 /data && \
     chmod g=u /data

WORKDIR /data

ENV LANG="C.UTF-8"

USER 1001

ENTRYPOINT ["/usr/local/bin/uid_entrypoint.sh"]

CMD ["/bin/bash"]

