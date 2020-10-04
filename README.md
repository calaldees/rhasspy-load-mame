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


mame \
    -window \
    -prescale 0 \
    -rompath "/home/pi/rapidseedbox/MAME 0.224 ROMs (merged)/;/home/pi/rapidseedbox/MAME 0.224 Software List ROMs (merged)/" \
    sms hulk

-gl_glsl_filter 0 \
-scalemode none \