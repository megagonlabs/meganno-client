import json
import os

from meganno_client.constants import VALID_PROVIDERS
from meganno_client.helpers import get_request, post_request
from meganno_client.llm_jobs import OpenAIJob
from meganno_client.prompt import PromptTemplate
from meganno_client.service import Service
from meganno_client.subset import Subset


class Controller:
    """
    The Controller class manages agents and runs agent jobs.
    """

    def __init__(self, service, auth):
        """
        Init function

        Parameters
        ----------
        service : Service
            Labeler service object for the connected project.
        auth : Authentication
            Labeler authentication object.
        """
        self.__service = service
        self.__auth = auth

    def list_agents(
        self,
        created_by_filter=None,
        provider_filter=None,
        api_filter=None,
        show_job_list=False,
    ):
        """
        Get the list of registered agents by their issuer IDs.

        Parameters
        ----------
        created_by_filter : list, optional
            List of user IDs to filter agents, by default None (if None, list all)
        provider_filter: str
            Returns agents with the specified provider eg. openai
        api_filter: list(str)
            Returns agents with the specified api eg. completion
        show_job_list: bool
            if True, also return the list uuids of jobs of the agent.

        Returns
        -------
        list
            A list of agents that are created by specified issuers.
        """
        payload = self.__service.get_base_payload()
        payload.update(
            {
                "created_by_filter": created_by_filter,
                "provider_filter": provider_filter,
                "api_filter": api_filter,
                "show_job_list": show_job_list,
            }
        )
        path = self.__service.get_service_endpoint("get_agents")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def list_jobs(self, filter_by, filter_values, show_agent_details=False):
        """
        Get the list of jobs with querying filters.

        Parameters
        ----------
        filter_by : str
            Filter options. Must be ["agent_uuid" | "issued_by" | "uuid"] | None
        filter_values : list
            List of uuids of entity specified in 'filter_by'
        show_agent_details : bool, optional
            If True, return agent configuration, by default False

        Returns
        -------
        list
            A list of jobs that match given filtering criteria.
        """
        payload = self.__service.get_base_payload()
        payload.update(
            {
                "details": show_agent_details,
                "filter_by": filter_by,
                "filter_values": filter_values,
            }
        )
        path = self.__service.get_service_endpoint("get_jobs")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def list_jobs_of_agent(self, agent_uuid, show_agent_details=False):
        """
        Get the list of jobs of a given agent.

        Parameters
        ----------
        agent_uuid : str
            Agent uuid
        show_agent_details : bool, optional
            If True, return agent configuration, by default False

        Returns
        -------
        list
            A list of jobs of a given agent
        """
        payload = self.__service.get_base_payload()
        payload.update({"details": show_agent_details})
        path = self.__service.get_service_endpoint("get_jobs_of_agent").format(
            agent_uuid=agent_uuid
        )
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def register_agent(self, model_config, prompt_template_str, provider_api):
        """
        Registers an agent with backend service.

        Parameters
        ----------
        model_config : dict
            Model configuration object
        prompt_template_str : str
            Serialized prompt template
        provider_api : str
            Name of provider and corresponding api eg. 'openai:chat'

        Returns
        -------
        dict
            object with unique agent id.
        """
        payload = self.__service.get_base_payload()
        payload.update(
            {
                "model_config": model_config,
                "prompt_template": prompt_template_str,
                "provider_api": provider_api,
            }
        )
        path = self.__service.get_service_endpoint("register_agent")
        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def persist_job(self, agent_uuid, job_uuid, label_name, annotation_uuid_list):
        """
        Given annoations for a subset, persit as a job for the project.

        Parameters
        ----------
        agent_uuid : str
            Agent uuid
        job_uuid : str
            Job uuid
        label_name : str
            Label name used for annotation
        annotation_uuid_list : list
            List of uuids of records that have valid annotations from the job

        Returns
        -------
        dict
            Object with job uuid and annotation count
        """
        print("\nPersisting the job :::")
        print("\nJob ID: {}".format(job_uuid))

        payload = self.__service.get_base_payload()
        payload.update(
            {
                "label_name": label_name,
                "annotation_uuid_list": annotation_uuid_list,
            }
        )
        path = self.__service.get_service_endpoint("set_job").format(
            agent_uuid=agent_uuid, job_uuid=job_uuid
        )
        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def create_agent(self, model_config, prompt_template, provider_api="openai:chat"):
        """
        Validates model configs and registers a new agent.
        Returns new agent's uuid.

        Parameters
        ----------
        model_config : dict
            Model configuration object
        prompt_template : str
            PromptTemplate object
        provider_api : str
            Name of provider and corresponding api eg. 'openai:chat'

        Returns
        -------
        agent_uuid : str
            Agent uuid
        """
        # validate configs
        api_provider, api_name = provider_api.split(":")
        if (
            api_provider not in VALID_PROVIDERS
            or api_name not in VALID_PROVIDERS[api_provider]
        ):
            raise Exception("LLM not supported")
        if api_provider == "openai":
            model_config = OpenAIJob.validate_model_config(model_config, api_name)
        # calls register_agent (with model_config, template, provider_api to serializer)
        agent = self.register_agent(
            model_config, prompt_template.get_template(), provider_api
        )  # service endpoint
        agent_uuid = agent["agent_uuid"]

        print("Agent registered :::")
        print("\nAgent ID: {}".format(agent_uuid))
        print("\nModel config: {}".format(model_config))
        print("\nAPI Provider: {}".format(provider_api))
        print("\nPrompt template: ")
        print("\033[34m{}\x1b[0m".format(prompt_template.get_template()))
        return agent_uuid

    def get_agent_by_uuid(self, agent_uuid):
        """
        Returns agent model configuration, prompt template, and creator id of specified agent.

        Parameters
        ----------
        agent_uuid : str
            Agent uuid

        Returns
        -------
        dict
            A dict containing agent details.
        """
        agents = self.list_my_agents()
        for a in agents:
            if a["uuid"] == agent_uuid:
                return {
                    "agent_uuid": a["uuid"],
                    "model_config": json.loads(a["model_config"]),
                    "prompt_template": a["prompt_template"],
                    "provider_api": a["provider_api"],
                    "created_by": a["created_by"],
                }
        return None

    def list_my_agents(self):
        """
        Get the list of registered agents by me.

        Returns
        -------
        agents : list
            A list of agents that are created by me.
        """
        annotator_id = self.__service.get_annotator()["user_id"]
        agents = self.list_agents([annotator_id])  # service endpoint
        return agents

    def list_my_jobs(self, show_agent_details=False):
        """
        Get the list of jobs of issued by me.

        Parameters
        ----------
        show_agent_details : bool, optional
            If True, return agent configuration, by default False

        Returns
        -------
        jobs : list
            A list of jobs of issued by me.
        """
        filter_by = "issued_by"
        annotator_id = self.__service.get_annotator()["user_id"]
        filter_values = [annotator_id]
        jobs = self.list_jobs(
            filter_by, filter_values, show_agent_details
        )  # service endpoint
        return jobs

    def run_job(
        self,
        agent_uuid,
        subset,
        label_name,
        batch_size=1,
        num_retrials=2,
        label_meta_names=[],
        fuzzy_extraction=False,
    ):
        """
        Creates, runs, and persists an LLM annotation job with given agent and subset.

        Parameters
        ----------
        agent_uuid : str
            Uuid of an agent to be used for the job
        subset : Subset
            [Megagon-only] Labeler Subset object to be annotated in the job
        label_name : str
            Label name used for annotation
        batch_size : int
            Size of batch to each Open AI prompt
        num_retrials : int
            Number of retrials to OpenAI in case of failure in response
        label_meta_names: list
            list of label metadata names to be set
        fuzzy_extraction: bool
            Set to True if fuzzy extraction desired in post processing
        Returns
        -------
        job_uuid : str
            Job uuid
        """
        # if self.project and self.agent_token:
        #     self.create_service()
        # else:
        #     raise Exception("Service cannot be created as project and token not provided")

        label_schema = self.__service.get_schemas().value(active=True)[0]["schemas"][
            "label_schema"
        ]
        records = subset.get_view_record()

        agent = self.get_agent_by_uuid(agent_uuid)
        if not agent:
            raise Exception("Agent ID: {} is invalid".format(agent_uuid))
        model_config = agent["model_config"]
        prompt_template = PromptTemplate(
            label_schema=label_schema,
            label_names=[label_name],
            template=agent["prompt_template"],
        )  # todo: read is_json_template
        provider_api = agent["provider_api"]

        print("Job issued :::")
        print("\nAgent ID: {}".format(agent_uuid))
        print("\nModel config: {}".format(model_config))
        print("\nPrompt template: ")
        print("\033[34m{}\x1b[0m".format(prompt_template.get_template()))

        # assumption: api key in env; model config is openai specific
        openai_api_key = os.environ["OPENAI_API_KEY"]
        openai_organization = (
            os.environ["OPENAI_ORGANIZATION"]
            if "OPENAI_ORGANIZATION" in os.environ
            else ""
        )

        # create job class instance
        api_provider, api_name = provider_api.split(":")
        if (
            api_provider in VALID_PROVIDERS
            and api_name in VALID_PROVIDERS[api_provider]
        ):
            if api_provider == "openai":
                if "conf" in label_meta_names:
                    model_config["logprobs"] = True
                llm_job = OpenAIJob(
                    label_schema, label_name, records, model_config, prompt_template
                )
                llm_job.validate_openai_api_key(openai_api_key, openai_organization)
                llm_job.preprocess()
                llm_job.get_llm_annotations(
                    batch_size=batch_size,
                    num_retrials=num_retrials,
                    api_name=api_name,
                    label_meta_names=label_meta_names,
                )
                llm_job.post_process_annotations(fuzzy_extraction=fuzzy_extraction)

        # create job token and service
        job_auth = self.__auth.create_access_token(job=True)
        job_uuid, job_token = job_auth["user_id"], job_auth["token"]
        job_service = Service(
            project=self.__service.project,
            host=self.__service.host,
            port=self.__service.port,
            token=job_token,
        )

        # set annotations and labels for job
        job_subset = Subset(job_service, subset.get_uuid_list(), job_id=job_uuid)
        for uuid, annotation in llm_job.annotations:
            job_subset.set_annotations(uuid, annotation)
        ret = job_service.submit_annotations(
            job_subset, llm_job.uuids_with_valid_annotations
        )

        annotation_uuid_list = []
        for r in ret:
            if "annotation_uuid" in r:
                annotation_uuid_list.append(r["annotation_uuid"])
            elif "error" in r:
                print(
                    f"Invalid response for uuid {r['uuid']}: {r['error']}; annotation not persisted"
                )
            else:
                raise Exception("Invalid responses; annotations not persisted")

        # set job
        if len(annotation_uuid_list) > 0:
            ret = self.persist_job(
                agent_uuid, job_uuid, label_name, annotation_uuid_list
            )
            print("\n", ret)
            return job_uuid
        else:
            print("No valid responses; annotations not persisted")
            return None
