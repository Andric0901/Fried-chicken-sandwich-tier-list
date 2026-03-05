PYTHON=./venv/Scripts/python.exe
PYTEST=./venv/Scripts/pytest.exe

make:  # Set up the commit procedure with required test checks
	touch pre-commit
	echo '#!/bin/bash' > pre-commit
	echo '$(PYTEST) -n auto tests.py' >> pre-commit
	echo '$(PYTEST) editor_tests.py' >> pre-commit
	echo '$(PYTEST) -n auto editor_dynamic_tests.py' >> pre-commit
	chmod +x pre-commit
	mv pre-commit .git/hooks

clean:
	rm -rf .git/hooks/pre-commit

test:
	$(PYTEST) editor_tests.py
	$(PYTEST) -n auto editor_dynamic_tests.py
	$(PYTEST) -n auto tests.py
