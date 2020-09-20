# rhasspy-load-mame
Tools to use local voice recognition to launch mame emulation

[rhasspy readthedocs](https://rhasspy.readthedocs.io/en/latest/)

```bash
    docker run \
        -p 12101:12101 \
        --name rhasspy \
        --restart unless-stopped \
        -v "$HOME/.config/rhasspy/profiles:/profiles" \
        -v "/etc/localtime:/etc/localtime:ro" \
        --device /dev/snd:/dev/snd \
        rhasspy/rhasspy \
        --user-profiles /profiles \
        --profile en
```
