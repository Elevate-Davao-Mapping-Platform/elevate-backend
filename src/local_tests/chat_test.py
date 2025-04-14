# noqa
from dotenv import load_dotenv

load_dotenv()

from rag_api.controllers.chat_controller import ChatController  # noqa: E402
from rag_api.models.chat import ChatPromptIn  # noqa: E402


def main():
    chat_controller = ChatController()

    chat_in = ChatPromptIn(
        userId='8b1cac56-af56-4200-814f-77b8dcf32368',
        query='Give me a list of all the startups and enablers that could be a potential partner for my startup',
        chatTopicId='123',
        entryId='123',
    )

    chat_controller.process_prompt(chat_in)


if __name__ == '__main__':
    main()
