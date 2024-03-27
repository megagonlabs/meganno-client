from pathlib import Path

import nest_asyncio

nest_asyncio.apply()

_VERSION_PATH = Path(__file__).parent / "version"
version = Path(_VERSION_PATH).read_text().strip()
print("labeler-client: " + version)

from .admin import Admin
from .authentication import Authentication
from .controller import Controller
from .prompt import PromptTemplate
from .service import Service
