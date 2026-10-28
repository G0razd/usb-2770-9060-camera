#!/usr/bin/env bash
set -euo pipefail

LIBGPHOTO2_COMMIT=02d92fea8a269eb94330a4eade204ba799433606
GPHOTO2_COMMIT=70e83ed3fd630c656e7859f2a510b70bc20b50b8
PREFIX=${PREFIX:-/opt/gphoto2-sq9060}
REPO_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
WORK_DIR=$(mktemp -d)

if [ "$(id -u)" -ne 0 ]; then
	echo "Run this as root: sudo $0" >&2
	exit 1
fi

run() {
	local step=$1
	shift
	echo "==> $step"
	"$@" >"$WORK_DIR/$step.log" 2>&1 &
	if ! wait $!; then
		tail -40 "$WORK_DIR/$step.log" >&2
		echo "Step '$step' failed. Full log: $WORK_DIR/$step.log" >&2
		exit 1
	fi
}

fetch() {
	git init -q "$3"
	git -C "$3" fetch -q --depth 1 "$1" "$2"
	git -C "$3" checkout -q FETCH_HEAD
}

install_packages() {
	export DEBIAN_FRONTEND=noninteractive
	apt-get update -qq
	apt-get install -y -qq git build-essential autoconf automake autopoint gettext libtool \
		pkg-config libusb-1.0-0-dev libltdl-dev libexif-dev libjpeg-dev libpopt-dev \
		libreadline-dev netpbm usbutils
}

build_libgphoto2() {
	fetch https://github.com/gphoto/libgphoto2.git "$LIBGPHOTO2_COMMIT" "$WORK_DIR/libgphoto2"
	cd "$WORK_DIR/libgphoto2"
	git apply "$REPO_DIR/patches/libgphoto2-sq9060.patch"
	autoreconf -is
	./configure --prefix="$PREFIX" --with-camlibs=digigr8 --disable-docs \
		--without-libxml-2.0 --without-gdlib --without-libcurl
	make -j"$(nproc)"
	make install
}

build_gphoto2() {
	fetch https://github.com/gphoto/gphoto2.git "$GPHOTO2_COMMIT" "$WORK_DIR/gphoto2"
	cd "$WORK_DIR/gphoto2"
	autoreconf -is
	PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig" LDFLAGS="-Wl,-rpath,$PREFIX/lib" \
		./configure --prefix="$PREFIX"
	make -j"$(nproc)"
	make install
}

install_tools() {
	install -m 755 "$REPO_DIR/linux/sq9060-pull" "$PREFIX/bin/sq9060-pull"
	ln -sf "$PREFIX/bin/sq9060-pull" /usr/local/bin/sq9060-pull
	if [ -d /etc/udev/rules.d ]; then
		install -m 644 "$REPO_DIR/linux/60-sq9060-camera.rules" /etc/udev/rules.d/60-sq9060-camera.rules
		udevadm control --reload-rules 2>/dev/null || true
	fi
}

run packages install_packages
run libgphoto2 build_libgphoto2
run gphoto2 build_gphoto2
run tools install_tools
rm -rf "$WORK_DIR"

echo "Installed to $PREFIX. Plug the camera in and run: sq9060-pull"
