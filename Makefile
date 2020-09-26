DOCKER_IMAGE:=mame_voice

help:
	# help

rhasspy:
	docker run \
		-p 12101:12101 \
		--name rhasspy \
		--restart unless-stopped \
		-v "${HOME}/.config/rhasspy/profiles:/profiles" \
		-v "/etc/localtime:/etc/localtime:ro" \
		--device /dev/snd:/dev/snd \
		rhasspy/rhasspy \
		--user-profiles /profiles \
		--profile en

build:
	docker build \
		--tag ${DOCKER_IMAGE} \
		--build-arg MAME_GIT_TAG=mame0222 \
	.

test:
	pytest --doctest-modules -p no:cacheprovider

shell:
	docker run --rm -it ${DOCKER_IMAGE} /bin/sh
