FROM postgres:11

RUN apt-get update \
 && apt-get install -y \
    build-essential \
    git \
    libcurl4-openssl-dev \
    postgresql-server-dev-11 \
    zlib1g-dev

#COPY docker-entrypoint.sh /usr/local/bin/
#RUN ln -s /usr/local/bin/docker-entrypoint.sh / # backwards compat
#ENTRYPOINT ["docker-entrypoint.sh"]
#CMD ["postgres"]