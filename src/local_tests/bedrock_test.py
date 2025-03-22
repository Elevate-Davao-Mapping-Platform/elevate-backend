# noqa
import json

import boto3
from dotenv import load_dotenv
from mypy_boto3_bedrock_agent_runtime.client import AgentsforBedrockRuntimeClient
from mypy_boto3_bedrock_agent_runtime.type_defs import RetrieveRequestTypeDef

load_dotenv()


# Initialize the Bedrock Agent Runtime client
region_name = 'us-east-1'
bedrock_agent_runtime_client: AgentsforBedrockRuntimeClient = boto3.client(
    'bedrock-agent-runtime', region_name=region_name
)
model_id = 'us.anthropic.claude-3-5-haiku-20241022-v1:0'


def main():
    query = 'give me a list of the top startups in Davao City'
    number_of_results = 5

    response: RetrieveRequestTypeDef = bedrock_agent_runtime_client.retrieve(
        knowledgeBaseId='ORGCXIYNDH',
        retrievalQuery={'text': query},
        retrievalConfiguration={
            'vectorSearchConfiguration': {'numberOfResults': number_of_results}
        },
    )

    text_results = []
    retrieval_results = response.get('retrievalResults')
    for result in retrieval_results:
        content = result.get('content')
        text = content.get('text')
        text_results.append(text)

    print('Retrieved context:', text_results)

    # Format the prompt with the new template
    prompt = (
        'You are a context-aware startup ecosystem assistant for Davao City. Your goal is to help startups, '
        'investors, and ecosystem enablers by providing relevant, timely, and personalized support based on '
        "the user's needs and the local startup environment.\n\n"
        f'## User Input:\n{query}\n\n'
        '## Chat History:\n'
        '(No previous chat history for this test)\n\n'
        '## Retrieved Knowledge Base Data:\n'
        f'{json.dumps(text_results, indent=2)}\n'
        '(This includes information from local incubators, web-scraped directories, and structured database entries '
        'on startups, investors, and mentors.)\n\n'
        '## Instructions:\n'
        '- Your responses must reflect the current startup landscape of Davao City.\n'
        '- Incorporate specific local context (e.g., known incubators, typical funding rounds, or local startup challenges).\n'
        '- Leverage the retrieved knowledge base to offer tailored recommendations.\n'
        '- If information is not available, ask clarifying questions instead of making assumptions.\n'
        '- Keep the response concise, friendly, and helpful.\n'
        '- Never hallucinate; rely only on the provided context.\n\n'
        '## Response:\n'
    )

    # Invoke the model with the new prompt
    client = boto3.client('bedrock-runtime', region_name=region_name)
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(
            {
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1000,
                'messages': [{'role': 'user', 'content': prompt}],
            }
        ),
        contentType='application/json',
        accept='application/json',
    )

    # Parse and print the response
    response_body = json.loads(response['body'].read())
    print('\nModel Response:')
    print(response_body.get('content', 'No response content'))


if __name__ == '__main__':
    main()
