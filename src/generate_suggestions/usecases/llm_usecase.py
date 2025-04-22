import os
from http import HTTPStatus
from typing import List, Union

import instructor
from anthropic import AnthropicBedrock
from aws_lambda_powertools import Logger
from instructor.utils import disable_pydantic_error_url
from shared_modules.models.dynamodb.suggestions import Suggestions
from shared_modules.models.schema.entity import EntitySchema
from shared_modules.models.schema.message import ErrorResponse
from shared_modules.models.schema.suggestions import SuggestionMatchList


class LLMUsecase:
    def __init__(self):
        self.logger = Logger()
        self.bedrock_model_id = 'us.anthropic.claude-3-5-haiku-20241022-v1:0'
        self.bedrock_region = os.getenv('BEDROCK_AWS_REGION')
        self.max_tokens = 4096

    def build_prompt(
        self, entities_available: List[EntitySchema], entities_selected: List[EntitySchema]
    ):
        """
        Build a prompt for the LLM to generate a list of suggested matches.

        :param list entities_available: The entities available to generate a response for.
        :param list entities_selected: The entities selected to generate a response for.
        :return str: The prompt for the LLM.
        """
        prompt = f"""
        You are an expert startup ecosystem matchmaker with deep knowledge of startup-enabler partnerships, specifically within Davao City's ecosystem.
        Your task is to analyze the provided entities (all based in Davao City) and suggest ideal partnerships based on their compatibility.
            ## Input Data:
            Selected Entities (Primary Focus):
            {entities_selected}

            Available Entities (Potential Matches):
            {entities_available}

            ## Context:
            IMPORTANT: Only generate matches that include at least one entity from the Selected Entities list above. Do not suggest matches between entities that are only from the Available Entities pool.

            All startups and enablers are based in Davao City, which means:
            - They share a common understanding of the local business environment
            - They can easily arrange face-to-face meetings and collaborations
            - They are part of the same growing tech and startup ecosystem
            - They may already have overlapping networks within the local community

            ## Instructions:
            1. ONLY suggest matches where at least one entity is from the Selected Entities list
            2. Analyze each entity's profile considering these key matching criteria:

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

            3. For each suggested match:
            - Ensure at least one entity is from the Selected Entities list
            - Explain the specific reasons for compatibility
            - Highlight potential synergies
            - Identify mutual benefits
            - Rate the match strength (High/Medium/Low)
            - Suggest specific collaboration opportunities

            4. Important Guidelines:
            - ONLY generate matches that include entities from the Selected Entities list
            - Focus on actionable, practical partnerships within the Davao City ecosystem
            - Consider both parties' constraints and preferences in the local context
            - Prioritize matches based on alignment strength
            - Identify any potential risks or challenges specific to the local environment
            - Suggest next steps for initiating the partnership, including local venues or events for meetings

            ## Output Format:
            Please provide your analysis in the following structure, ensuring each match includes at least one Selected Entity:

            1. Top Startup-Enabler Matches
            2. Top Startup-Startup Matches
            3. Top Enabler-Enabler Matches

            For each match, include:
            - Match Pair (with at least one entity from Selected Entities)
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

    def generate_response(
        self, entities_available: List[EntitySchema], entities_selected: List[EntitySchema]
    ) -> Union[SuggestionMatchList, ErrorResponse]:
        """
        Generate a response from the LLM.

        :param list entities_available: The entities available to generate a response for.
        :param list entities_selected: The entities selected to generate a response for.
        :return Union[SuggestionMatchList, ErrorResponse]: The response from the LLM.
        """
        try:
            prompt = self.build_prompt(entities_available, entities_selected)
            return self.invoke_llm(prompt)

        except Exception as e:
            self.logger.error(f'Error generating response: {e}')
            return ErrorResponse(
                response=str(e),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
