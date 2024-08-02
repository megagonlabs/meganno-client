import asyncio
import json
import math
import time
import warnings

import httpx
import pandas as pd
import pydash
from tqdm import tqdm

from meganno_client.authentication import Authentication
from meganno_client.constants import (BATCH_SIZE, DEFAULT_LIST_LIMIT, DNS_NAME,
                                      HTTPX_LIMITS, REQUEST_TIMEOUT_SECONDS,
                                      SERVICE_ENDPOINTS)
from meganno_client.helpers import get_request, post_request
from meganno_client.schema import Schema
from meganno_client.statistic import Statistic
from meganno_client.subset import Subset


class Service:
    """
    Service objects communicate to back-end MEGAnno services and establish
    connections to a MEGAnno project.


    """

    def __init__(self, host=None, project=None, token=None, auth=None, port=5000):
        """
        Init function

        Parameters
        -------
        host : str, optional
            Host IP address for the back-end service to connect to.
            If None, connects to a Megagon-hosted service.
        project : str
            Project name. The name needs to be unique within the host
            domain.
        token : str
            User's authentication token.
        auth : Authentication
            Authentication object.
            Can be skipped if a valid token is provided.
        """
        if pydash.is_empty(project):
            raise Exception("Project cannot be None or empty.")
        if pydash.is_empty(token) and pydash.is_empty(auth):
            raise Exception("At least 1 authentication method is required.")
        self.project = project
        self.token = token
        self.port = port
        self.auth: Authentication = auth
        self.host = host
        self.user = None
        self.version = None
        response = get_request(
            path=self.get_service_endpoint() + "?url_check=1", timeout=5
        )
        if response.status_code == 200:
            self.version = pydash.objects.get(response.json(), "version", None)
        else:
            raise Exception(response.text)

    def get_version(self):
        return self.version

    def show(self, config={}):
        """
        Show project management dashboard in a floating dashboard.
        """
        from meganno_ui.widgets.Dashboard import Dashboard

        current_time = int(time.time())
        service_ref = f"service_ref_{current_time}"
        setattr(Service, service_ref, self)
        return Dashboard(service=service_ref, config=config).show()

    def __get_token(self):
        """
        Get token. If authentication object is used to initialize
        the service object, retrieve corresponding user token.
        """
        try:
            if not pydash.is_empty(self.token):
                return self.token
            elif not pydash.is_empty(self.auth):
                return self.auth.get_token()
        except:
            pass
        return None

    def get_service_endpoint(self, key=None):
        """
        Get REST endpoint for the connected project.
        Endpoints are composed from base project url and routes for
        specific requests.

        Parameters
        -------
        key : str
            Name of the specific request. Mapping to routes is stored in
            a dictionary `SERVICE_ENDPOINTS` in `constants.py`.

        """
        dns_name = DNS_NAME
        if self.host is not None:
            dns_name = self.host
        return (
            f"{dns_name}:{self.port}/" + self.project + SERVICE_ENDPOINTS.get(key, "")
        )

    def get_base_payload(self):
        """
        Get the base payload for any REST request which includes the authentication token.
        """
        return {"token": self.__get_token()}

    def get_project_info(self):
        return {"id": self.get_service_endpoint(), "project_name": self.project}

    def get_schemas(self):
        """
        Get schema object for the connected project.
        """
        return Schema(service=self)

    def get_statistics(self):
        """
        Get the statistics object for the project which supports
        calculations in the management dashboard.
        """
        return Statistic(service=self)

    def get_users_by_uids(self, uids: list = []):
        """
        Get user names by their unique IDs.
        Parameters
        -------
        uids : list
            list of unique user IDs.
        """
        if len(uids) > 0:
            path = self.get_service_endpoint("get_users_by_uids")
            payload = self.get_base_payload()
            payload.update({"uids": uids})
            response = get_request(path, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(response.text)
        return {}

    def get_annotator(self):
        """
        Get annotator's own name and user ID.
        The back-end service distinguishes annotator by the
        token or auth object used to initialize the connection.
        """
        if pydash.is_empty(self.user):
            token = self.token
            if self.auth is not None:
                token = self.auth.get_token()
            if not pydash.is_empty(token):
                path = self.get_service_endpoint("get_user")
                payload = self.get_base_payload()
                response = post_request(path, json=payload)
                if response.status_code == 200:
                    parsed_result = response.json()
                else:
                    raise Exception(response.text)
            self.user = {
                "name": parsed_result.get("username"),
                "user_id": parsed_result.get("user_id"),
            }
        return self.user

    def search(
        self,
        limit=DEFAULT_LIST_LIMIT,
        skip=0,
        uuid_list=None,
        keyword=None,
        regex=None,
        record_metadata_condition=None,
        annotator_list=None,
        label_condition=None,
        label_metadata_condition=None,
        verification_condition=None,
    ):
        """
        Search the back-end database based on user-provided predicates.
        Parameters
        ------
        limit: int
            The limit of returned records in the subest.
        skip: int
            skip index of returned subset
            (excluding the first `skip` rows from the raw results ordered by importing order).
        uuid_list: list
            list of record uuids to filter on
        keyword: str
            Term for exact keyword searches.
        regex: str
            Term for regular expression searches.
        record_metadata_condition: dict
            {"name": # name of the record-level metadata to filter on
            "opeartor": "=="|"<"|">"|"<="|">="|"exists",
            "value": # value to complete the expression}
        annotator_list: list
            list of annotator names to filter on
        label_condition: dict
            Label condition of the annotation.
            {"name": # name of the label to filter on
            "opeartor": "=="|"<"|">"|"<="|">="|"exists"|"conflicts",
            "value": # value to complete the expression}
        label_metadata_condition: dict
            Label metadata condition of the annotation.
            Note this can be on different labels than label_condition
            {"label_name": # name of the associated label
            "name": # name of the label-level metadata to filter on
            "operator": "=="|"<"|">"|"<="|">="|"exists",
            "value": # value to complete the expression}
        verification_condition: dict
            verification condition of the annotation.
            {"label_name": # name of the associated label
             "search_mode":"ALL"|"UNVERIFIED"|"VERIFIED"}

        Returns
        -------
        subset : Subset
            Subset meeting the search conditions.
        """
        payload = self.get_base_payload()
        filter = {
            "limit": limit,
            "skip": skip,
        }
        if keyword is not None:
            filter["keyword"] = keyword
        if uuid_list is not None:
            filter["uuid_list"] = uuid_list
        if regex is not None:
            filter["regex"] = regex
        if record_metadata_condition is not None:
            filter["record_metadata_condition"] = record_metadata_condition
        if annotator_list is not None:
            filter["annotator_list"] = annotator_list
        if label_condition is not None:
            filter["label_condition"] = label_condition
        if label_metadata_condition is not None:
            filter["label_metadata_condition"] = label_metadata_condition
        if verification_condition is not None:
            filter["verification_condition"] = verification_condition
        payload.update(filter)
        path = self.get_service_endpoint("search")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return Subset(data_uuids=response.json(), service=self)
        else:
            raise Exception(response.text)

    def search_by_job(
        self,
        limit=DEFAULT_LIST_LIMIT,
        skip=0,
        uuid_list=None,
        keyword=None,
        regex=None,
        record_metadata_condition=None,
        job_id=None,
        label_condition=None,
        label_metadata_condition=None,
        verification_condition=None,
    ):
        ret = self.search(
            limit=limit,
            skip=skip,
            uuid_list=uuid_list,
            keyword=keyword,
            regex=regex,
            record_metadata_condition=record_metadata_condition,
            annotator_list=[job_id],
            label_condition=label_condition,
            label_metadata_condition=label_metadata_condition,
            verification_condition=verification_condition,
        )
        return Subset(data_uuids=ret.get_uuid_list(), service=self, job_id=job_id)

    def deprecate_submit_annotations(self, subset=None, uuid_list=[]):
        # To be deprecated. Default to submit annotations as a batch
        """
        Submit annotations for records in a subset to the back-end service database.
        Results are filtered to only include annotations owned by the authenticated
        annotator.

        Parameters
        -------
        subset : Subset
            The subset object containing records and annotations.
        uuid_list : list
            Additional filter. Only subset records whose uuid are in this list
            will be submitted.

        """
        if pydash.is_empty(subset):
            raise Exception("Subset can not be None.")
        annotator_user_id = self.get_annotator()["user_id"]
        client = httpx.AsyncClient(limits=HTTPX_LIMITS, timeout=REQUEST_TIMEOUT_SECONDS)

        async def submit_annotation_by_uuid(uuid):
            annotation_data = subset.get_annotation_by_uuid(uuid)
            if annotation_data is not None:
                payload = self.get_base_payload()
                own = list(
                    filter(
                        lambda annotation: annotation["annotator"] == annotator_user_id,
                        annotation_data["annotation_list"],
                    )
                )
                payload.update({"labels": {} if len(own) == 0 else own[0]})
                path = self.get_service_endpoint("set_annotations").format(uuid=uuid)
                try:
                    response = await client.post(path, json=payload)
                    if response.status_code == 200:
                        return response.json()
                    else:
                        return {"uuid": uuid, "error": response.text}
                except httpx.TimeoutException:
                    return {"uuid": uuid, "error": "408 Request Timeout"}
                except Exception as e:
                    return {"uuid": uuid, "error": str(e)}

        async def main():
            return await asyncio.gather(
                *[submit_annotation_by_uuid(uuid=uuid) for uuid in uuid_list]
            )

        return asyncio.run(main())

    def submit_annotations(self, subset=None, uuid_list=[]):
        """
        Submit annotations for a batch of records in a subset to the back-end service database.
        Results are filtered to only include annotations owned by the authenticated
        annotator.

        Parameters
        -------
        subset : Subset
            The subset object containing records and annotations.
        uuid_list : list
            Additional filter. Only subset records whose uuid are in this list
            will be submitted.

        """
        if pydash.is_empty(subset):
            raise Exception("Subset can not be None.")
        client = httpx.AsyncClient(limits=HTTPX_LIMITS, timeout=REQUEST_TIMEOUT_SECONDS)

        async def submit_annotation_by_uuid_batch(uuids):
            payload = self.get_base_payload()
            annotator_user_id = self.get_annotator()["user_id"]
            annotation_list = []

            for uuid in uuids:
                annotation_data = subset.get_annotation_by_uuid(uuid)
                if annotation_data is not None:
                    own = list(
                        filter(
                            lambda annotation: annotation["annotator"]
                            == annotator_user_id,
                            annotation_data["annotation_list"],
                        )
                    )
                    own_annotation = {
                        "record_uuid": uuid,
                        "labels": {} if len(own) == 0 else own[0],
                    }
                    annotation_list.append(own_annotation)

            if annotation_list:
                parameters = {"annotation_list": annotation_list}
                payload.update(parameters)
                path = self.get_service_endpoint("submit_annotations_batch")
                try:
                    response = await client.post(path, json=payload)
                    if response.status_code == 200:
                        return response.json()
                    else:
                        return [
                            {"uuid": uuid, "error": response.text} for uuid in uuids
                        ]
                except httpx.TimeoutException:
                    return [
                        {"uuid": uuid, "error": "408 Request Timeout"} for uuid in uuids
                    ]
                except Exception as e:
                    return [{"uuid": uuid, "error": str(e)} for uuid in uuids]
            else:
                return []

        async def main():
            index = 0
            batches = []
            while index < len(uuid_list):
                chunk = uuid_list[index : index + BATCH_SIZE]
                index += BATCH_SIZE
                batches.append(chunk)
            # results is a list of list(s)
            results = await asyncio.gather(
                *[submit_annotation_by_uuid_batch(uuids=batch) for batch in batches]
            )
            # flatten_concatenation
            ret = []
            for result in results:
                ret += result
            return ret

        return asyncio.run(main())

    def get_reconciliation_data(self, uuid_list=[]):
        if pydash.is_empty(uuid_list):
            return []
        BATCH_SIZE = 45
        # making sure the request URL doesn't exceed the 2048 characters limitation for certain browsers
        index = 0
        result = []
        while index < len(uuid_list):
            uuids = []
            counter = 0
            while index < len(uuid_list) and counter < BATCH_SIZE:
                counter += 1
                uuids.append(uuid_list[index])
                index += 1
            payload = self.get_base_payload()
            payload.update({"uuid_list": uuids})
            response = get_request(
                self.get_service_endpoint("get_reconciliation_data"), json=payload
            )
            if response.status_code == 200:
                result += response.json()
            else:
                raise Exception(response.text)
        return result

    def import_data_url(self, url="", file_type="csv", column_mapping={}):
        """
        Import data from a public url, currently only supporting csv files.
        Each row corresponds to a data record. The file needs at least two columns:
        one with a unique id for each row, and one with the raw data content.

        Parameters
        ----
        url : str
            Public url for csv file
        file_type : str
            Currently only supporting type 'CSV'
        column_mapping : dict
            Dictionary with fields `id` specifying id column name, and `content` specifying
            content column name. For example, with a csv file with two columns `index` and `tweet`:
            ```json
            --8<-- "docs/assets/code/column_mapping/basic.json"
            ```
        """
        payload = self.get_base_payload()
        payload.update(
            {"url": url, "file_type": file_type, "column_mapping": column_mapping}
        )
        path = self.get_service_endpoint("post_data")
        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(response.text)

    def import_data_df(self, df, column_mapping={}):
        """
        Import data from a pandas DataFrame.
        Each row corresponds to a data record. The dataframe needs at least two columns:
        one with a unique id for each row, and one with the raw data content.

        Parameters
        ----
        df : DataFrame
            Qualifying dataframe
        column_mapping : dict
            Dictionary with fields `id` specifying id column name, and `content` specifying
            content column name. Using a dataframe, users can import metadata at the same time.
            For example, with a csv file with two columns `index` and `tweet`, and a column `location`:
            ```json
            --8<-- "docs/assets/code/column_mapping/metadata.json"
            ```
            metadata with name `location` will be created for all imported data records.

        """

        if not isinstance(df, pd.DataFrame):
            raise Exception("df needs to be a valid pandas dataframe")
        filtered_columns = []
        if pydash.is_empty(column_mapping):
            # defult mapping ,check for columns "id" and "content"
            if "id" in df.columns and "content" in df.columns:
                filtered_columns.extend(["id", "content"])
                column_mapping = {"id": "id", "content": "content"}
            else:
                raise Exception(
                    "Needs to provide valid column_mapping, or columns with name 'id' and 'content'."
                )
        else:
            if (
                column_mapping["id"] in df.columns
                and column_mapping["content"] in df.columns
            ):
                filtered_columns.extend(
                    [column_mapping["id"], column_mapping["content"]]
                )
            else:
                raise Exception(
                    "Needs to provide valid column_mapping with fields 'id' and 'content'."
                )
        if "metadata" in column_mapping:
            filtered_columns.append(column_mapping["metadata"])

        # filter columns to only send necessary columns.
        # fill nan values to make json serializable.

        df = df[filtered_columns].fillna("NaN")

        if len(df) > 1000:
            warnings.warn(
                "Try using 'import_data_url' for import; importing large datasets DataFrame is not advised.",
                RuntimeWarning,
            )
        payload = self.get_base_payload()
        payload.update(
            {
                "file_type": "DF",
                "df_dict": df.to_dict(orient="records"),
                "column_mapping": column_mapping,
            }
        )
        path = self.get_service_endpoint("post_data")
        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(response.text)

    def export(self):
        """
        Exporting function.
        Returns
        ----
        export_df : DataFrame
            A pandas dataframe with columns
            `'data_id', 'content', 'annotator',
            'label_name', 'label_value'` for all records in the project

        """
        payload = self.get_base_payload()
        path = self.get_service_endpoint("export_data")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return pd.DataFrame(
                json.loads(response.text),
                columns=[
                    "data_id",
                    "content",
                    "annotator",
                    "label_name",
                    "label_value",
                ],
            )
        else:
            raise Exception(response.text)

    def set_verification_data(self, verify_list=[]):
        result = []
        for each in verify_list:
            uuid = each["uuid"]
            annotator_id = each["annotator_id"]
            label_level = each["labels"][0]["label_level"]
            label_name = each["labels"][0]["label_name"]
            payload = self.get_base_payload()
            payload.update(
                {
                    "uuid": uuid,
                    "labels": each["labels"],
                    "label_level": label_level,
                    "label_name": label_name,
                    "annotator_id": annotator_id,
                }
            )
            path = self.get_service_endpoint("set_verification_data").format(uuid=uuid)
            response = post_request(path, json=payload)
            if response.status_code == 200:
                result.append(response.json())
            else:
                result.append({"uuid": uuid, "error": response.text})
        return result

    def set_reconciliation_data(self, recon_list=[]):
        result = []
        for each in recon_list:
            uuid = each["uuid"]
            payload = self.get_base_payload()
            payload.update(
                {"uuid": uuid, "labels": each["labels"], "annotator": "reconciliation"}
            )
            path = self.get_service_endpoint("set_reconciliation_data").format(
                uuid=uuid
            )
            response = post_request(path, json=payload)
            if response.status_code == 200:
                result.append(response.json())
            else:
                result.append({"uuid": uuid, "error": response.text})
        return result

    def __batch_update_metadata(self, meta_name, metadata_list):
        """
        Update database and set metadata in batch.
        Parameters
        ----
        meta_name : str
            Name of metadata
        metadata_list : list[dict]
            List of dictionary with fields `uuid` specifying uuid of the
            source data record, and `value` for the metadata value to store.
        """
        payload = self.get_base_payload()
        payload.update(
            {
                "record_meta_name": meta_name,
                "metadata_list": metadata_list,
            }
        )
        path = self.get_service_endpoint("batch_update_metadata")
        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(response.text)

    def set_metadata(self, meta_name, func, batch_size=500):
        """
        Set metadata for all records in the back-end database,
        based on user-defined function for metadata calculation.
        Parameters
        ------
        meta_name : str
            Name of the metadata. Will be used to identify and query the metadata.
        func : function(raw_content)
            Function which takes input the raw data content and returns the
            corresponding metadata (int, string, vectors...).
        batch_size : int
            Batch size for back-end database updates.

        Example
        ----
        ```python
        --8<-- "docs/assets/code/set_metadata.py"
        ```
        """
        n = self.get_statistics().get_label_progress()["total"]
        set_count = 0
        batch_number = math.ceil(float(n) / batch_size)

        with tqdm(
            total=batch_number, leave=True, desc="Metadata batches processed:"
        ) as tq:
            for i in range(batch_number):
                s = self.search(limit=batch_size, skip=i * batch_size)
                data_batch = s.get_view_record()
                for item in data_batch:
                    item["value"] = func(item["record_content"])

                res = self.__batch_update_metadata(meta_name, data_batch)
                set_count += int(res)
                tq.update()
        return f"Set metadata '{meta_name}' for {set_count} data record{'s' if set_count > 1 else ''}."

    def get_assignment(self, annotator=None, latest_only=False):
        """
        Get workload assignment for annotator.
        Parameters
        ------
        annotator : str
            User ID to query. If set to None, use ID of auth token holder.
        latest_only : bool
            If true, return only the last assignment for the user.
            Else, return the set of all assigned records.
        """
        payload = self.get_base_payload()
        payload["annotator"] = annotator
        payload["latest_only"] = latest_only
        path = self.get_service_endpoint("get_assignment")
        response = get_request(path, json=payload)

        unique_assignments = set({})
        if response.status_code == 200:
            for res in response.json():
                unique_assignments.update(res["uuid_list"])
            return Subset(data_uuids=list(unique_assignments), service=self)

        else:
            raise Exception(response.text)
