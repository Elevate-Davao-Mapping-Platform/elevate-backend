# noqa
import csv
import uuid
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from rag_api.controllers.chat_controller import ChatController  # noqa: E402
from rag_api.models.chat import ChatPromptIn  # noqa: E402


def process_prompts_to_csv(prompts, output_file='responses.csv'):
    chat_controller = ChatController()
    user_id = '80555af4-e4f6-4068-bd5b-bedafb27d2bb'

    # Open CSV file to write responses
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(['Prompt', 'Response', 'ChatTopicId', 'EntryId'])

        # Process each prompt
        for prompt in prompts:
            entry_id = str(uuid.uuid4())

            chat_in = ChatPromptIn(userId=user_id, query=prompt, entryId=entry_id)

            # Get response from chat controller
            result = chat_controller.process_prompt(chat_in)

            # Write to CSV
            writer.writerow([prompt, result['response'], result['chatTopicId'], result['entryId']])


def main():
    chatbot_prompts = [
        'Give me a list of fintech startups in Makati City',
        # 'List startup incubators in Cebu City',
        # 'Is InnovatePH Accelerator a startup or incubator?',
        # 'Who are potential investors for AgriNova?',
        # 'Suggest partners for Finwise',
        # 'What does the ecosystem map show?',
        # 'Who won the NBA Finals?',
        # '1. List edtech startups\n2. Which of them are funded?',
        # 'Who can mentor AI startups?',
        # 'Hey, I’m working on AgriNova. Where can I get funding?',
        # 'Can I access the financial reports of Finwise?',
        # 'What has AgriNova achieved so far?',
        # 'Who is the target audience of Finwise?',
        # 'What is Finwise’s biggest traction milestone?',
        # 'Which investors might fund SnackSavvy?',
        # 'Who is the founder of AgriNova?',
        # 'How is Finwise’s business model different from SnackSavvy?',
        # 'Which startup in Cebu connects students to tutors?',
        # 'What’s the background of SnackSavvy’s founder?',
        # 'Which investors are a good fit for AgriNova?',
        # 'Who provides over ₱50M in funding?',
        # 'What does MindForge Ventures look for in a startup?',
        # 'Does InnovatePH Accelerator provide mentorship?',
        # 'How has AgriLift PH helped its portfolio startups?',
        # 'What stages does Bayanihan Angels support?',
        # 'Who supports startups with a subscription-based model?',
        # 'What kind of founders do investors prefer?',
        # 'How can I get in touch with AgriLift PH?',
        # 'What role does InnovatePH Accelerator play in the startup ecosystem?',
    ]

    # Process prompts to CSV
    print('Processing prompts to CSV...')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'local_tests/chat_test_csv/chatbot_prompts_{timestamp}.csv'
    process_prompts_to_csv(chatbot_prompts, output_file)
    print(f'Prompts processed to {output_file}.')


if __name__ == '__main__':
    main()
