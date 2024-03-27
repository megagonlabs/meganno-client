import json
import time
from re import S

import pydash

from labeler_client.helpers import get_request, post_request


class Subset:
    """
    The Subset class is used to represent a group of data records

    Attributes
    ----------
    __data_uuids : list
        List of unique identifiers of data records in the subset.
    __service : Service
        Connected backend service
    __my_annotation_list : list
        Local cache of the record and annotation view of the subset owned by
        service.annotator_id. with all possible metadata.

    """

    def __init__(self, service, data_uuids=[], job_id=None):
        """
        Init function

        Parameters
        -------
        service : Service
            Service-class object identifying the connected
            backend service and corresponding data storage
        data_uuids : list
            List of data uuid's to be included in the subset
        """
        self.__data_uuids = data_uuids
        self.__service = service
        # TODO: to be removed after UI changes
        # in verifcation UI, instead of calling value() for subset owned
        # by job_id, on subset owned by user, call value(annotator_list =[job_id])
        self.job_id = job_id
        if job_id is None:
            self.annotator_id = service.get_annotator()["user_id"]
        else:
            self.annotator_id = job_id
        self.__my_annotation_list = self.__get_annotation_list(
            annotator_list=[self.annotator_id]
        )

    def __get_annotator_id(self):
        if self.job_id is not None:
            return self.job_id
        return self.annotator_id

    def get_verification_annotations(
        self,
        label_name=None,
        label_level=None,
        annotator: str = None,
        verifiers: list = None,
        verified_status: str = None,
    ):
        # signature names to be changed
        # verifiers --> verifier_filter
        # verified_status --> status_filter
        if pydash.is_empty(label_name):
            raise Exception("label_name cannot be None or empty.")
        if pydash.is_empty(label_level):
            raise Exception("label_level cannot be None or empty.")
        payload = self.__service.get_base_payload()
        payload.update(
            {
                "uuid_list": self.__data_uuids,
                "label_name": label_name,
                "label_level": label_level,
                "annotator": annotator,
                "verifier_filter": verifiers,
                "status_filter": verified_status,
            }
        )
        path = self.__service.get_service_endpoint("get_view_verification")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_uuid_list(self):
        """
        Get list of unique identifiers for all records in the subset.

        Returns
        -------
        __data_uuids : list
            List of data uuids included in Subset
        """
        return self.__data_uuids

    def __get_annotation_list(self, annotator_list: list = None):
        """
        Internal function, used by UI only.
        Returns all annotation list for all data records in the subset.


        Parameters
        ------
        annotator_list: list
            If None, only return data and annotation by all annotators
        Returns
        ------
        subset_annotation_list : list
            A list of data and annotation for each data record in the subset.
                For each item in the list, `uuid` uniquely identifies the data record,
                , `data` field stores raw content, and metadata stores additional information
                about the record if `__meta_names` is set for the subset object.
                `annotation_list` stores all annotations (by different annotators) and contains
                two lists 'labels_record' and 'labels_span' for labels at different level.


            Example
            ---------
            Example annotation list with for a single-record subset:
            ```json
            --8<-- "docs/assets/code/annotation_list.json"
            ```
        """

        payload = self.__service.get_base_payload()
        update_cache = (
            True
            if len(annotator_list) == 1 and annotator_list[0] == self.annotator_id
            else False
        )
        payload.update(
            {"uuid_list": self.__data_uuids, "annotator_list": annotator_list}
        )
        path = self.__service.get_service_endpoint("get_annotations")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            ret = response.json()
            if update_cache:
                self.__my_annotation_list = ret
            return ret
        else:
            raise Exception(response.text)

    def value(self, annotator_list: list = None):
        """
        Check for cached data and annotations of service owner,
        or retrieve for other annotators (not cached).
        Parameters
        ----------
        annotator_list : list
            if None, retrieve cached own annotator.
            else, fetch live annotation from others.
        Returns
        -------
        subset_annotation_list : list
            See `__get_annotation_list` for description and example.
        """

        # TODO: default value None should return for all annotators
        # To retrieve own annotations. passin own id.
        # leave unchanged untile UI changes.
        if annotator_list is None:
            return self.__my_annotation_list
        else:
            return self.__get_annotation_list(annotator_list=annotator_list)

    def get_view_record(
        self,
        record_id=None,
        record_content=None,
        record_meta_names=None,
    ):
        payload = self.__service.get_base_payload()
        payload.update({"uuid_list": self.__data_uuids})
        if record_id:
            payload.update({"record_id": record_id})
        if record_content:
            payload.update({"record_content": record_content})
        if record_meta_names:
            payload.update({"record_meta_names": record_meta_names})
        path = self.__service.get_service_endpoint("get_view_record")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_view_annotation(
        self,
        annotator_list=None,
        label_names=None,
        label_meta_names=None,
    ):
        payload = self.__service.get_base_payload()
        payload.update({"uuid_list": self.__data_uuids})
        if annotator_list is not None:
            payload.update({"annotator_list": annotator_list})
        if label_names is not None:
            payload.update({"label_names": label_names})
        if label_meta_names is not None:
            payload.update({"label_meta_names": label_meta_names})
        path = self.__service.get_service_endpoint("get_view_annotation")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_view_verification(
        self,
        label_name=None,
        label_level=None,
        annotator=None,
        verifier_filter=None,
        status_filter=None,
    ):
        # TODO: replace get_verification_annotations
        payload = self.__service.get_base_payload()
        payload.update({"uuid_list": self.__data_uuids})
        if label_name is not None:
            payload.update({"label_name": label_name})
        if label_level is not None:
            payload.update({"label_level": label_level})
        if annotator is not None:
            payload.update({"annotator": annotator})
        if verifier_filter is not None:
            payload.update({"verifier_filter": verifier_filter})
        if status_filter is not None:
            payload.update({"status_filter": status_filter})

        path = self.__service.get_service_endpoint("get_view_verification")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_annotation_by_uuid(self, uuid):
        """
        Returns the annotation for a particular data record (specified by uuid)

        Parameters
        ----------
        uuid : str
            the uuid for the data record specified by user

        Returns
        -------
        annotation : dict
            Annotation for specified data record if it exists else None
        """
        for annotation in self.__my_annotation_list:
            if annotation["uuid"] == uuid:
                return annotation
        return None

    def show(self, config={}):
        """
        Visualize the current subset in an in-notebook annotation widget.

        Development note: initializing an Annotation widget, creating unique reference to
        the associated subset and service.

        Parameters
        ----------
        config : dict
            Configuration for default view of the widget.

                - view : "single" | "table", default "single"
                - mode : "annotating" | "reconciling", default "annotating"
                - title: default "Annotation"
                - height: default 300 (pixels)
        """
        from labeler_ui import Annotation

        current_time = int(time.time())
        # Create a Subset class-level reference to the subset and service object
        # used to init the annotation widget. Thus the UI widget will always have
        # a referring handle to the corresponding communication channel.
        subset_ref = "subset_ref_{}".format(current_time)
        service_ref = "service_ref_{}".format(current_time)
        # Set class variables
        config.update({"verifying_id": self.__get_annotator_id()})
        setattr(Subset, subset_ref, self)
        setattr(Subset, service_ref, self.__service)
        return Annotation(subset=subset_ref, service=service_ref, config=config).show()

    def set_annotations(self, uuid=None, labels=None):
        """Sets the annotation for a particular data record with the specified label

        Parameters
        ----------
        uuid : str
            the uuid for the data record specified by user
        labels : dict
            The labels for the data record at record and span level, with the following structure:

                - "labels_record" : list
                    A list of record-level labels
                - "labels_span" : list
                    A list of span-level labels

                Examples
                -------

                Example of setting an annotation with the desired record and span level labels:
                ```json
                --8<-- "docs/assets/code/set_annotations.json"
                ```

        Raises
        ------
        Exception
            If uuid or labels is None

        Returns
        -------
        labels : dict
            Updated labels for uuid annotated by user
        """
        annotator_user_id = self.annotator_id
        if pydash.is_empty(uuid):
            raise Exception("UUID can not be None.")
        elif pydash.is_empty(labels):
            raise Exception(
                f"Labels can not be None. For clearing annotations, use {{}}."
            )
        labels["annotator"] = annotator_user_id
        added = False
        index = -1
        for datapoint_idx, datapoint in enumerate(self.__my_annotation_list):
            if datapoint["uuid"] == uuid:
                index = datapoint_idx
                for annotation_idx, annotation in enumerate(
                    datapoint["annotation_list"]
                ):
                    if annotation["annotator"] == annotator_user_id:
                        added = True
                        self.__my_annotation_list[datapoint_idx]["annotation_list"][
                            annotation_idx
                        ] = labels
        if not added and index != -1 and index < len(self.__my_annotation_list):
            self.__my_annotation_list[index]["annotation_list"].append(labels)
        return labels

    def get_reconciliation_data(self, uuid_list=None):
        """Returns the list of reconciliation data for all data entries specified by user.
        The reconciliation data for one data record consists of the annotations for it by all annotators

        Parameters
        ----------
        uuid_list : list
            list of uuid's provided by user.
            If None, use all records in the subset

        Returns
        -------
        reconciliation_data_list : list
            List of reconciliation data for each uuid with the following keys: `annotation_list` which specifies all the annotations for the uuid, `data` which contains the raw data specified by the uuid, `metadata` which stores additional information about the data, `tokens` <tmp>, and the `uuid` of the data record
            Full Example:
            ```json
            --8<-- "docs/assets/code/reconciliation_data.json"
            ```
        """
        if uuid_list is None:
            uuid_list = self.__data_uuids
        return self.__service.get_reconciliation_data(uuid_list=uuid_list)

    def suggest_similar(self, record_meta_name, limit=3):
        """For each data record in the subset, suggest more similar data records
            by retriving the most similar data records from the pool, based on
            metadata(e.g., embedding) distance.
        Parameters
        ----------
        record_meta_name : str
            The meta-name eg. "bert-embedding" for which the similarity is calculated upon.
        limit : int
            The number of matching/similar records desired to be returned. Default is 3

        Raises
        ------
        Exception
            If response code is not successful

        Returns
        -------
        subset : Subset
            A subset of similar data entries
        """
        payload = self.__service.get_base_payload()
        payload.update(
            {
                "uuid_list": self.__data_uuids,
                "record_meta_name": record_meta_name,
                "limit": limit,
            }
        )
        path = self.__service.get_service_endpoint("suggest_similar_annotations")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            suggested_uuids = list(set(json.loads(response.text)))
            return Subset(service=self.__service, data_uuids=suggested_uuids)
        else:
            raise Exception(response.text)

    def assign(self, annotator):
        """
        Assign the current subset as payload to an annotator.
        Parameters
        ----------
        annotator : str
            Annotator ID.
        """
        if pydash.is_empty(annotator):
            raise Exception("Annotator cannot be None or empty.")
        payload = self.__service.get_base_payload()
        payload.update(
            {
                "subset_uuid_list": self.__data_uuids,
                "annotator": annotator,
            }
        )
        path = self.__service.get_service_endpoint("get_assignment")

        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    # overlading subset operation with set algebra
    def __or__(self, other):
        """
        Computation overloading for the set "or" operator |.
        With Subset A and B, C = A | B will return a new Subset object
        with a uuid_list which unions data records in A and B.
        """
        return Subset(
            service=self.__service,
            data_uuids=list(set(self.get_uuid_list()) | set(other.get_uuid_list())),
        )

    def union(self, other):
        return Subset.__or__(self, other)

    def __and__(self, other):
        """
        Computation overloading for the set "and" operator &.
        With Subset A and B, C = A & B will return a new Subset object
        with a uuid_list which intersects data records in A and B.
        """
        return Subset(
            service=self.__service,
            data_uuids=list(set(self.get_uuid_list()) & set(other.get_uuid_list())),
        )

    def intersection(self, other):
        return Subset.__and__(self, other)

    def __sub__(self, other):
        return Subset(
            service=self.__service,
            data_uuids=list(set(self.get_uuid_list()) - set(other.get_uuid_list())),
        )

    def difference(self, other):
        return Subset.__sub__(self, other)
