from dotenv import load_dotenv

load_dotenv()

from generate_suggestions.controllers.suggestions_controller import (  # noqa: E402
    SuggestionsController,
)


def main():
    suggestion_controller = SuggestionsController()
    suggestions = suggestion_controller.get_suggestions(
        entity_ids_selected=['80555af4-e4f6-4068-bd5b-bedafb27d2bb']
    )

    for index, suggestion in enumerate(suggestions.get('matches')):
        print(f'Match {index + 1}:')
        print(suggestion)
        print('==================================')
        print('\n')


if __name__ == '__main__':
    main()
