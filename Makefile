.PHONY = all clean distclean install uninstall

CC = gcc
prefix=/usr/local
default_prefix=/usr/local
SRCS := $(wildcard Source/*.c)

install_data_dir = $(DESTDIR)$(datadir)/fpms
install_bin_dir = $(DESTDIR)$(bindir)

LDCFLAGS += -lrt -lpthread

all: NanoHatOLED oled-start

NanoHatOLED: $(SRCS)
	# $@ = target (NanoHatOLED); $^ = prerequisites (SRCS files)
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ $^ $(LDCFLAGS)

oled-start: NanoHatOLED
	@echo "Create oled-start script"
	$(file > $@,#!/bin/sh)
	$(file >> $@,$(install_bin_dir)/$<)
	chmod +x $@

install: NanoHatOLED oled-start
	cp -rf $(filter-out debian fpms.service fpms.service.template $^,$(wildcard *)) $(install_data_dir)
	install oled-start $(install_bin_dir)/oled-start
	# Correct the prefix on fpms.service ExecStart
	sed "s#$(default_prefix)#$(prefix)#g" fpms.service.template > fpms.service
	install fpms.service $(DESTDIR)/lib/systemd/system

installdirs:
	mkdir -p $(install_bin_dir) \
		$(install_data_dir) \
		$(install_bin_dir)/oled-start \
		$(DESTDIR)/lib/systemd/system

clean:
	-rm -f NanoHatOLED
	-rm -f oled-start
	-rm -f fpms.service

distclean: clean

uninstall:
	-rm -rf $(install_data_dir) \
		$(install_bin_dir)/oled-start \
		$(DESTDIR)/lib/systemd/system
