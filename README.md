# 5G NWDAF

This is the central repository for the microservices _NWDAF_. It is based on the _submodules_ mechanisms provided by
_git_.

## Description

The repository is composed of several submodules:

| Submodule     | Description                                            | Directory       | Git URL                                                                                                                               |
|---------------|--------------------------------------------------------|-----------------|---------------------------------------------------------------------------------------------------------------------------------------|
| *API Gateway* | _API Gateway_ service for *NWDAF*, written in _Python_ | `./api-gateway` | [git@merce-gitlab.fr-merce.mee.com:artur/nwdaf-api-gateway.git](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/nwdaf-api-gateway) |
| *AnLF*        | *AnLF* service for *NWDAF*, written in *Python*        | `./anlf`        | [git@merce-gitlab.fr-merce.mee.com:artur/nwdaf-anlf.git](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/nwdaf-anlf)               |

The _API Gateway_ and _AnLF_ services are built into their own _Docker_ containers, and then orchestrated with _Docker
Compose_.

## Pre-requisites

In order to deploy the microservices, the following tools are required:

* _Docker_ (see [installation doc](https://docs.docker.com/engine/install/ubuntu/))
* _Docker Compose_ (see [installation doc](https://docs.docker.com/compose/install/linux/))

## Clone

In order to clone the current repository and its submodules on your local environment, run the following commands:

```bash
git clone git@merce-gitlab.fr-merce.mee.com:artur/5g-nwdaf.git
cd ./5g-nwdaf
git submodule update --init --recursive
```

For this clone operation to succeed, you should have already set up an _SSH_ key for authentication on your _Gitlab_
profile and made sure the right _SSH_ configuration is present on your local
environment. [This tutorial](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/gitlab-ssh-config/-/blob/main/README.md)
explains how to
do it.

You can then navigate to the freshly cloned repository to access the codebase:

```bash
cd ./5g-nwdaf
```

## Configure

A token to access the _MERCE Package Registry_ is required to build and deploy the
microservices. [This tutorial](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/python-packages#create-you-access-token)
explains how to create such a token.

You should then export the following environment variables:

```bash
export GITLAB_TOKEN_NAME=<gitlab_token_name>
export GITLAB_TOKEN_VALUE=<gitlab_token_value>
```

In these commands, _<gitlab_token_name>_ and _<gitlab_token_value>_ should be replaced by the relevant values. You can
also add these exports in your `.bashrc` in order to avoid doing this step for every new session.

## Build

To build the microservices, only one command is needed:

```bash
docker compose build
```

If re-building the containers from scratch is needed, the `--no-cache` option can be passed to the command.

## Deploy

To deploy the _NWDAF_, only one command is needed:

```bash
docker compose up
```
