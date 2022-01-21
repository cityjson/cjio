FROM ubuntu:20.04

RUN useradd -u 1001 -G root -s /bin/bash app && \
    chgrp -R 0 /etc/passwd && \
    chmod -R g=u /etc/passwd && \
    mkdir /app && \
    chgrp -R 0 /app && \
    chmod -R g=u /app
RUN apt-get update && \
    apt-get install -y python3

COPY --from=tudelft3d/cjio:latest /usr/local/bin/ /usr/local/bin/
COPY --from=tudelft3d/cjio:latest /usr/local/lib/ /usr/local/lib/

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