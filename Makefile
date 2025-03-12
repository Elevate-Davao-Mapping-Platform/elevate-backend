rag_api_dependencies:
	poetry export --with=rag_api -o src/rag_api/requirements.txt

deploy_dev:
	poetry run cdk deploy elevate-backend-stack-dev --verbose --debug --trace --progress events --outputs-file outputs.json --context stage=dev

deploy_staging:
	poetry run cdk deploy elevate-backend-stack-staging --verbose --debug --trace --progress events --outputs-file outputs.json --context stage=staging

deploy_prod:
	poetry run cdk deploy elevate-backend-stack-prod --verbose --debug --trace --progress events --outputs-file outputs.json --context stage=prod
