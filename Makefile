.PHONY: test

test:
	pip install -r requirements.test.txt && py.test

doc:
	make --directory docs doctest html

view-docs:
	open docs/_build/html/index.html
