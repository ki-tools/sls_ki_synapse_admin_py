.PHONY: reqs
reqs:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt


.PHONY: devserve
devserve:
	sls wsgi serve


.PHONY: test
test:
	pytest -v --cov --cov-report=term --cov-report=html


.PHONY: deploy_dev
deploy_dev:
	sls deploy --stage dev


.PHONY: remove_dev
remove_dev:
	sls remove --stage dev


.PHONY: deploy_staging
deploy_staging:
	sls deploy --stage staging


.PHONY: remove_staging
remove_staging:
	sls remove --stage staging


.PHONY: deploy_production
deploy_production:
	sls deploy --stage production


.PHONY: remove_productio
remove_productio:
	sls remove --stage productio
