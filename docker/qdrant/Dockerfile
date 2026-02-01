# Extend official Qdrant image with curl for healthchecks.
# The base image intentionally excludes curl/wget for security;
# we add curl only for the Docker healthcheck.
FROM qdrant/qdrant:latest
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
# Restore default user (base image uses root when USER_ID=0)
USER 0
