# Throughput _MTLF_

## Overview

This service is a _Model Training Logical Function_ (_MTLF_) that provides _ML_ models to *AnLF*s serving
`UE_LOC_THROUGHPUT` analytics.

It is based on the mechanics offered by the `MtlfService` class from the
_[nwdaf-libcommon](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/nwdaf-libcommon)_ library.

## Requirements

* _Python_ ≥ 3.12 (preferably in a _virtualenv_, or using [Conda](https://anaconda.org/anaconda/conda))
* [nwdaf-api](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/nwdaf-3gpp-apis)
* [nwdaf-libcommon](https://merce-gitlab.fr-merce.mee.com/gitlab/artur/nwdaf-libcommon)
* [FastAPI](https://github.com/fastapi/fastapi)

## TODO

* Ground truth data collection 
* Model training