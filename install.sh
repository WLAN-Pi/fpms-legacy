#!/bin/bash

if [ $(id -u) -ne 0 ]; then
  printf "Script must be run as root. Try 'sudo ./install.sh'\n"
  exit 1
fi

gcc Source/daemonize.c Source/main.c -lrt -lpthread -o NanoHatOLED

if [ ! -f $DESTDIR/usr/local/bin/oled-start ]; then
    cat >$DESTDIR/usr/local/bin/oled-start <<EOL
#!/bin/sh
cd $PWD
./NanoHatOLED
EOL

    cp fpms.service $DESTDIR/lib/systemd/system
    chmod 755 $DESTDIR/usr/local/bin/oled-start
fi

