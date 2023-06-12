PREFIX = ~/.local

install:
	install -Dm755 ddgmail.py ${PREFIX}/bin/ddgmail
	install -Dm644 LICENSE ${PREFIX}/share/ddgmail/LICENSE

uninstall:
	rm -f ${PREFIX}/bin/ddgmail
	rm -rf ${PREFIX}/share/ddgmail

all: install
