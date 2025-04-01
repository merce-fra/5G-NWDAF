# Copyright 2025 Mitsubishi Electric R&D Centre Europe
# Author: Vincent Artur

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)  any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with this program. If not, see https://www.gnu.org/licenses/lgpl-3.0.html

# Use a build argument for the base image
ARG BASE_IMAGE=python:3.12
FROM ${BASE_IMAGE}

# Define build arguments
ARG SERVICE_DIR
ARG SCRIPT_NAME

# Environment variable to control local package installation
ARG USE_LOCAL_PACKAGES

# Check if required arguments are set
RUN echo "SCRIPT_NAME is: $SCRIPT_NAME" && \
    echo "SERVICE_DIR is: $SERVICE_DIR" && \
    if [ -z "$SCRIPT_NAME" ]; then echo "ERROR: SCRIPT_NAME is not set"; exit 1; fi && \
    if [ -z "$SERVICE_DIR" ]; then echo "ERROR: SERVICE_DIR is not set"; exit 1; fi

# Set the working directory
WORKDIR /app

# Copy all service files
COPY ${SERVICE_DIR}/ /app/

COPY ./local_packages /mnt/local_packages/

# Install local packages if needed
RUN if [ "$USE_LOCAL_PACKAGES" = "1" ]; then \
        echo "Copying and installing local packages..." && \
        mkdir -p /mnt/local_packages && \
        pip install --no-cache-dir /mnt/local_packages/*.whl; \
    else \
        echo "Skipping local package installation."; \
    fi


# Install pip packages
ENV PIP_ROOT_USER_ACTION=ignore
RUN pip config set global.trusted-host "pypi.org merce-gitlab.fr-merce.mee.com" && \
    pip --disable-pip-version-check install --no-compile --no-cache-dir --use-feature=fast-deps -r requirements.txt

# Run the service
ENV SCRIPT_NAME=${SCRIPT_NAME}
ENTRYPOINT ["sh", "-c", "exec python -u $SCRIPT_NAME"]