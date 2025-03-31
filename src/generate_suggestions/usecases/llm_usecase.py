import os
from http import HTTPStatus
from typing import Union

import instructor
from anthropic import AnthropicBedrock
from aws_lambda_powertools import Logger
from instructor.utils import disable_pydantic_error_url
from shared_modules.models.dynamodb.suggestions import Suggestions
from shared_modules.models.schema.message import ErrorResponse
from shared_modules.models.schema.suggestions import SuggestionMatchList


class LLMUsecase:
    def __init__(self):
        self.logger = Logger()
        self.bedrock_model_id = 'us.anthropic.claude-3-5-haiku-20241022-v1:0'
        self.bedrock_region = os.getenv('BEDROCK_REGION')
        self.max_tokens = 4096

    def build_prompt(self, entities_json):
        prompt = f"""
        You are an expert startup ecosystem matchmaker with deep knowledge of startup-enabler partnerships, specifically within Davao City's ecosystem.
        Your task is to analyze the provided entities (all based in Davao City) and suggest ideal partnerships based on their compatibility.
            ## Input Data:
            {entities_json}

            ## Context:
            All startups and enablers are based in Davao City, which means:
            - They share a common understanding of the local business environment
            - They can easily arrange face-to-face meetings and collaborations
            - They are part of the same growing tech and startup ecosystem
            - They may already have overlapping networks within the local community

            ## Instructions:
            1. Analyze each entity's profile considering these key matching criteria:

            For Startup-Enabler Matches:
            - Industry alignment (startup's industries vs enabler's industryFocus)
            - Stage compatibility (startup's startupStage vs enabler's startupStagePreference)
            - Business model fit (startup's revenueModel vs enabler's preferredBusinessModels)
            - Support needs (enabler's supportType and fundingStageFocus)
            - Geographic proximity (already established as all entities are in Davao City)

            For Startup-Startup Matches:
            - Complementary industries
            - Similar growth stage
            - Potential for collaboration or resource sharing
            - Geographic proximity
            - Complementary milestone achievements

            For Enabler-Enabler Matches:
            - Complementary support types
            - Non-overlapping industry focus
            - Potential for co-investment or joint programs
            - Geographic synergies
            - Portfolio complementarity

            2. For each suggested match:
            - Explain the specific reasons for compatibility
            - Highlight potential synergies
            - Identify mutual benefits
            - Rate the match strength (High/Medium/Low)
            - Suggest specific collaboration opportunities

            3. Important Guidelines:
            - Focus on actionable, practical partnerships within the Davao City ecosystem
            - Consider both parties' constraints and preferences in the local context
            - Prioritize matches based on alignment strength
            - Identify any potential risks or challenges specific to the local environment
            - Suggest next steps for initiating the partnership, including local venues or events for meetings

            ## Output Format:
            Please provide your analysis in the following structure:

            1. Top Startup-Enabler Matches
            2. Top Startup-Startup Matches
            3. Top Enabler-Enabler Matches

            For each match, include:
            - Match Pair
            - Compatibility Score
            - Key Synergies
            - Rationale
            - Recommended Next Steps

            ## Response:
            """
        return prompt

    def invoke_llm(
        self,
        prompt: str,
    ) -> Suggestions:
        """Generate questions from the LLM.

        :param str prompt: The prompt for the question generator.
        :return TaggedQuestionInstanceValidated: The validated output from the LLM.
        """
        disable_pydantic_error_url()  # instructor not include error url in response to save on tokens

        model = AnthropicBedrock(aws_region=self.bedrock_region)
        client = instructor.from_anthropic(model, mode=instructor.Mode.ANTHROPIC_TOOLS)
        resp, _ = client.chat.completions.create_with_completion(
            model=self.bedrock_model_id,
            max_tokens=self.max_tokens,
            messages=[
                {'role': 'user', 'content': prompt},
            ],
            response_model=SuggestionMatchList,
            max_retries=2,
        )
        return resp

    def generate_response(self, entities) -> Union[SuggestionMatchList, ErrorResponse]:
        """
        Generate a response from the LLM.

        :param list entities: The entities to generate a response for.
        :return Union[SuggestionMatchList, ErrorResponse]: The response from the LLM.
        """
        try:
            prompt = self.build_prompt(entities)
            response_text = self.invoke_llm(prompt)

            return response_text

        except Exception as e:
            self.logger.error(f'Error generating response: {e}')
            return ErrorResponse(
                response=str(e),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
