export SHELL = sh
PACKAGE = swin
ICON = data/images/swin.ico
REVISION = $(shell bzr revno)
VERSION = $(shell head -n 1 debian/changelog | sed -e "s/^$(PACKAGE) (\(.*\)).*/\1/g")
COPYRIGHTYEAR = 2009
AUTHOR = Agostino Russo
EMAIL = agostino.russo@gmail.com

all: build

build: wubi

wubi: wubi-pre-build
	PYTHONPATH=src tools/pywine -OO src/pypack/pypack --verbose --bytecompile --outputdir=build/setup src/main.py data build/bin build/version.py build/winboot build/translations
	PYTHONPATH=src tools/pywine -OO build/pylauncher/pack.py build/setup
	mv build/application.exe build/swin.exe

wubi-pre-build: check_wine pylauncher winboot2 src/main.py src/wubi/*.py cpuid version.py translations
	rm -rf build/setup
	rm -rf build/bin
	cp -a blobs build/bin
	cp wine/drive_c/windows/system32/python23.dll build/pylauncher #TBD
	cp build/cpuid/cpuid.dll build/bin

translations: po/*.po
	mkdir -p build/translations/
	@for po in $^; do \
		language=`basename $$po`; \
		language=$${language%%.po}; \
		target="build/translations/$$language/LC_MESSAGES"; \
		mkdir -p $$target; \
		msgfmt --output=$$target/$(PACKAGE).mo $$po; \
	done

version.py:
	$(shell echo 'version = "5.0"' > build/version.py)
	$(shell echo 'revision = 0' >> build/version.py)
	$(shell echo 'application_name = "$(PACKAGE)"' >> build/version.py)

pylauncher: 7z src/pylauncher/*
	cp -rf src/pylauncher build
	cp "$(ICON)" build/pylauncher/application.ico
	sed -i 's/application_name/$(PACKAGE)/' build/pylauncher/pylauncher.exe.manifest
	cd build/pylauncher; make

cpuid: src/cpuid/cpuid.c
	cp -rf src/cpuid build
	cd build/cpuid; make

winboot2: grubutil
	mkdir -p build/winboot
	cp -f data/yldr.cfg data/yldr-bootstrap.cfg build/winboot/
	./build/grubutil/grubinst/grubinst --grub2 --boot-file=yldr -o build/winboot/yldr.mbr
	cd build/winboot && tar cf yldr.tar yldr.cfg
	grub-mkimage -O i386-pc -c build/winboot/yldr-bootstrap.cfg -m build/winboot/yldr.tar -o build/grubutil/core.img \
		loadenv biosdisk part_msdos part_gpt fat ntfs ext2 ntfscomp iso9660 loopback search linux boot minicmd cat cpuid chain halt help ls reboot \
		echo test configfile normal sleep memdisk tar font gfxterm gettext true
	cat /usr/lib/grub/i386-pc/lnxboot.img build/grubutil/core.img > build/winboot/yldr
	
	cp -f data/yldrd.cfg data/yldrd-bootstrap.cfg build/winboot/
	./build/grubutil/grubinst/grubinst --grub2 --boot-file=yldrd -o build/winboot/yldrd.mbr
	cd build/winboot && tar cf yldrd.tar yldrd.cfg
	grub-mkimage -O i386-pc -c build/winboot/yldrd-bootstrap.cfg -m build/winboot/yldrd.tar -o build/grubutil/core.img \
		loadenv biosdisk part_msdos part_gpt fat ntfs ext2 ntfscomp iso9660 loopback search linux boot minicmd cat cpuid chain halt help ls reboot \
		echo test configfile normal sleep memdisk tar font gfxterm gettext true
	cat /usr/lib/grub/i386-pc/lnxboot.img build/grubutil/core.img > build/winboot/yldrd

grubutil: src/grubutil/grubinst/*
	cp -rf src/grubutil build
	cd build/grubutil/grubinst; make

# not compiling 7z at the moment, but source is used by pylauncher
7z: src/7z/C/*.c
	cp -rf src/7z build

runbin: setup
	rm -rf build/test
	mkdir build/test
	cd build/test; ../../tools/wine ../swin.exe --test

check_wine: tools/check_wine
	tools/check_wine

unittest:
	tools/pywine tools/test

runpy:
	PYTHONPATH=src tools/pywine src/main.py --test

clean:
	rm -rf dist/*
	rm -rf build/*
	find ./ -type f -iname "*.py[co]" -exec rm -f {} \;

.PHONY: all build test setup wubi-pre-build runpy runbin ckeck_wine unittest
	7z translations version.py pylauncher grubutil
