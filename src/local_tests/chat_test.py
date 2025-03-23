# noqa
from dotenv import load_dotenv

load_dotenv()

from rag_api.controllers.chat_controller import ChatController  # noqa: E402
from rag_api.models.chat import ChatPromptIn  # noqa: E402


def main():
    chat_controller = ChatController()

    chat_in = ChatPromptIn(userId='123', query='Hello, how are you?', chatTopicId='123')

    chat_controller.process_prompt(chat_in)


if __name__ == '__main__':
    main()
