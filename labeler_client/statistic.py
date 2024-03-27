import pydash

from labeler_client.helpers import get_request


class Statistic:
    """
    The Statistic class defines methods which show basic statistics
    of the labeling project. Mostly used to back views in the monitoring dashboard.

    Attributes
    ----------
    __service : Service
        Service object for the connected project.
    """

    def __init__(self, service) -> None:
        self.__service = service

    def get_label_progress(self):
        """Get the overall label progress.

        Returns
        -------
        response : dict
            A dictionary with fields `total` showing total number for data records,
            and `annotated` showing number of records with *any* label from at least
            one annotator.
        """
        payload = self.__service.get_base_payload()
        path = self.__service.get_service_endpoint("get_label_progress")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_label_distributions(self, label_name: str = None):
        """Gets class distributions for specified label.
        If multiple annotators labeled the same record, aggregate using
        `majority vote`.

        Parameters
        ----------
        label_name : str
            Name of label as specified in the schema.

        Returns
        ---------
        response : dict
            A dictionary showing aggregated class frequencies. Example:
            `{'neg': 60, 'neu': 14, 'pos': 27, 'tied_annotations': 3}`.
            `tied_annotation` counts numbers of record when there's more than
            majority voted classes.

        """
        if pydash.is_empty(label_name):
            raise Exception("label_name can not be None or empty.")
        payload = self.__service.get_base_payload()
        payload.update({"label_name": label_name})
        path = self.__service.get_service_endpoint("get_label_distribution")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_annotator_contributions(self):
        """Get contributions of annotators in terms of records labeled.

        Returns
        ---------
        response : dict
            A dictionary where keys are annotator IDs and values are total numbers of annotated
            records by each annotator.
        """
        payload = self.__service.get_base_payload()
        path = self.__service.get_service_endpoint("get_annotator_contribution")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_annotator_agreements(self, label_name: str = None):
        """Gets pairwise agreement score between all contributing
        annotators to the project, on the specified label. The
        default agreement calculation method is
        [`cohen_kappa`](https://towardsdatascience.com/inter-annotator-agreement-2f46c6d37bf3).

        Parameters
        ----------
        label_name : str
            Name of label as specified in the schema.

        Returns
        ---------
        response : dict
            A dictionary where keys are pairs of annotator IDs, and values are their agreement scores.
            The higher the scores are, the more frequent the pairs of annotators agree.

        """
        if pydash.is_empty(label_name):
            raise Exception("label_name can not be None or empty.")
        payload = self.__service.get_base_payload()
        payload.update({"label_name": label_name})
        path = self.__service.get_service_endpoint("get_annotator_agreement")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_embeddings(self, label_name: str = None, embed_type: str = None):
        """Returns 2-dimensional
        [TSNE](https://en.wikipedia.org/wiki/T-distributed_stochastic_neighbor_embedding)
        projection of the text embedding for data records,
        together with their aggregated labels (using majority votes).
        Used for projection view in the monitoring dashboard.

        Parameters
        ----------
        label_name : str
            Name of label as specified in the schema.
        embed_type : str
            the meta_name for the specified embedding


        Returns
        ---------
        response : dict
            A dictionary with fields `agg_label` showing aggregated class label,
            `x_axis` and `y_axis` showing projected 2d coordinates.
        """
        if pydash.is_empty(label_name):
            raise Exception("'label_name' can not be None or empty.")
        elif pydash.is_empty(embed_type):
            raise Exception("'embed_type' can not be None or empty.")
        payload = self.__service.get_base_payload()
        payload.update({"label_name": label_name})
        path = self.__service.get_service_endpoint("get_embeddings").format(
            embed_type=embed_type
        )
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)
