FROM python:3.12

# Define build arguments for the Gitlab token and the certificates
ARG GITLAB_TOKEN_NAME
ARG GITLAB_TOKEN_VALUE

# Check if arguments are set
RUN if [ -z "$GITLAB_TOKEN_NAME" ]; then echo "ERROR: GITLAB_TOKEN_NAME is not set"; exit 1; fi \
 && if [ -z "$GITLAB_TOKEN_VALUE" ]; then echo "ERROR: GITLAB_TOKEN_VALUE is not set"; exit 1; fi

# Install necessary tools and update certificates
RUN apt-get update && apt-get install -y ca-certificates && \
    update-ca-certificates

# Add custom certificate
COPY ./certificates/merce-gitlab-fr-merce-mee-com-chain.crt /usr/local/share/ca-certificates/merce-gitlab-fr-merce-mee-com-chain.crt
RUN update-ca-certificates

# Set environment variables
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Configure pip to use the token
RUN mkdir -p /root/.pip && \
    pip config set global.extra-index-url "https://${GITLAB_TOKEN_NAME}:${GITLAB_TOKEN_VALUE}@merce-gitlab.fr-merce.mee.com/gitlab/api/v4/projects/248/packages/pypi/simple" && \
    pip config set global.trusted-host "pypi.org merce-gitlab.fr-merce.mee.com"

# Copy requirements and install pip packages
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -U --no-cache-dir -r requirements.txt

# Set working directory
WORKDIR /app

# Copy application files
COPY *.py .

# Set entrypoint
ENTRYPOINT ["python", "-u", "gmlc.py"]