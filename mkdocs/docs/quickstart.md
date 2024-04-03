# Getting Started
## Installation
1. Download [conda](https://conda.io/projects/conda/en/stable/user-guide/install/download.html)
2. Create a conda environment
      - Run `conda create -n <env_name> python=3.9`
      - Run `conda activate <env_name>`
3. Install **meganno-client** with **meganno-ui** (recommended for notebook users)
   
    > You can use either `SSH` or `HTTPS` to install this python package.
    
    > Add @vx.x.x tag after the github URL

      - Run `pip install "meganno_client[ui] @ git+ssh://git@github.com/megagonlabs/meganno-client.git"`
      - Run `pip install "meganno_client[ui] @ git+https://github.com/megagonlabs/meganno-client.git"`
          - You may need to use [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) instead of password<br/>
    ---
    To install without **meganno-ui**
      
      - Run `pip install git+ssh://git@github.com/megagonlabs/meganno-client.git`
      - Run `pip install git+https://github.com/megagonlabs/meganno-client.git`
          - You may need to use [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) instead of password<br/>
 
4. Set up OpenAI API Keys [using environment variables in place of your API key
](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety#h_a1ab3ba7b2)

## Self-hosted service
- Download docker compose files at [meganno-service](https://github.com/megagonlabs/meganno-service)
- Follow [setup instructions](https://github.com/megagonlabs/meganno-service?tab=readme-ov-file#set-up-services)

## Authentication
We have 2 ways to authenticate with the service:

1. Short-term 1 hour access with username and password sign in.
    - Require re-authentication every hour.
    - After executing `auth = Authentication(project="<project_name>")` (this only works for notebook and terminal running on local computer), you will be provided with a sign in interface via a new browser tab.
        ![Sign-in](assets/images/signin.png){: style="width:300px"}
   
    - After signing in, you will be able to generate a long-term personal access token by running `auth.create_access_token(expiration_duration=7, note="testing")`
        - `expiration_duration` is in days.
        - To have <strong>non-expiring</strong> token, set `expiration_duration` to 0 (under the hood, it still expires after 100 years).

2. Long-term access with access token without signing in every time.
    - If the notebook or terminal is running on the cloud, you need to use this method to authenticate with the service.
    - With the save token, you can initialize the authentication class object by executing: 
    ```python
    auth = Authentication(project="<project_name>", token="<your_token>")
    ```

### Roles
MEGAnno supports 2 types of user roles: Admin and Contributor. Admin users are project owners deploying the services; they have full access to the project such as importing data or updating schemas. Admin users can invite contributors by sharing invitation code(s) with them. Contributors can only access their own annotation namespace and cannot modify the project.

To invite contributors, follow the instructions below:

1. Initialize Admin class object:
```python
from labeler_client import Admin
token = "..."
auth = Authentication(project="<project_name>", token=token)

admin = Admin(project="eacl_demo", auth=auth)
# OR
admin = Admin(project="eacl_demo", token=token)
```
2. Genereate invitation code
    - invitation code has 7-day expiration duration
```python
admin.create_invitation(single_use=True, code="<invitation_code>", role_code="contributor")
```
3. To renew or revoke an existing invitation code:
    - after renewing, the expiration date is extended by another 7 days.
```python
admin.get_invitations()
admin.renew_invitation(id="<invitation_code_id>")
admin.revoke_invitation(id="<invitation_code_id>")
```
4. New users with valid invitation code can sign up by installing the client library and follow the instructions below:
    - After executing `auth = Authentication(project="<project_name>")`, a new browser tab will present itself.
    - Clicking on "Sign up" at the bottom of the dialog, and you will be taken to the sign up page.
    ![Sign-up](assets/images/signup.png){: style="width:300px"}

## Basic Usages
Please also refer to this [notebook](https://github.com/megagonlabs/meganno-client/blob/main/Examples/Example%201%20-%20Basic%20pipeline.ipynb) for a running example of the basic pipeline of using labeler in a notebook.


### Setting Schema
*Schema* defines the annotation task. Example of setting schema for a sentiment analysis task with positive and negative options. 
```Python
demo.get_schemas().set_schemas({
    'label_schema': [
        {
            "name": "sentiment",
            "level": "record", 
            "options": [
                { "value": "pos", "text": "positive" },
                { "value": "neg", "text": "negative" },
            ]
        }
    ]
})
demo.get_schemas().value(active=True)		
```
A label can be defined to have level `record` or `span`. Record-level labels correspond to the entire data record, while span-level labels are associated with a text span in the record. See [Updating Schema](advanced.md#updating-schema) for an example of a more complex schema.

### Importing Data
Given a pandas [dataframe](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html) like this (example generated from this [Twitter US Airline Sentiment dataset](https://www.kaggle.com/datasets/crowdflower/twitter-airline-sentiment)):

|   id | tweet                                        |
|-----:|:---------------------------------------------|
|    0 | @united how else would I know it was denied? |
|    1 | @JetBlue my SIL bought tix for us to NYC. We were told at the gate that her cc was declined. Supervisor accused us of illegal activity.                           |
|    2 | @JetBlue dispatcher keeps yelling and hung up on me!                        |

Importing data is easy by providing column names for `id` which is a unique importing identifier for data records, and `content` which is the raw text field.

```python
demo.import_data_df(df, column_mapping={
    'id':'id',
    'content':'tweet'
})
```

### Exploratory Labeling
Not all data points are equally important for downstream models and applications. There are often cases where users might want to prioritize a particular batch (e.g., to achieve better class or domain coverage or focus on the data points that the downstream model cannot predict well). Labeler provides a flexible and controllable way of organizing annotation projects through the exploratory labeling. This annotation process is done by first identifying an interesting subset and assigning labels to data in the subset. We provide a set of “power tools” to help identify valuable subsets.

The script below shows an example of searching for data records with keyword "delay" and bringing up a widget for annotation in the next cell. More examples [here](advanced.md#subset-suggestion).
```python
# search results => subset s1
s1 = demo.search(keyword='delay', limit=10, skip=0)
# bring up a widget 
s1.show()
```

#### Column Filters
<img src="../assets/images/column_filter_reset.png" alt="Column Filters" width="800">
<br/><span style="color: gray;">*To view all column filters, click on "Filters" button; to reset all column filters, click on "Reset filters" button.*</span>

#### Column Order & Visibility
<img src="../assets/images/column_visibility.png" alt="Column Order & Visibilty" width="500">
<br/><span style="color: gray;">
*1. To re-order and re-size column, mouse over column drag handler (left grip handler for re-order and right column edge for re-size).*
<br/>
*2. To toggle column visiblity, click on "Columns", then toggle column to show/hide.*
<br/>
*3. To reset column ordering and visibility, click on "Reset columns" button.*
</span>

#### Metadata Focus-view
<img src="../assets/images/metadata_focusview.png" alt="Metadata Focus-view" width="600">
<br/><span style="color: gray;">*To focus on a single metadata value, click on "Settings" button, then choose a metadata name from the list.*</span>

### Exporting
Although iterations can happen within a single notebook, it's easy to export the data, and annotations collected:

```python
# collecting the annotation generated by all annotators
demo.export()
```



