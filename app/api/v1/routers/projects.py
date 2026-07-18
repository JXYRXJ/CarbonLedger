import uuid
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_admin, get_current_active_user, get_pagination_params, get_service, get_db
from app.models.models import User, CarbonProject, Registry, ProjectDocument, DocumentType
from app.schemas.pagination import PaginationParams, PaginatedResponse, PaginationMetadata
from app.schemas.responses import APIResponse
from app.schemas.project import (
    CarbonProjectCreate,
    CarbonProjectUpdate,
    CarbonProjectResponse,
    ProjectDocumentResponse,
    ProjectDocumentCreate
)
from app.schemas.registry import RegistryResponse
from app.repositories.repositories import ProjectRepository, RegistryRepository, DocumentRepository
from app.services.services import ProjectService, RegistryService, DocumentService

router = APIRouter(prefix="/projects", tags=["Projects"])


# ==============================================================================
# INPUT SCHEMAS FOR DOCUMENTS
# ==============================================================================

class CreateDocumentRequest(BaseModel):
    document_type: DocumentType = Field(..., examples=[DocumentType.VERIFICATION_CERTIFICATE])
    file_name: str = Field(..., min_length=1, max_length=255, examples=["certificate.pdf"])
    file_url: str = Field(..., max_length=1024, examples=["https://storage.carbonledger.com/docs/certificate.pdf"])


class UpdateDocumentRequest(BaseModel):
    document_type: Optional[DocumentType] = Field(None)
    file_name: Optional[str] = Field(None, min_length=1, max_length=255)
    file_url: Optional[str] = Field(None, max_length=1024)


# ==============================================================================
# CARBON PROJECT ENDPOINTS
# ==============================================================================

@router.get("", response_model=APIResponse[PaginatedResponse[Any]])
def list_projects(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
    project_service: ProjectService = Depends(get_service(ProjectService, ProjectRepository))
):
    """
    Retrieves a paginated and filtered list of carbon projects registered on the platform.
    Accessible to all authenticated users.
    """
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    cache_key = f"projects:all:search={pagination.search}:page={pagination.page}:limit={pagination.limit}:sort={pagination.sort}:order={pagination.order}"
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return APIResponse(
            message="Projects list retrieved successfully (cached)",
            data=PaginatedResponse.model_validate(cached)
        )

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    projects, total = project_service.search_projects(
        search_query=pagination.search,
        page=pagination.page,
        limit=pagination.limit,
        sort=pagination.sort,
        order=pagination.order
    )
    
    items_data = []
    for p in projects:
        registry = p.registry
        items_data.append({
            "id": str(p.id),
            "registry_id": str(p.registry_id),
            "project_code": p.project_code,
            "name": p.name,
            "country": p.country,
            "project_type": p.project_type,
            "verification_standard": p.verification_standard,
            "methodology": p.methodology,
            "description": p.description,
            "developer": p.developer,
            "start_date": p.start_date.isoformat() if p.start_date else None,
            "end_date": p.end_date.isoformat() if p.end_date else None,
            
            # camelCase mappings for React frontend
            "projectType": p.project_type,
            "verificationStandard": p.verification_standard,
            "registryName": registry.name if registry else None,
            
            # Nested relations
            "registry": {
                "id": str(registry.id) if registry else None,
                "name": registry.name if registry else None,
            } if registry else None,
        })
    
    pages = (total + pagination.limit - 1) // pagination.limit if pagination.limit > 0 else 0
    paginated_data = PaginatedResponse(
        items=items_data,
        pagination=PaginationMetadata(
            total=total,
            page=pagination.page,
            limit=pagination.limit,
            pages=pages,
            has_next=pagination.page < pages,
            has_prev=pagination.page > 1
        )
    )

    cache_service.set(cache_key, paginated_data.model_dump(mode="json"), ttl=300)

    return APIResponse(
        message="Projects list retrieved successfully",
        data=paginated_data
    )


@router.get("/{project_id}", response_model=APIResponse[dict])
def get_project_details(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    project_service: ProjectService = Depends(get_service(ProjectService, ProjectRepository)),
    registry_service: RegistryService = Depends(get_service(RegistryService, RegistryRepository)),
    document_service: DocumentService = Depends(get_service(DocumentService, DocumentRepository))
) -> APIResponse[dict]:
    """
    Retrieves complete information of a carbon project, including registry details,
    attached documents, and credits verification statistics.
    Accessible to all authenticated users.
    """
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    cache_key = f"projects:id:{project_id}"
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return APIResponse(
            message="Project details retrieved successfully (cached)",
            data=cached
        )

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    project = project_service.get_project(project_id)
    registry = registry_service.get_registry(project.registry_id)
    documents = document_service.list_project_documents(project_id)
    stats = project_service.get_project_statistics(project_id)

    docs_data = []
    for doc in documents:
        docs_data.append({
            "id": str(doc.id),
            "documentType": doc.document_type.value if hasattr(doc.document_type, "value") else str(doc.document_type),
            "fileName": doc.file_name,
            "fileUrl": doc.file_url,
            "uploadedAt": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        })

    data = {
        # Raw model details (flat)
        "id": str(project.id),
        "registry_id": str(project.registry_id),
        "project_code": project.project_code,
        "name": project.name,
        "country": project.country,
        "project_type": project.project_type,
        "verification_standard": project.verification_standard,
        "methodology": project.methodology,
        "description": project.description,
        "developer": project.developer,
        "start_date": project.start_date.isoformat() if project.start_date else None,
        "end_date": project.end_date.isoformat() if project.end_date else None,
        
        # camelCase mappings for React frontend
        "projectType": project.project_type,
        "verificationStandard": project.verification_standard,
        "registryName": registry.name if registry else None,
        "vintageYears": [str(v) for v in range(project.start_date.year, project.end_date.year + 1)] if (project.start_date and project.end_date) else [],
        
        # Nested relations
        "registry": {
            "id": str(registry.id) if registry else None,
            "name": registry.name if registry else None,
        } if registry else None,
        
        "documents": docs_data,
        
        "stats": {
            "total_credits": float(stats["credits_issued"]),
            "remaining_credits": float(stats["credits_remaining"]),
            "batches_count": int(stats["batches_count"]),
        },
        
        # Original keys
        "project": CarbonProjectResponse.model_validate(project).model_dump(),
        "statistics": stats,
        "associated_credit_batch_count": stats["batches_count"]
    }
    
    cache_service.set(cache_key, data, ttl=300)
    
    return APIResponse(
        message="Project details retrieved successfully",
        data=data
    )


@router.post("", response_model=APIResponse[CarbonProjectResponse], status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CarbonProjectCreate,
    admin_user: User = Depends(get_current_admin),
    project_service: ProjectService = Depends(get_service(ProjectService, ProjectRepository))
) -> APIResponse[CarbonProjectResponse]:
    """
    Registers a new carbon project on the platform. Restricted to ADMIN users.
    """
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    metrics_service.record_db_query()
    project = project_service.create_project(payload.model_dump(), admin_user.id)
    
    cache_service.invalidate_pattern("projects:*")
    cache_service.invalidate_pattern("analytics:*")
    
    return APIResponse(
        message="Carbon project created successfully",
        data=CarbonProjectResponse.model_validate(project)
    )


@router.patch("/{project_id}", response_model=APIResponse[CarbonProjectResponse])
def update_project(
    project_id: uuid.UUID,
    payload: CarbonProjectUpdate,
    admin_user: User = Depends(get_current_admin),
    project_service: ProjectService = Depends(get_service(ProjectService, ProjectRepository))
) -> APIResponse[CarbonProjectResponse]:
    """
    Updates general metadata attributes of a carbon project. Restricted to ADMIN users.
    """
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    metrics_service.record_db_query()
    updated = project_service.update_project(project_id, payload.model_dump(exclude_unset=True), admin_user.id)
    
    cache_service.invalidate_pattern("projects:*")
    cache_service.invalidate_pattern("analytics:*")
    
    return APIResponse(
        message="Carbon project updated successfully",
        data=CarbonProjectResponse.model_validate(updated)
    )


@router.delete("/{project_id}", response_model=APIResponse[CarbonProjectResponse])
def delete_project(
    project_id: uuid.UUID,
    admin_user: User = Depends(get_current_admin),
    project_service: ProjectService = Depends(get_service(ProjectService, ProjectRepository))
) -> APIResponse[CarbonProjectResponse]:
    """
    Soft deletes a carbon project. Restricted to ADMIN users.
    """
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    metrics_service.record_db_query()
    deleted = project_service.delete_project(project_id, admin_user.id)
    
    cache_service.invalidate_pattern("projects:*")
    cache_service.invalidate_pattern("analytics:*")
    
    return APIResponse(
        message="Carbon project successfully soft deleted",
        data=CarbonProjectResponse.model_validate(deleted)
    )


@router.get("/{project_id}/statistics", response_model=APIResponse[dict])
def get_project_statistics(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    project_service: ProjectService = Depends(get_service(ProjectService, ProjectRepository))
) -> APIResponse[dict]:
    """
    Aggregates credits statistics (issued, remaining, retired, unique holders) for a project.
    Accessible to all authenticated users.
    """
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    cache_key = f"projects:stats:{project_id}"
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return APIResponse(
            message="Project statistics generated successfully (cached)",
            data=cached
        )

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    stats = project_service.get_project_statistics(project_id)
    
    cache_service.set(cache_key, stats, ttl=300)
    
    return APIResponse(
        message="Project statistics generated successfully",
        data=stats
    )


# ==============================================================================
# PROJECT DOCUMENT ENDPOINTS
# ==============================================================================

@router.get("/{project_id}/documents", response_model=APIResponse[List[ProjectDocumentResponse]])
def list_project_documents(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    document_service: DocumentService = Depends(get_service(DocumentService, DocumentRepository))
) -> APIResponse[List[ProjectDocumentResponse]]:
    """
    Lists all documents attached to a specific project.
    Accessible to all authenticated users.
    """
    documents = document_service.list_project_documents(project_id)
    return APIResponse(
        message="Project documents list retrieved successfully",
        data=[ProjectDocumentResponse.model_validate(d) for d in documents]
    )


@router.post("/{project_id}/documents", response_model=APIResponse[ProjectDocumentResponse], status_code=status.HTTP_201_CREATED)
def create_project_document(
    project_id: uuid.UUID,
    payload: CreateDocumentRequest,
    admin_user: User = Depends(get_current_admin),
    document_service: DocumentService = Depends(get_service(DocumentService, DocumentRepository))
) -> APIResponse[ProjectDocumentResponse]:
    """
    Attaches a verification, methodology, or monitoring document to a project. Restricted to ADMIN users.
    """
    doc = document_service.add_document(project_id, payload.model_dump(), admin_user.id)
    return APIResponse(
        message="Project document attached successfully",
        data=ProjectDocumentResponse.model_validate(doc)
    )


document_router = APIRouter(prefix="/documents", tags=["Documents"])


@document_router.patch("/{document_id}", response_model=APIResponse[ProjectDocumentResponse])
def update_project_document(
    document_id: uuid.UUID,
    payload: UpdateDocumentRequest,
    admin_user: User = Depends(get_current_admin),
    document_service: DocumentService = Depends(get_service(DocumentService, DocumentRepository))
) -> APIResponse[ProjectDocumentResponse]:
    """
    Updates the details of a project document. Restricted to ADMIN users.
    """
    updated = document_service.update_document(document_id, payload.model_dump(exclude_unset=True), admin_user.id)
    return APIResponse(
        message="Project document updated successfully",
        data=ProjectDocumentResponse.model_validate(updated)
    )


@document_router.delete("/{document_id}", response_model=APIResponse[dict])
def delete_project_document(
    document_id: uuid.UUID,
    admin_user: User = Depends(get_current_admin),
    document_service: DocumentService = Depends(get_service(DocumentService, DocumentRepository))
) -> APIResponse[dict]:
    """
    Deletes a project document from the system database. Restricted to ADMIN users.
    """
    document_service.delete_document(document_id, admin_user.id)
    return APIResponse(
        message="Project document deleted successfully",
        data={}
    )

