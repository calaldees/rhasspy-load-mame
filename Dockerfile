FROM python:alpine as base

ARG WORKDIR=/romcheck
ENV WORKDIR=${WORKDIR}
RUN mkdir -p ${WORKDIR}
WORKDIR ${WORKDIR}
ENV PYTHONPATH=.

FROM base as romdata_xml
    RUN apk add \
        curl \
        subversion \
        zip \
    && true
    ARG MAME_GIT_TAG
    ENV MAME_GIT_TAG=${MAME_GIT_TAG}
    RUN [ ! -z "${MAME_GIT_TAG}" ]
    RUN curl -L "https://github.com/mamedev/mame/releases/download/${MAME_GIT_TAG}/${MAME_GIT_TAG}lx.zip" -o mamelx.zip
    # `svn export` reference - https://stackoverflow.com/a/18324458/3356840
    RUN \
        svn export https://github.com/mamedev/mame.git/tags/${MAME_GIT_TAG}/hash &&\
        zip hash.zip -r hash/ &&\
        rm -rf hash/ &&\
    true

FROM romdata_xml as romdata_data
    COPY --from=code ${WORKDIR}/_common/roms.py ./_common/roms.py
    COPY --from=code ${WORKDIR}/romdata/parse_mame_xml.py ./romdata/parse_mame_xml.py
    # replace `>` with `| tee` to see output
    #  `&& zip roms.zip roms.txt` no real need for this - most of it is hash's which don't compress 29MB -> 12MB
    RUN set -o pipefail && \
        python3 -m romdata.parse_mame_xml > roms.txt
