"""Azure adapters for ADLS Gen2 and Azure AI Search."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable

from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
)
from azure.storage.blob import BlobServiceClient

from .models import AuditEvent, Evidence, MemoryEntry, Principal


def azure_credential() -> TokenCredential:
    if os.getenv("IDENTITY_ENDPOINT"):
        return ManagedIdentityCredential()
    return DefaultAzureCredential()


def search_index() -> SearchIndex:
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(
            name="source_principal",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(name="source_type", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="created_at", type=SearchFieldDataType.DateTimeOffset),
        SimpleField(name="ingestion_path", type=SearchFieldDataType.String),
        SimpleField(name="confidence", type=SearchFieldDataType.Double, filterable=True),
        SimpleField(name="trust_score", type=SearchFieldDataType.Double, filterable=True),
        SimpleField(
            name="approval_status",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(name="status", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="tenant", type=SearchFieldDataType.String, filterable=True),
        SearchField(
            name="allowed_groups",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
        ),
        SimpleField(name="version", type=SearchFieldDataType.Int32, filterable=True),
        SearchField(
            name="parent_evidence_ids",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
        ),
        SimpleField(name="derived_from_agent", type=SearchFieldDataType.Boolean),
    ]
    return SearchIndex(
        name=os.getenv("AZURE_SEARCH_INDEX", "patchpilot-memory"),
        fields=fields,
    )


class AzureBackend:
    def __init__(self) -> None:
        self.search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
        self.storage_url = os.environ["AZURE_STORAGE_ACCOUNT_URL"]
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER", "release-memory")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX", "patchpilot-memory")
        self.native_permission_filters_enabled = (
            os.getenv("PATCHPILOT_NATIVE_PERMISSION_FILTERS", "false").lower()
            == "true"
        )
        self.credential = azure_credential()
        self.blob_service = BlobServiceClient(self.storage_url, self.credential)

    def initialize(
        self,
        evidence: Iterable[Evidence],
        memories: Iterable[MemoryEntry],
    ) -> None:
        index_client = SearchIndexClient(self.search_endpoint, self.credential)
        index_client.create_or_update_index(search_index())
        container = self.blob_service.get_container_client(self.container_name)
        try:
            container.create_container()
        except Exception as error:
            if getattr(error, "status_code", None) != 409:
                raise
        for item in evidence:
            blob = container.get_blob_client(f"evidence/{item.id}.json")
            blob.upload_blob(
                item.model_dump_json(indent=2),
                overwrite=True,
                metadata={
                    "tenant": item.tenant,
                    "source_principal": item.source_principal,
                },
            )
        initial_memories = list(memories)
        container.get_blob_client("snapshots/clean-v1.json").upload_blob(
            json.dumps(
                [json.loads(item.model_dump_json()) for item in initial_memories],
                indent=2,
            ),
            overwrite=True,
        )
        self.sync_state(initial_memories, [])

    def sync_memories(self, memories: Iterable[MemoryEntry]) -> None:
        documents = [
            json.loads(memory.model_dump_json())
            for memory in memories
        ]
        with SearchClient(
            self.search_endpoint,
            self.index_name,
            self.credential,
        ) as client:
            existing_ids = {
                str(result["id"])
                for result in client.search(
                    search_text="*",
                    select=["id"],
                    top=1000,
                )
            }
            current_ids = {str(document["id"]) for document in documents}
            stale_ids = existing_ids - current_ids
            if stale_ids:
                client.delete_documents(
                    [{"id": document_id} for document_id in stale_ids]
                )
            if not documents:
                return
            results = client.merge_or_upload_documents(documents)
        failures = [result.key for result in results if not result.succeeded]
        if failures:
            raise RuntimeError(f"Azure AI Search rejected documents: {failures}")

    def sync_state(
        self,
        memories: Iterable[MemoryEntry],
        audit_events: Iterable[AuditEvent],
    ) -> None:
        memory_items = list(memories)
        self.sync_memories(memory_items)
        container = self.blob_service.get_container_client(self.container_name)
        container.get_blob_client("snapshots/current.json").upload_blob(
            json.dumps(
                [json.loads(item.model_dump_json()) for item in memory_items],
                indent=2,
            ),
            overwrite=True,
        )
        for event in audit_events:
            blob = container.get_blob_client(
                f"audit/{event.sequence:06d}-{event.action}-{event.subject_id}.json"
            )
            try:
                blob.upload_blob(event.model_dump_json(indent=2), overwrite=False)
            except Exception as error:
                if getattr(error, "status_code", None) != 409:
                    raise

    def search(
        self,
        principal: Principal,
        question: str,
        *,
        guarded: bool,
        query_source_authorization: str | None,
    ) -> list[dict[str, object]]:
        tenant = principal.tenant.replace("'", "''")
        groups = ",".join(group.replace(",", "") for group in principal.groups)
        filters = [
            f"tenant eq '{tenant}'",
            f"allowed_groups/any(group: search.in(group, '{groups}', ','))",
        ]
        if guarded:
            filters.extend(["status eq 'approved'", "trust_score ge 0.7"])
        kwargs: dict[str, object] = {}
        if query_source_authorization and self.native_permission_filters_enabled:
            kwargs["headers"] = {
                "x-ms-query-source-authorization": query_source_authorization
            }
        with SearchClient(
            self.search_endpoint,
            self.index_name,
            self.credential,
        ) as client:
            results = client.search(
                search_text=question,
                filter=" and ".join(filters),
                top=3,
                **kwargs,
            )
            return [dict(result) for result in results]
