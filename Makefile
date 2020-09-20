DOCKER_IMAGE:=mame_voice

help:
	# help

build:
	docker build \
		--tag ${DOCKER_IMAGE} \
		--build-arg MAME_GIT_TAG=mame0222 \
	.

test:
	pytest --doctest-modules -p no:cacheprovider

shell:
	docker run --rm -it ${DOCKER_IMAGE} /bin/sh
