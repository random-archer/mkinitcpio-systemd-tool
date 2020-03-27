PREFIX ?= /usr/local
SYSTEMD_SYSTEM_PATH ?= /usr/lib

install:
	install -vDm 644 src/fstab -t $(DESTDIR)/etc/mkinitcpio-systemd-tool/config
	install -vDm 644 src/crypttab -t $(DESTDIR)/etc/mkinitcpio-systemd-tool/config
	install -vDm 644 src/initrd-network.network -t $(DESTDIR)/etc/mkinitcpio-systemd-tool/network/
	install -vDm 755 src/mkinitcpio-hook.sh $(DESTDIR)$(PREFIX)/lib/initcpio/hooks/systemd-tool
	install -vDm 755 src/mkinitcpio-install.sh $(DESTDIR)$(PREFIX)/lib/initcpio/install/systemd-tool
	install -vDm 755 src/initrd-build.sh -t $(DESTDIR)$(PREFIX)/lib/mkinitcpio-systemd-tool
	install -vDm 755 src/initrd-shell.sh -t $(DESTDIR)$(PREFIX)/lib/mkinitcpio-systemd-tool
	install -vDm 644 src/*.{path,service} -t $(DESTDIR)$(SYSTEMD_SYSTEM_PATH)/systemd/system
	install -vDm 644 LICENSE.md -t $(DESTDIR)$(PREFIX)/share/licenses/mkinitcpio-systemd-tool
	install -vDm 644 README.md -t $(DESTDIR)$(PREFIX)/share/doc/mkinitcpio-systemd-tool
