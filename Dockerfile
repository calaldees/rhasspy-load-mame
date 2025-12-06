FROM python:alpine AS base

ARG WORKDIR=/romdata
ENV WORKDIR=${WORKDIR}
RUN mkdir -p ${WORKDIR}
WORKDIR ${WORKDIR}
ENV PYTHONPATH=.

FROM base AS code
    COPY ./*.py ./

FROM base AS base_test
    RUN pip3 install pytest
FROM base_test AS test
    COPY --from=code ${WORKDIR} ./
    RUN pytest --doctest-modules -p no:cacheprovider \
        parse_mame_xml_names.py

FROM base AS romdata_xml
    RUN apk add \
        curl \
        git \
        zip \
    && true
    ARG MAME_GIT_TAG
    ENV MAME_GIT_TAG=${MAME_GIT_TAG}
    RUN [ ! -z "${MAME_GIT_TAG}" ]
    RUN curl -L "https://github.com/mamedev/mame/releases/download/${MAME_GIT_TAG}/${MAME_GIT_TAG}lx.zip" -o mamelx.zip
    # GitHub dropped support for SNV in 2024
    # `svn export` reference - https://stackoverflow.com/a/18324458/3356840
    #RUN \
    #    svn export https://github.com/mamedev/mame.git/tags/${MAME_GIT_TAG}/hash &&\
    #    zip hash.zip -r hash/ &&\
    #    rm -rf hash/ &&\
    #true
    RUN git clone --filter=blob:none --no-checkout https://github.com/mamedev/mame.git &&\
        cd mame &&\
        git sparse-checkout init --cone &&\
        git sparse-checkout set hash &&\
        git checkout ${MAME_GIT_TAG} &&\
        zip hash.zip -r hash/ &&\
        cd .. && \
        mv ./mame/hash.zip ./ &&\
        rm -rf mame/ &&\
    true

FROM romdata_xml AS romdata_data
    COPY --from=code ${WORKDIR} ./
    # replace `>` with `| tee` to see output
    #  `&& zip roms.zip roms.txt` no real need for this - most of it is hash's which don't compress 29MB -> 12MB
    RUN set -o pipefail && \
        python3 -m parse_mame_xml_names
        # > mame.txt

#FROM base as romdata_output
#    COPY --from=romdata_data ${WORKDIR}/slots/mame ./

FROM rhasspy/rhasspy AS rhasspy
    COPY ./rhasspy/profiles/en/ /profiles/en/
    COPY --from=romdata_data /romdata/slots/mame /_profiles/en/slots/mame
    RUN ln -s /_profiles/en/slots/mame /profiles/en/slots/
    CMD ["--user-profiles", "/profiles", "--profile", "en"]
