rag_api_dependencies:
	poetry export --only=rag_api -o src/rag_api/layer/requirements.txt

suggestions_dependencies:
	poetry export --only=suggestions -o src/generate_suggestions/layer/requirements.txt

common_dependencies:
	poetry export -o infra/layers/common_dependencies/requirements.txt

deploy_dev2:
	poetry run cdk deploy elevate-backend-stack-dev2 --verbose --debug --trace --progress events --outputs-file outputs.json --context stage=dev2 --require-approval never

deploy_dev:
	poetry run cdk deploy elevate-backend-stack-dev --verbose --debug --trace --progress events --outputs-file outputs.json --context stage=dev --require-approval never
