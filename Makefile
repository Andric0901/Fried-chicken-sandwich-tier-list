make:  # Set up the commit procedure with required test checks
	touch pre-commit
	echo '#!/bin/bash' > pre-commit
	echo 'python -m pytest -n auto tests.py' >> pre-commit
	echo 'python -m pytest editor_tests.py' >> pre-commit
	chmod +x pre-commit
	mv pre-commit .git/hooks

clean:
	rm -rf .git/hooks/pre-commit

test:
	python -m pytest editor_tests.py
	python -m pytest -n auto tests.py
