import httpx

SERVICE_ENDPOINTS = {
    "get_annotations": "/annotations",
    "set_annotations": "/annotations/{uuid}",
    "post_data": "/data",
    "batch_update_metadata": "/data/metadata",
    "suggest_similar_annotations": "/data/suggest_similar",
    "export_data": "/data/export",
    "get_schemas": "/schemas",
    "set_schemas": "/schemas",
    "get_assignment": "/assignments",
    "set_assignment": "/assignments",
    "get_reconciliation_data": "/reconciliations",
    "set_reconciliation_data": "/annotations/{uuid}/labels",
    "set_verification_data": "/verifications/{uuid}/labels",
    "get_user": "/auth/users/authenticate",
    "get_users_by_uids": "/auth/users/uids",
    "get_label_progress": "/statistics/label/progress",
    "get_label_distribution": "/statistics/label/distributions",
    "get_annotator_contribution": "/statistics/annotator/contributions",
    "get_annotator_agreement": "/statistics/annotator/agreements",
    "get_embeddings": "/statistics/embeddings/{embed_type}",
    "get_agents": "/agents",
    "get_jobs_of_agent": "/agents/{agent_uuid}/jobs",
    "get_jobs": "/agents/jobs",
    "register_agent": "/agents",
    "set_job": "/agents/{agent_uuid}/jobs/{job_uuid}",
    "add_metadata_to_label": "/annotations/label_metadata",
    "search": "/data/search",
    "get_view_record": "/view/record",
    "get_view_annotation": "/view/annotation",
    "get_view_verification": "/view/verifications",
    "submit_annotations_batch": "/annotations/batch",
}
VALID_SCHEMA_LEVELS = ["span_ch", "record"]
NO_TIMEOUT_ENDPOINTS = {
    "post": [SERVICE_ENDPOINTS["post_data"]],
    "get": [SERVICE_ENDPOINTS["suggest_similar_annotations"]],
}
DEFAULT_LIST_LIMIT = 10
REQUEST_TIMEOUT_SECONDS = 10
DNS_NAME = "https://labeler.megagon.ai"
HTTPX_LIMITS = httpx.Limits(max_connections=(9 + 1))
VALID_PROVIDERS = {"openai": ["chat"]}
FUZZY_THRESHOLD = 0.6
BATCH_SIZE = 6
