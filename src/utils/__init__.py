from src.utils.general.get_sample_from_distribution import (
    get_sample_from_distribution,
)
from src.utils.general.search_files_with_name import search_files_with_name

# This is a Windows-specific import
from os import name

if name == "nt":
    from src.utils.general.simple_popup_handler import SimplePopupHandler
else:
    from unittest.mock import MagicMock

    SimplePopupHandler = MagicMock
