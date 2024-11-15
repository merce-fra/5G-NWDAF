# NWDAF API Gateway

This is an _API Gateway_ service written in _Python_, that fits within a _Kafka_-based _NWDAF_
microservices architecture.

## Table of Contents

- [Pre-requisites](#pre-requisites)
- [Clone](#clone)
- [Run locally](#run-locally)
- [Run in a _Docker_ container](#run-in-a-_docker_-container)
    - [Build](#build)
    - [Run](#run)

## Pre-requisites

To build this project, these pre-requisites are needed:

* _Python_ ≥ 3.12 (preferably in a _virtualenv_, or using [Conda](https://anaconda.org/anaconda/conda))
* _pip_ (_Python_ package installer)
* _Docker_ (for containerized setup)

This tutorial has been tested with _[WSL](https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux)_, and assumes the
user has some basic knowledge of _Linux_ command line interface and _Python_ development.

## Clone

In order to clone the current repository on your local environment, run the following command:

```bash
git clone git@merce-gitlab.fr-merce.mee.com:artur/nwdaf-api-gateway.git
```

For this clone operation to succeed, you should have already set up an _SSH_ key for authentication on your _Gitlab_
profile and made sure the right _SSH_ configuration is present on your local
environment. [This tutorial](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/gitlab-ssh-config/-/blob/main/README.md)
explains how to do it.

You can then navigate to the freshly cloned repository to access the codebase:

```bash
cd ./nwdaf-api-gateway
```

## Run locally

To run the service locally, you first need to install the _pip_ pre-requisites. If you haven't set up your system for
pulling from the _MERCE Package Registry_, please
follow [this tutorial](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/python-packages/-/blob/master/README.md).

To install the pre-requisites in your _virtualenv_, run the following command:

```bash
pip install -r requirements.txt
```

You should now be able to run the service locally with:

```bash
python main.py
```

## Run in a _Docker_ container

To be able to build the _Docker_ image of the service, you should already have a _Gitlab_ token for pulling packages
from the _MERCE Package Registry_, please
follow [this tutorial](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/python-packages/-/blob/master/README.md) if
you don't have one yet.

### Build

To build the image, run the following command:

```bash
docker build --build-arg GITLAB_TOKEN_NAME=<my_token_name> --build-arg GITLAB_TOKEN_VALUE=<my_token_value> -t api-gateway .
```

The values of _<my_token_name>_ and _<my_token_value>_ should be replaced by your own token values.

### Run

Once the image is built, you can run it with:

```bash
docker run api-gateway
```

By default, the web service will run on port `5000`.




