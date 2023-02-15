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

## Install rhasspy-load-mame
```
pacman -Sy git
pacman -Sy make

mkdir -p ~/code/
cd ~/code/
git clone https://github.com/calaldees/rhasspy-load-mame.git
cd rhasspy-load-mame
make build
make start_service
# go to localhost:12101 or `ip address :12101` and download 100mb of packages + restart
# maybe set sound capture device `arecord` and sound output device

pacman -Sy python-pip
pip install websockets
make websocket

make install_lxde_startup
```


mame \
    -window \
    -prescale 0 \
    -rompath "/home/pi/rapidseedbox/MAME 0.224 ROMs (merged)/;/home/pi/rapidseedbox/MAME 0.224 Software List ROMs (merged)/" \
    sms hulk

-gl_glsl_filter 0 \
-scalemode none \


[mame.spludlow](https://mame.spludlow.co.uk/) - web accessible mame lists
