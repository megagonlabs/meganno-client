# LLM Integration

This [notebook](https://github.com/megagonlabs/meganno-client/blob/main/Examples/Example%203%20-%20LLM%20integration.ipynb) provides an example workflow of integrating LLMs within MEGAnno.


![Figure 1. Human-LLM collaborative workflow.](assets/images/meganno_site_llm_human.png)
<br/><span style="color: gray; text-align:center;",>*Figure 1. Human-LLM collaborative workflow.*</span>

MEGAnno offers a simple human-LLM collaborative annotation workflow: LLM annotation followed by human verification. Put simply, LLM agents label data first (Figure 2, step ①), and humans verify LLM labels as needed. For most tasks and datasets one can use LLM labels as is; for some subset of difficult or uncertain instances (Figure 2, step ②), humans can verify LLM labels – confirm the right ones and correct the wrong ones (Figure 2, step ③). In this way, the LLM annotation part can be automated, and human efforts can be directed to where they are most needed to improve the quality of final labels.

An overview of the entire system is shown below.

![Figure 2. Overview of MEGAnno+ system.](assets/images/meganno_site_overview.png)
<br/><span style="color: gray; text-align:center;",>*Figure 2. Overview of MEGAnno+ system.*</span>

**Subset**: refers to a slice of data created from user-defined searches. 

**Record**: refers to an item within the data corpus. 

**Agent**: an _Agent_ is defined by the configuration of the LLM (e.g., model’s name, version, and hyper-parameters) and a prompt template. 

**Job**: when an _Agent_ is employed to annotate a selected data _Subset_, the execution is referred to as a Job.

**Label**: stores the label assigned to a particular _Record_

**Label_Metadata**: captures additional aspects of a label, such as LLM confidence score or length of label response, etc.

**Verification**: captures annotations from human users that confirm or update LLM labels

## LLM Annotation

There are 3 major steps to LLM annotation using MEGAnno, as shown in the figure below. 

![Figure 3. Steps in the LLM annotation workflow.](assets/images/meganno_site_fig1.png)
<br/><span style="color: gray; text-align:center;",>*Figure 3. Steps in the LLM annotation workflow.*</span>

The _preprocessing_ step handles the generation of prompts and validation of model configuration.

Users can specify a particular LLM model, define its configurations and customize a prompt template. This defines an _Agent_ which can be used for the annotation task. You may also re-use an _Agent_.

After the selected model configuration is validated, the next step is _calling the LLM_. MEGAnno handles the call to the external LLM API to obtain LLM responses. Any API errors encountered during the call are also appropriately handled and a suitable message is relayed to the user. 

Once the responses are obtained, the _post-processing_ step extracts the label from the LLM response. This ensures some minor deviations in the LLM's response (such as trailing period) are handled. Furthermore, users can set `fuzzy_extraction=True` which performs a fuzzy match between the LLM response and the label schema space, and if a significant match is found the corresponding label is attributed for the task. The figure below shows how MEGAnno's post-processing mechanism handles several LLM responses.

![Figure 4. Example LLM responses and post-processing results by MEGAnno.](assets/images/meganno_site_post_process.png)
<br/><span style="color: gray; text-align:center;",>*Figure 4. Example LLM responses and post-processing results by MEGAnno.*</span>

## Verification Subset Selection 

It would be redundant for a human to verify every annotation in the dataset as that would defeat the purpose of using LLMs for a cheap and faster annotation process. Instead, MEGAnno provides a possibility to aid the human verifiers by computing confidence scores for each annotation. Users can specify `confidence_score` of the LLM labels to be computed and stored. They can then view the confidence scores, and even sort as well as filter over them to obtain only those annotations for which the LLM had low confidence scores. This will ease the human verification process and make it more efficient.

## Human Verification

Users can then use MEGAnno's in-notebook widget to verify LLM labels i.e., either _confirm_ a label as correct or _reject_ the label and specify a correct label. Users may view the final annotations and export the data for downstream tasks or further analysis. 

![Figure 5. Verification UI for exploring data and confirming/correcting LLM labels.](assets/images/meganno_site_verification.gif)
<br/><span style="color: gray; text-align:center;",>*Figure 5. Verification UI for exploring data and confirming/correcting LLM labels.*</span>