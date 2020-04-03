#
# manual build: cd $repo ; makepkg -e ;
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
            'tinyssh: for initrd-tinysshd.service'
            'tinyssh-convert: for initrd-tinysshd.service'
            'mc: for initrd-debug-progs.service')
conflicts=('mkinitcpio-dropbear' 'mkinitcpio-tinyssh')
backup=("etc/${pkgname}/config/crypttab"
        "etc/${pkgname}/config/fstab"
        "etc/${pkgname}/network/initrd-network.network" )
#source=("$pkgname-$pkgver.tar.gz::https://github.com/random-archer/${pkgname}/archive/v${pkgver}.tar.gz")
#install="${pkgname}.install"
#sha512sums=()

package() {
  cd ..
  make DESTDIR="$pkgdir/" PREFIX='/usr' install
}