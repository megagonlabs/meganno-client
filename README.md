# **meganno-client**
Client side programmatic python library for MEGAnno service with an inclusion of LLMs as annotators

![version](https://img.shields.io/badge/meganno--client%20latest-v1.5.4-blue)
## **Prerequisite Knowledge**
Documentation for [MEGAnno concepts](https://meganno.megagon.info) 

## **Installation**
1. Download [conda](https://conda.io/projects/conda/en/stable/user-guide/install/download.html)
2. Create and activate a conda environment
   - Run `conda create -n <env_name> python=3.9`
   - Run `conda activate <env_name>`
3. Install **meganno-client** with **meganno-ui** (recommended for notebook users)
    > You can use either `SSH` or `HTTPS` to install this python package.
    
    > Add @vx.x.x tag after the github URL
    - Run `pip install "meganno_client[ui] @ git+ssh://git@github.com/megagonlabs/meganno-client.git"`
    - Run `pip install "meganno_client[ui] @ git+https://github.com/megagonlabs/meganno-client.git"`
    ---
    To install without **meganno-ui**
      - Run `pip install git+ssh://git@github.com/megagonlabs/meganno-client.git`
      - Run `pip install git+https://github.com/megagonlabs/meganno-client.git`
4. Set up OpenAI API Keys [using environment variables in place of your API key
](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety#h_a1ab3ba7b2). Using these API keys will allow `MEGAnno` to access OpenAI's models through the API. You can find your API key using these [instructions](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key). We do not collect or store your API keys.

## **Self-hosted service**
- Download docker compose files at [meganno-service](https://github.com/megagonlabs/meganno-service)
- Follow [setup instructions](https://github.com/megagonlabs/meganno-service?tab=readme-ov-file#set-up-services)
## **Run Jupyter Notebook**
Configure your browser to allow pop-ups; we recommend using Google Chrome. 
- Install jupyter server `pip install jupyter`
- Run `jupyter notebook`
- You can find example notebooks under the Example folder

## For client development
- Clone and [create your own branch](https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-and-deleting-branches-within-your-repository)
- Under **root** folder
  - Run `pip install -e .`
- [Submit pull-request](https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) to `stage` or appropriate development branch
## For documentation development
meganno-client documentation is hosted [here](https://meganno.megagon.info/) (we use [`Mike`](https://github.com/jimporter/mike) with [`MkDocs`](https://github.com/mkdocs/mkdocs))
- Install Mike, theme and plugins
- **DO NOT** try to manually modify `gh-pages` branch unless you know what you are doing
- Run `mike list` to list all existing docs
- To deploy a specific version of docs, run `mike deploy [version]`
  - **DO NOT** try to re-deploy docs for older versions unless you are certain
  - To retitle a version, run `mike retitle [version-or-alias] [title]`
  - To set default, run `mike set-default [version-or-alias]`
  - To set alias, run `mike alias [version-or-alias] [alias]...`
- To view the docs you just deployed on localhost, run `mike serve`
  - use `-a localhost:[port]`
- To publish new docs, run `mike deploy [version] --push`
  - This will trigger GitHub action: `pages build and deployment`
- For detailed documentation, refer to [Mike usage documentation](https://github.com/jimporter/mike#usage)

## Citation

Check out our research papers on [exploratory labeling (DaSH@EMNLP 2022)](https://aclanthology.org/2022.dash-1.1/) and [human-LLM collaborative annotation (EACL 2024 Demo)](https://aclanthology.org/2024.eacl-demo.18/).

If you use MEGAnno in your work, please cite as:

```bibtex
@inproceedings{kim-etal-2024-meganno,
    title = "{MEGA}nno+: A Human-{LLM} Collaborative Annotation System",
    author = "Kim, Hannah and Mitra, Kushan and Li Chen, Rafael and Rahman, Sajjadur and Zhang, Dan",
    editor = "Aletras, Nikolaos and De Clercq, Orphee",
    booktitle = "Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics: System Demonstrations",
    month = mar,
    year = "2024",
    address = "St. Julians, Malta",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2024.eacl-demo.18",
    pages = "168--176",
}
```
```bibtex
@inproceedings{zhang-etal-2022-meganno,
    title = "{MEGA}nno: Exploratory Labeling for {NLP} in Computational Notebooks",
    author = "Zhang, Dan and Kim, Hannah and Li Chen, Rafael and Kandogan, Eser and Hruschka, Estevam",
    editor = "Dragut, Eduard and Li, Yunyao and Popa, Lucian and Vucetic, Slobodan and Srivastava, Shashank",
    booktitle = "Proceedings of the Fourth Workshop on Data Science with Human-in-the-Loop (Language Advances)",
    month = dec,
    year = "2022",
    address = "Abu Dhabi, United Arab Emirates (Hybrid)",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2022.dash-1.1",
    pages = "1--7",
}
```

## Disclosure
This software may include, incorporate, or access open source software (OSS) components, datasets and other third party components, including those identified below. The license terms respectively governing the datasets and third-party components continue to govern those portions, and you agree to those license terms may limit any distribution. You may  use any OSS components under the terms of their respective licenses, which may include BSD 3, Apache 2.0, or other licenses. In the event of conflicts between Megagon Labs, Inc. (“Megagon”) license conditions and the OSS license conditions, the applicable OSS conditions governing the corresponding OSS components shall prevail. 
You agree not to, and are not permitted to, distribute actual datasets used with the OSS components listed below. You agree and are limited to distribute only links to datasets from known sources by listing them in the datasets overview table below. You agree that any right to modify datasets originating from parties other than Megagon  are governed by the respective third party’s license conditions. 
You agree that Megagon grants no license as to any of its intellectual property and patent rights.  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS (INCLUDING MEGAGON) “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. You agree to cease using and distributing any part of the provided materials if you do not agree with the terms or the lack of any warranty herein.
While Megagon makes commercially reasonable efforts to ensure that citations in this document are complete and accurate, errors may occur. If you see any error or omission, please help us improve this document by sending information to contact_oss@megagon.ai.

All open source software components used within the product are listed below (including their copyright holders and the license information).
For OSS components having different portions released under different licenses, please refer to the included Upstream link(s) specified for each of the respective OSS components for identifications of code files released under the identified licenses.

| ID  | OSS Component Name | Modified | Copyright Holder | Upstream Link | License  |
|-----|----------------------------------|----------|------------------|-----------------------------------------------------------------------------------------------------------|--------------------|
| 01 | pandas | No  | AQR Capital Management, LLC, Lambda Foundry, Inc. and PyData Development Team | [link](https://pandas.pydata.org/) | BSD 3-Clause License |
| 02 | tqdm | No  | Noamraph and tqdm developers | [link](https://tqdm.github.io/) | MIT License, Mozilla Public License 2.0 |
| 03 | httpx | No  | Encode OSS Ltd. | [link](https://github.com/encode/httpx) | BSD 3-Clause License |
| 04 | nest_asyncio | No  | Ewald de Wit | [link](https://github.com/erdewit/nest_asyncio) | BSD 3-Clause License |
| 05 | websockets | No  | Aymeric Augustin and contributors | [link](https://github.com/python-websockets/websockets) | BSD 3-Clause License |
| 06 | openai | No  | OpenAI | [link](https://github.com/openai/openai-python) | Apache License Version 2.0 |
| 07 | Jsonschema | No  | Julian Berman | [link](https://github.com/python-jsonschema/jsonschema) | MIT License |
| 08 | notebook | No  | Jupyter Development Team | [link](https://github.com/jupyter/notebook) | BSD 3-Clause License |
| 09 | traitlets | No  | IPython Development Team | [link](https://github.com/ipython/traitlets) | BSD 3-Clause License |
| 10 | pydash | No  | Derrick Gilland | [link](https://github.com/dgilland/pydash) | MIT License |
| 11 | tabulate | No  | Sergey Astanin and contributors | [link](https://github.com/astanin/python-tabulate) | MIT License |
| 12 | jaro-winkler | No  | Free Software Foundation, Inc. | [link](https://github.com/richmilne/JaroWinkler.git) | GPL 3.0 License |
