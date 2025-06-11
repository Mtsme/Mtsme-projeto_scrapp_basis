FROM asciidoctor/docker-asciidoctor

ARG D2_VERSION=0.6.4

RUN set -x && \
    apk add --no-cache curl tar gzip && \
    curl -fL "https://github.com/terrastruct/d2/releases/download/v${D2_VERSION}/d2-v${D2_VERSION}-linux-amd64.tar.gz" -o d2.tar.gz && \
    tar -xzf d2.tar.gz && \
    mv d2-v${D2_VERSION}/bin/d2 /usr/local/bin/d2 && \
    chmod +x /usr/local/bin/d2 && \
    rm -rf d2.tar.gz d2-v${D2_VERSION}

RUN d2 --version
