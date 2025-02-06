# Throughput _MTLF_

## Overview

This service is a _Model Training Logical Function_ (_MTLF_) that provides _ML_ models to *AnLF*s serving
`UE_LOC_THROUGHPUT` analytics.

It is based on the mechanics offered by the `MtlfService` class from the
_[nwdaf-libcommon](https://github.com/merce-fra/NWDAF-Common-Library)_ library.

## Requirements

* _Python_ ≥ 3.12 (preferably in a _virtualenv_, or using [Conda](https://anaconda.org/anaconda/conda))
* [nwdaf-api](https://github.com/merce-fra/NWDAF-3GPP-APIs)
* [nwdaf-libcommon](https://github.com/merce-fra/NWDAF-Common-Library)
* [FastAPI](https://github.com/fastapi/fastapi)

## TODO

* Ground truth data collection 
* Model training