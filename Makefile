#!make
include .env

DOCKER_IMAGE:=rhasspy-load-mame

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
		--build-arg MAME_GIT_TAG=${MAME_GIT_TAG} \
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

start_service:
	if [ "$$(docker ps | grep rhasspy)" = "" ]; then\
		docker run \
			--detach \
			--rm \
			--name rhasspy \
			-p 12101:12101 \
			-v "/etc/localtime:/etc/localtime:ro" \
			-v "rhasspy_profiles:/profiles" \
			--device /dev/snd:/dev/snd \
			${DOCKER_IMAGE} \
			;\
	fi
		# --restart unless-stopped
stop_service:
	docker stop rhasspy
log:
	docker log rhasspy


install_lxde_startup:
	echo -e "\n@lxterminal -e make --directory $(PWD) websocket" >> $$(find ~/ -iwholename "*/lxsession/*/autostart" 2>/dev/null)

/mnt/MAME/:
	sudo mount /dev/sdb1 /mnt
websocket: start_service /mnt/MAME/
	# Wait for rhasspy port 12101
	# while ! nc -z localhost 12101 ; do sleep 1 ; done  # this dose not work as the port becoms active but dose not function
	# TODO: sleep is a workaround
	sleep 3
	python3 websocket_mame.py || true
