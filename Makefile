.PHONY: test check install uninstall run check-connection

test:
	./scripts/test.sh

check: test
	git diff --check

install:
	./scripts/install.sh

uninstall:
	./scripts/uninstall.sh

run:
	./codex-usage

check-connection:
	./codex-usage --check
