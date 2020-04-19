#
# Developer support: allow local install
#
# note: keep in sync with package maintainer origin:
# https://git.archlinux.org/svntogit/community.git/tree/trunk/PKGBUILD?h=packages/mkinitcpio-systemd-tool
#
# manual package build and install steps:
# * cd "$this_repo"
# * rm -r -f  pkg/ *.pkg.tar.xz
# * makepkg -e
# * sudo pacman -U *.pkg.tar.xz
#

pkgname=mkinitcpio-systemd-tool
pkgver=build
pkgrel=$(date +%s)
pkgdesc="Provisioning tool for systemd in initramfs (systemd-tool)"
arch=('any')
url="https://github.com/random-archer/mkinitcpio-systemd-tool"
license=('Apache')
depends=('mkinitcpio' 'systemd')
optdepends=('cryptsetup: for initrd-cryptsetup.service'
            'dropbear: for initrd-dropbear.service'
            'busybox: for initrd-tinysshd.service'
            'mc: for initrd-debug-progs.service'
            'nftables: for initrd-nftables.service'
            'tinyssh: for initrd-tinysshd.service'
            'tinyssh-convert: for initrd-tinysshd.service')
conflicts=('mkinitcpio-dropbear' 'mkinitcpio-tinyssh')
backup=("etc/${pkgname}/config/crypttab"
        "etc/${pkgname}/config/fstab"
        "etc/${pkgname}/config/initrd-nftables.conf"
        "etc/${pkgname}/config/initrd-util-usb-hcd.conf"
        "etc/${pkgname}/network/initrd-network.network" )
#source=("$pkgname-$pkgver.tar.gz::https://github.com/random-archer/${pkgname}/archive/v${pkgver}.tar.gz")
#install="${pkgname}.install"
#sha512sums=()

package() {
  cd ..
  make DESTDIR="$pkgdir/" PREFIX='/usr' install
}
