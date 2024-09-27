# Use a build argument for the base image
ARG BASE_IMAGE=python:3.11
FROM ${BASE_IMAGE}

# Define build arguments for the GitLab token and other configurations
ARG GITLAB_TOKEN_NAME
ARG GITLAB_TOKEN_VALUE
ARG SERVICE_DIR
ARG SCRIPT_NAME

# Check if required arguments are set
RUN if [ -z "${SCRIPT_NAME}" ]; then echo "ERROR: SCRIPT_NAME is not set"; exit 1; fi && \
    if [ -z "${SERVICE_DIR}" ]; then echo "ERROR: SERVICE_DIR is not set"; exit 1; fi && \
    if [ -z "${GITLAB_TOKEN_NAME}" ]; then echo "ERROR: GITLAB_TOKEN_NAME is not set"; exit 1; fi && \
    if [ -z "${GITLAB_TOKEN_VALUE}" ]; then echo "ERROR: GITLAB_TOKEN_VALUE is not set"; exit 1; fi

# Install necessary tools
ARG CACHEBUST=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Add custom certificate
COPY ./certificates/merce-gitlab-fr-merce-mee-com-chain.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates

# Configure pip to use the token
RUN mkdir -p /root/.pip && \
    echo "[global]" > /root/.pip/pip.conf && \
    echo "extra-index-url = https://${GITLAB_TOKEN_NAME}:${GITLAB_TOKEN_VALUE}@merce-gitlab.fr-merce.mee.com/gitlab/api/v4/projects/248/packages/pypi/simple" >> /root/.pip/pip.conf

# Set the working directory
WORKDIR /app

# Copy all service files
COPY ${SERVICE_DIR}/ /app/

# Install pip packages
ENV PIP_ROOT_USER_ACTION=ignore
RUN pip config set global.trusted-host "pypi.org merce-gitlab.fr-merce.mee.com" && \
    pip install --upgrade pip && \
    pip install --no-cache-dir --use-feature=fast-deps -r requirements.txt

# Run the service
ENV SCRIPT_NAME=${SCRIPT_NAME}
ENTRYPOINT ["sh", "-c", "python -u $SCRIPT_NAME"]