rag_api_dependencies:
	poetry export --with=rag_api -o lambdas/rag_api/requirements.txt

deploy_from_local:
	cdk deploy --outputs-file outputs.json --context stage=dev
