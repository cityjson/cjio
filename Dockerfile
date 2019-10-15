FROM alpine:3.10

#
# Install proj4
#
ARG PROJ_VERSION=6.2.0
RUN apk --update add sqlite libstdc++ sqlite-libs libgcc && \
    apk --update add --virtual .proj4-deps \
        make \
        gcc \
        g++ \
        file \
        sqlite-dev \
        unzip && \
    cd /tmp && \
    wget http://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz && \
    tar xfvz proj-${PROJ_VERSION}.tar.gz && \
    rm -f proj-${PROJ_VERSION}.tar.gz && \
    wget http://download.osgeo.org/proj/proj-datumgrid-1.8.zip && \
    unzip proj-datumgrid-1.8.zip -d proj-${PROJ_VERSION}/nad/ && \
    rm -f proj-datumgrid-1.8.zip && \
    wget http://download.osgeo.org/proj/proj-datumgrid-europe-1.1.zip && \
    unzip proj-datumgrid-europe-1.1.zip -d proj-${PROJ_VERSION}/nad/ && \
    rm -f proj-datumgrid-europe-1.1.zip && \
    wget http://download.osgeo.org/proj/proj-datumgrid-north-america-1.1.zip && \
    unzip proj-datumgrid-north-america-1.1.zip -d proj-${PROJ_VERSION}/nad/ && \
    rm -f proj-datumgrid-north-america-1.1.zip && \
    wget http://download.osgeo.org/proj/proj-datumgrid-oceania-1.0.zip && \
    unzip proj-datumgrid-oceania-1.0.zip -d proj-${PROJ_VERSION}/nad/ && \
    rm -f proj-datumgrid-oceania-1.0.zip && \
    cd proj-${PROJ_VERSION} && \
    ./configure && \
    make -j 4 && \
    make install && \
    echo "Entering root folder" && \
    cd / &&\
    echo "Cleaning dependencies tmp and manuals" && \
    apk del .proj4-deps && \
    rm -rf /tmp/* && \
    rm -rf /user/local/man && \
    proj

# Install geos
ARG GEOS_VERSION=3.7.1
RUN apk --update add --virtual .geos-deps \
        which \
        make \
        gcc \
        g++ \
        file \
        git \
        autoconf \
        automake \
        libtool && \
    cd /tmp && \
    git clone https://git.osgeo.org/gitea/geos/geos.git geos && \
    cd geos && \
    git checkout ${GEOS_VERSION} && \
    ./autogen.sh && \
    ./configure && \
    make -j 4 && \
    make install && \
    cd ~ && \
    apk del .geos-deps && \
    rm -rf /tmp/* && \
    rm -rf /user/local/man

RUN adduser -u 1001 -G root -s /bin/bash -D app && \
    chgrp -R 0 /etc/passwd && \
    chmod -R g=u /etc/passwd && \
    mkdir /app && \
    chgrp -R 0 /app && \
    chmod -R g=u /app && \
    apk --update add \
        gcc \
        bash \
        make \
        git \
        libc-dev \
        python3

ARG PIP_VERSION="pip==19.2.1"
ARG SETUPTOOL_VERSION="setuptools==41.0.1"
RUN cd /app && \
    apk --update add --virtual .cjio-build-deps \
        musl-dev \
        python3-dev && \
    python3 -m venv .venv --system-site-packages && \
    .venv/bin/pip3 install ${PIP_VERSION} ${SETUPTOOL_VERSION} cjio shapely && \
    apk del .cjio-build-deps && \
    rm -rf /tmp/* && \
    rm -rf /user/local/man && \
    .venv/bin/cjio --help

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

