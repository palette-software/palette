
all:
	python setup.py bdist
	make -C DEBIAN all
.PHONY: all

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm '{}' ';'
	make -C DEBIAN clean
