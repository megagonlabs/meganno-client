import json
import queue
import re
import time
from collections import Counter

import jaro
import jsonschema
import numpy as np
import openai
from tabulate import tabulate
from tqdm.notebook import tqdm_notebook

from meganno_client.constants import FUZZY_THRESHOLD
from meganno_client.valid_formats import model_config_options

MAX_TOKEN_LIMIT = 2044


class OpenAIJob:
    """
    The OpenAIJob class handles calls to OpenAI APIs.
    """

    def __init__(
        self,
        label_schema={},
        label_names=[],
        records=[],
        model_config={},
        prompt_template=None,
    ):
        """
        Init function

        Parameters
        ----------
        label_schema : list
            List of label objects
        label_names : list
            List of label names to be used for annotation
        records : list
            List of records in [{'data': , 'uuid': }] format
        model_config : dict
            Parameters for the Open AI model
        prompt_template : str
            Template based on which prompt to OpenAI is prepared for each record
        """
        # (self, service, subset, agent_token, model_config, openai_api_key, openai_organization = ""):
        self.records = records  # list of records in [{'data': , 'uuid': }] format
        self.model_config = model_config
        self.template = prompt_template

        self.uuids_with_valid_annotations = []

        label_dic = {
            label["name"]: {
                "level": label["level"],
                "options": [o["text"] for o in label["options"]],
                "text_to_value": {
                    o["text"].strip().lower(): o["value"] for o in label["options"]
                },
            }
            for label in label_schema
            if label["name"] in label_names
        }
        self.label_dic = label_dic
        self.syntax_errors = []
        self.semantic_errors = []
        self.label_meta_func_map = {
            "length": "get_response_length",
            "conf": "get_openai_conf_score",
        }

    def set_openai_api_key(self, openai_api_key, openai_organization):
        """
        Set the API keys necessary for call to OpenAI API

        Parameters
        ----------
        openai_api_key : str
            OpenAI API key provided by user
        openai_organization : str [optional]
            OpenAI organization key provided by user
        """
        openai.api_key = openai_api_key
        if openai_organization:
            openai.organization = openai_organization

    @staticmethod
    def validate_openai_api_key(openai_api_key, openai_organization):
        """Validate the OpenAI API and organization keys provided by user

        Parameters
        ----------
        openai_api_key : str
            OpenAI API key provided by user
        openai_organization : str [optional]
            OpenAI organization key provided by user

        Raises
        ------
        Exception
            If api keys provided by user are invalid, or if any error in calling OpenAI API

        Returns
        -------
        openai_api_key : str
            OpenAI API key
        openai_organization : str
            OpenAI Organization key
        """
        openai.api_key = openai_api_key
        if openai_organization:
            openai.organization = openai_organization
        # make a dummy call to openai for validation of key
        try:
            openai.Model.list()
        except openai.error.AuthenticationError:
            raise Exception("Invalid Open API Key")
        except openai.error.APIError as e:
            raise Exception("OpenAI API returned an API Error {}".format(e))
        except openai.error.APIConnectionError as e:
            raise Exception("Conncection Error with OpenAI API {}".format(e))
        except openai.error.RateLimitError as e:
            raise Exception("Rate limit error {}".format(e))
        except openai.error.Timeout as e:
            raise Exception("OpenAI API request timed out {}".format(e))
        except openai.error.InvalidRequestError as e:
            raise Exception("Invalid request to OpenAI API {}".format(e))
        except openai.error.ServiceUnavailableError as e:
            raise Exception("OpenAI API service unavailable {}".format(e))
        except Exception as e:
            raise Exception(
                "Unknown error occurred during call to Open AI API {}".format(e)
            )
        return openai_api_key, openai_organization

    @staticmethod
    def validate_model_config(model_config, api_name="chat"):
        """Validate the LLM model config provided by user. Model should be among the models allowed on MEGAnno, and the parameters should match format specified by Open AI

        Parameters
        ----------
        model_config : dict
            Model specifications such as model name, other parameters eg. temperature, as provided by user
        api_name : str
            Name of OpenAI api eg. "chat" or "completion

        Raises
        ------
        Exception
            If model is not among the ones provided by MEGAnno, or if configuration format is incorrect

        Returns
        -------
        model_config : dict
            Model congigurations
        """
        valid_format = model_config_options[api_name]["valid_format"]
        validator = jsonschema.Draft7Validator(valid_format)

        model_config_errors = validator.iter_errors(
            model_config
        )  # get all validation errors

        invalid_config_parameters = []
        for error in model_config_errors:
            param_name = ".".join(error.path)
            param_error_msg = error.message
            print(
                "Invalid model configuration for [{}]: {}".format(
                    param_name, param_error_msg
                )
            )
            invalid_config_parameters.append(param_name)

        if invalid_config_parameters:
            raise ValueError(
                "Model configuration has {} invalid value(s)".format(
                    len(invalid_config_parameters)
                )
            )

        for key in model_config:
            if key not in model_config_options[api_name]["valid_format"]["properties"]:
                print(
                    "Paramater {} is not included in OpenAI Completion API".format(key)
                )

        if "logprobs" not in model_config and api_name == "completions":
            model_config["logprobs"] = 0
        return model_config

    def is_valid_prompt(self, prompt):
        """Validate the prompt generated. It should not exceed the maximum token limit specified by OpenAI.
        We use the approximation 1 word ~ 1.33 tokens

        Parameters
        ----------
        prompt : str
            Prompt generated for OpenAI based on template and the record data

        Returns
        -------
        bool
            True if prompt is valid, False otherwise
        """
        num_words = len(prompt.split())
        num_tokens = round(num_words * 1.33)
        if num_tokens > MAX_TOKEN_LIMIT:
            return False
        return True

    def generate_prompts(self):
        """
        Helper function. Given a prompt template and a list of records, generate a list of prompts for each record

        Returns
        -------
        prompts: list
            List of tuples of (uuid, generated prompt) for each record in given subset
        """
        prompts = []
        self.invalid_prompts = []
        for record in self.records:
            # append each data record to the template to generate prompt
            prompt = self.template.get_prompt(input_str=record["record_content"])
            if self.is_valid_prompt(prompt):
                prompts.append((record["uuid"], prompt))
            else:
                print(
                    "Prompt generated for uuid {} : {} was not within Open AI max token limits, and was hence dropped".format(
                        record["uuid"], prompt
                    )
                )
                self.invalid_prompts.append((record["uuid"], prompt))
        return prompts

    def get_response_length(self):
        """
        Return the length of the openai response
        """
        content = self.openai_response.choices[0]["message"]["content"]
        return len(content)

    def get_openai_conf_score(self):
        """
        Return confidence score of the label, calculated using average of logit scores
        """
        logprobs = []
        logprobs_response = self.openai_response.choices[0]["logprobs"]["content"]
        for logprob in logprobs_response:
            logprobs.append(logprob["logprob"])
        conf_score = round(np.mean(np.exp(logprobs)), 6)
        return conf_score

    def preprocess(self):
        """
        Generate the list of prompts for each record based on the subset and template

        Returns
        -------
        prompts : list
            List of prompts
        """
        self.is_json_template = self.template.is_json_template
        prompts = self.generate_prompts()

        print("\nPre-processing [{}] record(s) :::".format(len(self.records)))
        table = [
            [
                "Valid prompts",
                len(prompts),
                100 * round(len(prompts) / len(self.records), 4),
            ],
            [
                "Invalid prompts",
                len(self.invalid_prompts),
                100 * round(len(self.invalid_prompts) / len(self.records), 4),
            ],
        ]
        print(tabulate(table, headers=["", "Count", "%"], tablefmt="rounded_outline"))
        self.prompts = prompts

    def get_llm_annotations(
        self, batch_size=1, num_retrials=2, api_name="chat", label_meta_names=[]
    ):
        """
        Call OpenAI using the generated prompts, to obtain valid & invalid responses

        Parameters
        ----------
        batch_size : int
            Size of batch to each Open AI prompt
        num_retrials : int
            Number of retrials to OpenAI in case of failure in response
        api_name : str
            Name of OpenAI api eg. "chat" or "completion
        label_meta_names: list
            list of label metadata names to be set

        Returns
        -------
        responses : list
            List of valid responses from OpenAI
        invalid_responses : list
            List of invalid responses from OpenAI
        """
        print("\nCalling LLM API :::")

        prompts = self.prompts
        # todo: set batch_size depending on tokens per minute and requests per minute
        if batch_size < 1:
            batch_size = 1
        elif batch_size > 10:
            batch_size = 10

        responses = []
        invalid_responses = []
        q = queue.Queue()
        start = time.time()
        if batch_size == 1:
            for i, (uuid, prompt) in tqdm_notebook(enumerate(prompts), "Progress"):
                time.sleep(1e-10)
                q.put(num_retrials)
                while not q.empty():
                    try:
                        trials_left = q.get()
                        if api_name == "completions":
                            completion = openai.Completion.create(
                                prompt=prompt, **self.model_config
                            )
                            confidence_score = np.mean(
                                np.exp(
                                    completion["choices"][0]["logprobs"][
                                        "token_logprobs"
                                    ]
                                )
                            )
                            response = completion["choices"][0]["text"]
                        elif api_name == "chat":
                            self.model_config["messages"] = [
                                {
                                    "role": "user",
                                    "content": prompt,
                                },
                            ]
                            openai_response = openai.ChatCompletion.create(
                                **self.model_config
                            )
                            self.openai_response = openai_response
                            metadata_list = []
                            for label_meta_name in label_meta_names:
                                func = getattr(
                                    self, self.label_meta_func_map[label_meta_name]
                                )
                                metadata_list.append(
                                    {
                                        "metadata_name": label_meta_name,
                                        "metadata_value": func(),
                                    }
                                )

                            response = openai_response.choices[0]["message"]["content"]
                        responses.append((uuid, response.strip(), metadata_list))
                    except openai.error.AuthenticationError as e:
                        print("--------------------------")
                        print(
                            'Encounted an error during call to OpenAI for uuid: {}\nError Message from OpenAI: "{}"'.format(
                                uuid, e
                            )
                        )
                        invalid_responses.append((uuid, e))
                    except openai.error.APIError as e:
                        print("--------------------------")
                        print(
                            'Encounted an error during call to OpenAI for uuid: {}\nError Message from OpenAI: "{}"'.format(
                                uuid, e
                            )
                        )
                        invalid_responses.append((uuid, e))
                    except openai.error.APIConnectionError as e:
                        print("--------------------------")
                        print(
                            'Encounted an error during call to OpenAI for uuid: {}\nError Message from OpenAI: "{}"'.format(
                                uuid, e
                            )
                        )
                        invalid_responses.append((uuid, e))
                    except openai.error.RateLimitError as e:
                        trials_left -= 1
                        if trials_left == 0:
                            print(
                                "-------------------\nEncounted an error during call to OpenAI for uuid: {}\nRetried call to OpenAI {} number of times. \nError Message from OpenAI: {}.\n".format(
                                    uuid, num_retrials, e
                                )
                            )
                            invalid_responses.append((uuid, e))
                        else:
                            q.put(trials_left)
                    except openai.error.Timeout as e:
                        trials_left -= 1
                        if trials_left == 0:
                            print(
                                "-------------------\nEncounted an error during call to OpenAI for uuid: {}\nRetried call to OpenAI {} number of times. \nError Message from OpenAI: {}.\n".format(
                                    uuid, num_retrials, e
                                )
                            )
                            invalid_responses.append((uuid, e))
                        else:
                            q.put(trials_left)
                    except openai.error.InvalidRequestError as e:
                        print("--------------------------")
                        print(
                            'Encounted an error during call to OpenAI for uuid: {}\nError Message from OpenAI: "{}"'.format(
                                uuid, e
                            )
                        )
                        invalid_responses.append((uuid, e))
                    except openai.error.ServiceUnavailableError as e:
                        print("--------------------------")
                        print(
                            'Encounted an error during call to OpenAI for uuid: {}\nError Message from OpenAI: "{}"'.format(
                                uuid, e
                            )
                        )
                        invalid_responses.append((uuid, e))
                    except Exception as e:
                        print("--------------------------")
                        print(
                            "Encounted an unknown error during call to OpenAI for uuid: {} - {}\n".format(
                                uuid, e
                            )
                        )
                        invalid_responses.append((uuid, e))
        else:
            prompt_batches = [
                prompts[i : i + batch_size] for i in range(0, len(prompts), batch_size)
            ]
            for i, prompt_batch in tqdm_notebook(enumerate(prompt_batches), "Progress"):
                time.sleep(1e-10)
                uuids = [uuid for uuid, prompt in prompt_batch]
                prompts = [prompt for uuid, prompt in prompt_batch]
                q.put(num_retrials)
                while not q.empty():
                    try:
                        trials_left = q.get()
                        if api_name == "completions":
                            response_batch = openai.Completion.create(
                                prompt=prompts, **self.model_config
                            )
                            for choice in response_batch.choices:
                                confidence_score = np.mean(
                                    np.exp(choice.logprobs.token_logprobs)
                                )
                                responses.append(
                                    (
                                        uuids[choice.index],
                                        choice.text.strip(),
                                        confidence_score,
                                    )
                                )
                        elif api_name == "chat":
                            # TO BE IMPLEMENTED
                            pass
                    except openai.error.AuthenticationError as e:
                        print("--------------------------")
                        print(
                            'Encounted an error during call to OpenAI for uuids: {}\nError Message from OpenAI: "{}"'.format(
                                uuids, e
                            )
                        )
                        for uuid in uuids:
                            invalid_responses.append((uuid, e))
                    except openai.error.APIError as e:
                        print("--------------------------")
                        print(
                            'Encounted an error during call to OpenAI for uuids: {}\nError Message from OpenAI: "{}"'.format(
                                uuids, e
                            )
                        )
                        for uuid in uuids:
                            invalid_responses.append((uuid, e))
                    except openai.error.APIConnectionError as e:
                        print("--------------------------")
                        print(
                            'Encounted an error during call to OpenAI for uuids: {}\nError Message from OpenAI: "{}"'.format(
                                uuids, e
                            )
                        )
                        for uuid in uuids:
                            invalid_responses.append((uuid, e))
                    except openai.error.RateLimitError as e:
                        trials_left -= 1
                        if trials_left == 0:
                            print(
                                "-------------------\nEncounted an error during call to OpenAI for uuids: {}\nRetried call to OpenAI {} number of times. \nError Message from OpenAI: {}.\n".format(
                                    uuids, num_retrials, e
                                )
                            )
                            for uuid in uuids:
                                invalid_responses.append((uuid, e))
                        else:
                            q.put(trials_left)
                    except openai.error.Timeout as e:
                        trials_left -= 1
                        if trials_left == 0:
                            print(
                                "-------------------\nEncounted an error during call to OpenAI for uuids: {}\nRetried call to OpenAI {} number of times. \nError Message from OpenAI: {}.\n".format(
                                    uuids, num_retrials, e
                                )
                            )
                            for uuid in uuids:
                                invalid_responses.append((uuid, e))
                        else:
                            q.put(trials_left)
                    except openai.error.InvalidRequestError as e:
                        print("--------------------------")
                        print(
                            'Encounted an error during call to OpenAI for uuids: {}\nError Message from OpenAI: "{}"'.format(
                                uuids, e
                            )
                        )
                        for uuid in uuids:
                            invalid_responses.append((uuid, e))
                    except openai.error.ServiceUnavailableError as e:
                        print("--------------------------")
                        print(
                            'Encounted an error during call to OpenAI for uuids: {}\nError Message from OpenAI: "{}"'.format(
                                uuids, e
                            )
                        )
                        for uuid in uuids:
                            invalid_responses.append((uuid, e))
                        invalid_responses.append((uuid, e))
                    except Exception as e:
                        print("--------------------------")
                        print(
                            "Encounted an unknown error during call to OpenAI for uuids: {}\n".format(
                                uuids, e
                            )
                        )
                        for uuid in uuids:
                            invalid_responses.append((uuid, e))
        print(
            "Time taken to obtain responses from LLM: {} seconds".format(
                round(time.time() - start, 2)
            )
        )
        self.responses = responses
        self.invalid_responses = invalid_responses

        table = [
            [
                "Valid reponses",
                len(responses),
                100 * round(len(responses) / len(prompts), 4),
            ],
            [
                "Encountered API errors",
                len(prompts) - len(responses),
                100 * round(len(invalid_responses) / len(prompts), 4),
            ],
        ]
        print(tabulate(table, headers=["", "Count", "%"], tablefmt="rounded_outline"))

    def extract(self, uuid, response, fuzzy_extraction):
        """
        Helper function for post-processing. Extract the label (name and value) from the OpenAI response

        Parameters
        ----------
        uuid : str
            Record uuid
        response : str
            Output from OpenAI
        fuzzy_extraction: bool
            Set to True if fuzzy extraction desired in post processing

        Returns
        -------
        ret : dict
            Returns the label name and label value
        """
        # output {'label_name' : 'valid_formatted_response'}
        ret = {}

        if self.is_json_template == False:
            # assume only one label in label_dic
            # todo: fix label level should be dependent on parsed label name
            label_name = list(self.label_dic.keys())[0]
            label_level = self.label_dic[label_name]["level"]
            if label_level == "record":
                response = re.split(":|\n", response)
                for i in range(0, len(response), 2):
                    label_name = response[i].strip().lower()
                    if i + 1 == len(response):
                        self.syntax_errors.append((uuid, response))
                        continue
                    label_response = re.sub(r"[^\w\d\-_+]", "", response[i + 1].lower())
                    if label_name not in self.label_dic:
                        self.semantic_errors.append((uuid, response))
                        continue

                    if fuzzy_extraction == False:
                        if label_response not in self.label_dic[label_name]["options"]:
                            self.semantic_errors.append((uuid, response))
                            self.invalid_option_counter[label_response] += 1
                            continue
                        ret[label_name] = label_response

                    else:
                        max_fuzzy_score = 0
                        best_label_response = ""

                        for label_option in self.label_dic[label_name]["options"]:
                            fuzzy_score_jaro = jaro.jaro_winkler_metric(
                                label_option, label_response
                            )
                            if fuzzy_score_jaro > max_fuzzy_score:
                                max_fuzzy_score = fuzzy_score_jaro
                                best_label_response = label_option

                        if max_fuzzy_score >= FUZZY_THRESHOLD:
                            ret[label_name] = best_label_response
                        else:
                            self.semantic_errors.append((uuid, response))
                            self.invalid_option_counter[label_response] += 1
                            continue
            else:
                response = re.split(":|\n", response)
                label_name = response[0].strip().lower()
                if len(response[1].split(",")) == 2:
                    entity, label_response = response[1].split(",")
                    for record in self.records:
                        if record["uuid"] == uuid:
                            start_idx = (
                                record["record_content"]
                                .strip()
                                .lower()
                                .find(entity.strip().lower())
                            )
                            end_idx = start_idx + len(entity.strip())
                    label_response = label_response.strip().lower()
                    ret[label_name] = {}
                    ret[label_name]["label_response"] = (
                        label_response if label_response.isalpha() else "others"
                    )
                    ret[label_name]["start_idx"] = start_idx
                    ret[label_name]["end_idx"] = end_idx
                else:
                    print(
                        "For uuid : {}, response generated : {} for label name : {} is in invalid format".format(
                            uuid, response, label_name
                        )
                    )
        else:
            if response.endswith('"}') == False:
                response += '"}'
            response = response.strip().lower()

            try:
                data = json.loads(response)
            except ValueError as e:
                print(
                    "For uuid : {}, response generated : {} is in invalid JSON format".format(
                        uuid, response
                    )
                )
                return {}

            for label_name, label_obj in self.label_dic.items():
                allowed_values = label_obj["options"]
                if label_name in data and data[label_name] in allowed_values:
                    ret[label_name] = data[label_name]
                else:
                    print(
                        "For uuid : {}, response generated : {} is not valid".format(
                            uuid, data
                        )
                    )
                    continue
        return ret

    def post_process_annotations(self, fuzzy_extraction=False):
        """
        Perform output extraction from the responses generated by LLM, and formats it according to MEGAnno data model.

        Parameters
        ----------
        fuzzy_extraction: bool
            Set to True if fuzzy extraction desired in post processing

        Returns
        -------
        annotations : list
            List of annotations (uuid, label) in format required by MEGAnno
        """
        print("\nPost-processing [{}] response(s) :::".format(len(self.responses)))

        responses = self.responses
        if len(responses) == 0:
            raise Exception("No valid responses obtained")
        self.invalid_option_counter = Counter()
        annotations = []
        self.label_distribution = {}
        for label_key in self.label_dic:
            for key in self.label_dic[label_key]["options"]:
                self.label_distribution[
                    self.label_dic[label_key]["text_to_value"][key]
                ] = 0

        # assume only one label in label_dic
        # todo: fix label level should be dependent on parsed label name
        label_name = list(self.label_dic.keys())[0]
        label_level = self.label_dic[label_name]["level"]

        for uuid, response, metadata_list in responses:
            # extract, format, validate responses
            label_responses = self.extract(uuid, response, fuzzy_extraction)
            if len(label_responses) == 0:
                continue
            self.uuids_with_valid_annotations.append(uuid)

            if label_level == "record":
                label = {"labels_record": []}
                for label_name, response in label_responses.items():
                    label_value = self.label_dic[label_name]["text_to_value"][response]
                    label["labels_record"].append(
                        {
                            "label_name": label_name,
                            "label_level": label_level,
                            "label_value": [label_value],
                            "metadata_list": metadata_list,
                        }
                    )
                    self.label_distribution[label_value] += 1
            else:
                label = {"labels_span": []}
                for label_name, response in label_responses.items():
                    label_value = self.label_dic[label_name]["text_to_value"][
                        response["label_response"]
                    ]
                    label["labels_span"].append(
                        {
                            "label_name": label_name,
                            "label_level": label_level,
                            "label_value": [label_value],
                            "start_idx": response["start_idx"],
                            "end_idx": response["end_idx"],
                        }
                    )
                    self.label_distribution[label_value] += 1
            annotations.append((uuid, label))
        self.annotations = annotations

        table = [
            [
                "Valid annotations",
                len(annotations),
                100 * round(len(annotations) / len(responses), 4),
            ],
            [
                "Encountered extraction errors",
                len(responses) - len(annotations),
                100 * round((len(responses) - len(annotations)) / len(responses), 4),
            ],
        ]
        print(tabulate(table, headers=["", "Count", "%"], tablefmt="rounded_outline"))

        print("\nAnnotation Summary :::")
        print(
            tabulate(
                self.label_distribution.items(),
                headers=[label_name, "Count"],
                tablefmt="rounded_outline",
            )
        )
        print(
            tabulate(
                self.invalid_option_counter.most_common(10),
                headers=["Frequent invalid labels", "Count"],
                tablefmt="rounded_outline",
            ),
        )
