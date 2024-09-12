make:  # Set up the commit procedure with required test checks
	touch pre-commit
	echo '#!/bin/bash' > pre-commit
	echo 'pytest tests.py' >> pre-commit
	chmod +x pre-commit
	mv pre-commit .git/hooks

clean:
	rm -rf .git/hooks/pre-commit
