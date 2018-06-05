.PHONY: test

test:
	pip install -r requirements.test.txt && rm -rf **/*.pyc && rm -rf **/__pycache__/*.* && py.test
