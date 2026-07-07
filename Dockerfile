FROM postgres:16

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*

CMD ["postgres"]
