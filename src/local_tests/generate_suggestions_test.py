from dotenv import load_dotenv

load_dotenv()

from generate_suggestions.controllers.suggestions_controller import (  # noqa: E402
    SuggestionsController,
)


def main():
    suggestion_controller = SuggestionsController()
    suggestions = suggestion_controller.get_suggestions()
    print(suggestions)


if __name__ == '__main__':
    main()
