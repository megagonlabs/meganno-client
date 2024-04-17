from pathlib import Path

from setuptools import find_packages, setup

version = Path("./meganno_client/version").read_text().strip()
package = {
    "name": "meganno_client",
    "version": version,
    "description": "Megagon Client-side Python Programmatic Library",
    "url": "https://github.com/megagonlabs/meganno-client",
    "author": "Megagon Labs",
    "author_email": "",
    "license": "unlicense",
    "packages": find_packages(),
    "install_requires": [
        "pandas==1.5.3",
        "httpx==0.24.1",
        "nest_asyncio==1.5.1",
        "websockets==11.0.3",
        "tqdm==4.62.0",
        "openai==0.28.1",
        "jsonschema>=4.18.0",
        "notebook==6.5.5",
        "traitlets==5.9.0",
        "pydash==7.0.6",
        "tabulate==0.9.0",
        "jaro-winkler==2.0.3",
    ],
    "extras_require": {
        "ui": ["meganno-ui @ git+https://github.com/megagonlabs/meganno-ui.git@v1.5.7"]
    },
    "include_package_data": True,
    "zip_safe": False,
}
setup(**package)
