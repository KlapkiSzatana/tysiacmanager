# Maintainer: KlapkiSzatana
pkgname=tysiac-manager
pkgver=0.9.1
pkgrel=1
pkgdesc="Menedżer Gry 1000"
arch=('any')
url="https://github.com/KlapkiSzatana/tysiacmanager"
license=('GPL-3.0')
depends=('python' 'pyside6')
makedepends=('git')

# ZMIANA 1: Źródłem jest teraz archiwum z GitHuba, a nie pliki lokalne!
source=("${url}/archive/refs/tags/v${pkgver}.tar.gz")

sha256sums=('b99889989eadef61fe84c63e2a55208421cf22b8783a750bad0f329aaeea4c46')

package() {
    # ZMIANA 2: Po pobraniu archiwum, pliki są w folderze z nazwą repo i wersją
    cd "tysiacmanager-${pkgver}"

    # 1. Instalacja plików aplikacji
    install -d "${pkgdir}/usr/share/${pkgname}"
    install -m644 tysiac.py "${pkgdir}/usr/share/${pkgname}/tysiac.py"

    install -m644 tysiac.png "${pkgdir}/usr/share/${pkgname}/tysiac.png"

    # 2. Tworzymy skrypt startowy (Wrapper)
    install -d "${pkgdir}/usr/bin"
    cat <<EOF > "${pkgdir}/usr/bin/${pkgname}"
#!/bin/sh
cd /usr/share/${pkgname}
export APP_ID="${pkgname}"
exec /usr/bin/python tysiac.py "\$@"
EOF
    chmod 755 "${pkgdir}/usr/bin/${pkgname}"

    # 3. Generujemy plik .desktop W LOCIE
    install -d "${pkgdir}/usr/share/applications"
    cat <<EOF > "${pkgdir}/usr/share/applications/${pkgname}.desktop"
[Desktop Entry]
Name=Menedżer Gry 1000
Comment=Aplikacja do liczenia punktów w Tysiąca
Exec=${pkgname}
Icon=${pkgname}
Terminal=false
Type=Application
Categories=Game;CardGame;
EOF

    # 4. Instalacja ikony systemowej (żeby .desktop ją widział)
    install -d "${pkgdir}/usr/share/pixmaps"
    install -m644 tysiac.png "${pkgdir}/usr/share/pixmaps/${pkgname}.png"
}
