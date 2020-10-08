.PHONY = all clean distclean install uninstall

CC = gcc

prefix=/usr/local
bindir=$(prefix)/bin
datadir=$(prefix)/share
default_prefix=/usr/local

SRCS := $(wildcard Source/*.c)

install_data_dir = $(DESTDIR)$(datadir)/fpms
install_bin_dir = $(DESTDIR)$(bindir)

networkinfo_rel_dir = share/fpms/BakeBit/Software/Python/scripts/networkinfo

binary_name=NanoHatOLED

SERVICE_SUBS = \
	s,[@]bindir[@],$(bindir),g; \
	s,[@]datadir[@],$(datadir),g

OLED_SCRIPT_SUBS = \
	s,[@]bindir[@],$(bindir),g; \
	s,[@]binary_name[@],$(binary_name),g

LDCFLAGS += -lrt -lpthread

all: $(binary_name)

$(binary_name): $(SRCS)
	# $@ = target (NanoHatOLED); $^ = prerequisites (SRCS files)
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ $^ $(LDCFLAGS)

oled-start: oled-start.in
	@echo "Set variables on oled-start script"
	sed -e '$(OLED_SCRIPT_SUBS)' $< > $@
	chmod +x $@

fpms.service: fpms.service.in
	@echo "Set the prefix on fpms.service"
	sed -e '$(SERVICE_SUBS)' $< > $@

install: installdirs $(binary_name) oled-start fpms.service networkinfo-links
	cp -rf $(filter-out debian fpms.service.in $^,$(wildcard *)) $(install_data_dir)
	install oled-start $(install_bin_dir)
	install $(binary_name) $(install_bin_dir)
	install -m 644 fpms.service $(DESTDIR)/lib/systemd/system

installdirs:
	mkdir -p $(install_bin_dir) \
		$(install_data_dir) \
		$(DESTDIR)/lib/systemd/system

networkinfo-links:
	ln -fs ../$(networkinfo_rel_dir)/reachability.sh $(install_bin_dir)/reachability
	ln -fs ../$(networkinfo_rel_dir)/publicip.sh $(install_bin_dir)/publicip
	ln -fs ../$(networkinfo_rel_dir)/watchinternet.sh $(install_bin_dir)/watchinternet
	ln -fs ../$(networkinfo_rel_dir)/telegrambot.sh $(install_bin_dir)/telegrambot
	ln -fs ../$(networkinfo_rel_dir)/ipconfig.sh $(install_bin_dir)/ipconfig
	ln -fs ../$(networkinfo_rel_dir)/portblinker.sh $(install_bin_dir)/portblinker

clean:
	-rm -f $(binary_name)
	-rm -f oled-start
	-rm -f fpms.service

distclean: clean

uninstall:
	-rm -rf $(install_data_dir) \
		$(install_bin_dir)/oled-start \
		$(DESTDIR)/lib/systemd/system \
		$(bindir)/reachability \
		$(bindir)/publicip \
		$(bindir)/watchinternet \
		$(bindir)/telegrambot \
		$(bindir)/ipconfig \
		$(bindir)/portblinker
