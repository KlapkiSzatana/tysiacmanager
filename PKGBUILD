# Maintainer: KlapkiSzatana
pkgname=tysiac-manager
pkgver=0.9.1
pkgrel=1
pkgdesc="Menedżer Gry 1000"
arch=('any')
url="https://github.com/KlapkiSzatana/tysiacmanager"
license=('GPL-3.0')
depends=('python' 'pyside6') # Wymagamy tylko Pythona i biblioteki GUI
makedepends=('git') # Nic specjalnego do budowania nie jest potrzebne
source=("local://tysiac.py"
        "local://tysiac.png"
        "tysiac.desktop")
sha256sums=('SKIP' 'SKIP' 'SKIP')

package() {
    # 1. Tworzymy katalog dla aplikacji w /usr/share/tysiac-manager
    install -d "${pkgdir}/usr/share/${pkgname}"
    install -m644 tysiac.py "${pkgdir}/usr/share/${pkgname}/tysiac.py"
    install -m644 tysiac.png "${pkgdir}/usr/share/${pkgname}/tysiac.png"

    # 2. Tworzymy skrypt startowy (tzw. wrapper) w /usr/bin
    install -d "${pkgdir}/usr/bin"

    cat <<EOF > "${pkgdir}/usr/bin/${pkgname}"
#!/bin/sh
# Przechodzimy do katalogu, żeby działały ikony (QIcon)
cd /usr/share/${pkgname}

# Ustawiamy zmienną APP_ID na nazwę pakietu (dynamicznie!)
export APP_ID="${pkgname}"

# Uruchamiamy grę
exec /usr/bin/python tysiac.py "\$@"
EOF

    # Nadajemy uprawnienia wykonywania dla wrappera
    chmod 755 "${pkgdir}/usr/bin/${pkgname}"

    # 3. Instalacja pliku .desktop i ikony
    install -Dm644 "tysiac.desktop" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
    install -Dm644 "tysiac.png" "${pkgdir}/usr/share/pixmaps/${pkgname}.png"

}
