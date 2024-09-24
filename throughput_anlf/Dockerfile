FROM python:3.12

# Define build arguments for the Gitlab token and the certificates
ARG GITLAB_TOKEN_NAME
ARG GITLAB_TOKEN_VALUE

# Check if arguments are set
RUN if [ -z "$GITLAB_TOKEN_NAME" ]; then echo "ERROR: GITLAB_TOKEN_NAME is not set"; exit 1; fi
RUN if [ -z "$GITLAB_TOKEN_VALUE" ]; then echo "ERROR: GITLAB_TOKEN_VALUE is not set"; exit 1; fi

# Install necessary tools
RUN apt-get update && apt-get install -y \
    ca-certificates


# Add custom certificate
COPY ./certificates/merce-gitlab-fr-merce-mee-com-chain.crt /usr/local/share/ca-certificates/merce-gitlab-fr-merce-mee-com-chain.crt
RUN update-ca-certificates
RUN export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Configure pip to use the token
RUN mkdir -p /root/.pip && \
    echo "[global]" > /root/.pip/pip.conf && \
    echo "extra-index-url = https://$GITLAB_TOKEN_NAME:$GITLAB_TOKEN_VALUE@merce-gitlab.fr-merce.mee.com/gitlab/api/v4/projects/248/packages/pypi/simple" >> /root/.pip/pip.conf

# Copy requirements file
COPY requirements.txt .

# Install pip packages
ENV PIP_ROOT_USER_ACTION=ignore
RUN pip config set global.trusted-host "pypi.org merce-gitlab.fr-merce.mee.com"
RUN pip install --upgrade pip
RUN pip install -U --no-cache-dir -r requirements.txt

# Set the working directory
WORKDIR /app

# Copy application files
COPY *.py ./

# Copy models
RUN mkdir models
COPY models/* ./models/

ENTRYPOINT ["python", "-u", "main.py"]