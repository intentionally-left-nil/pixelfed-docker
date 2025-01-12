.PHONY: setup scaffold clean

setup:
	if [ ! -d "./env" ]; then \
		python -m venv ./env && \
		./env/bin/pip install -r requirements.txt; \
	fi

scaffold: setup
	./env/bin/python scaffold.py

clean:
	rm -rf ./env
