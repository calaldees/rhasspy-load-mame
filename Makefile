DOCKER_IMAGE:=mame_voice

help:
	# help

rhasspy_example:  # https://rhasspy.readthedocs.io/en/latest/installation/#docker
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
	pytest --doctest-modules -p no:cacheprovider \
		parse_mame_xml_names.py

shell:
	docker run --rm -it --entrypoint /bin/bash ${DOCKER_IMAGE}

search:
	#docker run --rm --workdir /_profiles/en/slots/mame/ --entrypoint /bin/grep ${DOCKER_IMAGE} -r "golden"
	docker exec \
		--workdir /_profiles/en/slots/mame/ \
		 rhasspy \
		 grep -r \
		 golden

run:
	docker run --rm \
		--name rhasspy \
		-p 12101:12101 \
		-v "/etc/localtime:/etc/localtime:ro" \
		-v "rhasspy_profiles:/profiles" \
		--device /dev/snd:/dev/snd \
		${DOCKER_IMAGE} \
			
		#
		#--name rhasspy \
		# 		--restart unless-stopped \
		#--entrypoint /bin/sh \
		#-it \