# ----------------------------------
#          INSTALL & TEST
# ----------------------------------
install_requirements:
	@pip install -r requirements.txt

check_code:
	@flake8 becode3d/*.py --ignore=E501

test:
	@coverage run -m pytest tests/*.py
	@coverage report -m --include='./becode3d/*'

clean:
	@rm -f */version.txt
	@rm -f .coverage
	@rm -fr */__pycache__ */*.pyc __pycache__
	@rm -fr build dist
	@rm -fr houses3d-*.dist-info
	@rm -fr houses3d.egg-info

install:
	@pip install . -U

all: clean install test check_code

uninstal:
	@python setup.py install --record files.txt
	@cat files.txt | xargs rm -rf
	@rm -f files.txt