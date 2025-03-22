rag_api_dependencies:
	poetry export --with=rag_api -o src/rag_api/layer/requirements.txt

deploy_dev2:
	poetry run cdk deploy elevate-backend-stack-dev2 --verbose --debug --trace --progress events --outputs-file outputs.json --context stage=dev2 --require-approval never

deploy_dev:
	poetry run cdk deploy elevate-backend-stack-dev --verbose --debug --trace --progress events --outputs-file outputs.json --context stage=dev --require-approval never

deploy_staging:
	poetry run cdk deploy elevate-backend-stack-staging --verbose --debug --trace --progress events --outputs-file outputs.json --context stage=staging --require-approval never

deploy_prod:
	poetry run cdk deploy elevate-backend-stack-prod --verbose --debug --trace --progress events --outputs-file outputs.json --context stage=prod --require-approval never
