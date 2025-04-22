from dotenv import load_dotenv

load_dotenv()

from generate_suggestions.controllers.suggestions_controller import (  # noqa: E402
    SuggestionsController,
)


def main():
    suggestion_controller = SuggestionsController()
    suggestions = suggestion_controller.get_suggestions(
        entity_ids_selected=['82c59e97-eec1-4479-8cb4-83d2d8fe56a5']
    )

    for index, suggestion in enumerate(suggestions.get('matches')):
        print(f'Match {index + 1}:')
        print(suggestion)
        print('==================================')
        print('\n')


if __name__ == '__main__':
    main()
