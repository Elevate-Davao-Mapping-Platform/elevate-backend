import os
from typing import List


class LambdaUtils:
    @staticmethod
    def get_asset_excludes(included_folders: List[str]) -> List[str]:
        """
        Returns a list of folders to exclude based on the folders that should be included.

        Args:
            included_folders (List[str]): List of folder names to include (e.g. ['get_suggestions', 'rag_api'])

        Returns:
            List[str]: List of folders to exclude

        Example:
            >>> get_asset_excludes(['get_suggestions'])
            ['**/__pycache__', 'local_tests', 'rag_api', 'get_analytics', 'get_saved_profiles', 'suggestions_cron']
        """
        # Standard excludes that should always be excluded
        standard_excludes = {'**/__pycache__', 'local_tests'}

        # Dynamically get all folders by scanning src directory
        src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
        all_lambda_folders = {
            item for item in os.listdir(src_path) if os.path.isdir(os.path.join(src_path, item))
        }

        included_set = set(included_folders)
        excluded_folders = all_lambda_folders - included_set

        return list(standard_excludes | excluded_folders)
