PYTHON=python
PYTEST=pytest

# Detect if we should use the venv path (Windows)
ifneq (,$(wildcard ./venv/Scripts/pytest.exe))
	PYTEST=./venv/Scripts/pytest.exe
endif

make:  # Set up the commit procedure with required test checks
	touch pre-commit
	echo '#!/bin/bash' > pre-commit
	echo '$(PYTEST) -n auto tests/tests.py' >> pre-commit
	chmod +x pre-commit
	mv pre-commit .git/hooks

clean:
	rm -rf .git/hooks/pre-commit

test: test-editor test-dynamic test-general

test-general:
	$(PYTEST) -n auto tests/tests.py

test-editor:
	$(PYTEST) tests/editor_tests.py

test-dynamic:
	$(PYTEST) tests/editor_dynamic_tests.py
