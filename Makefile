.PHONY: reqs
reqs:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt


.PHONY: devserve
devserve:
	scripts/devserve.py . www/server.app 5000 localhost --ssl-context adhoc
# 	sls wsgi serve


.PHONY: test
test:
	pytest -v --cov --cov-report=term --cov-report=html


.PHONY: deploy_development
deploy_development:
	sls deploy --stage development


.PHONY: deploy_dev
deploy_dev: deploy_development


.PHONY: remove_development
remove_development:
	sls remove --stage development


.PHONY: remove_dev
remove_dev: remove_development


.PHONY: deploy_staging
deploy_staging:
	sls deploy --stage staging


.PHONY: remove_staging
remove_staging:
	sls remove --stage staging


.PHONY: deploy_production
deploy_production:
	sls deploy --stage production


.PHONY: remove_production
remove_production:
	sls remove --stage production
