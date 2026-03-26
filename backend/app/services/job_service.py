"""
Job service for managing asynchronous operations.

This module provides business logic for job management operations
including listing, retrieving, and canceling jobs with proper
tenant isolation.
"""

from typing import Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from ..models.job import Job, JobStatus, JobType
from ..schemas.job import JobFilterParams, JobResponse, JobDetailResponse
from ..schemas.common import PaginatedResponse
from .base_service import BaseService


class JobService(BaseService):
    """
    Service for managing job operations.
    
    Provides methods for listing, retrieving, and canceling jobs
    with proper tenant isolation and audit logging.
    """
    
    def list_jobs(
        self,
        filters: Optional[JobFilterParams] = None,
        page: int = 1,
        page_size: int = 50,
        allow_cross_tenant: bool = False
    ) -> PaginatedResponse[JobResponse]:
        """
        List jobs with filtering and pagination.
        
        Args:
            filters: Optional filtering parameters
            page: Page number (1-based)
            page_size: Number of items per page
            allow_cross_tenant: Whether to allow cross-tenant access (SuperAdmin only)
            
        Returns:
            Paginated list of jobs
            
        Raises:
            HTTPException: If access denied or invalid parameters
        """
        # Start with base query
        query = self.db.query(Job)
        
        # Apply tenant filtering
        query = self._apply_tenant_filter(query, Job, allow_cross_tenant)
        
        # Apply filters if provided
        if filters:
            if filters.status:
                query = query.filter(Job.status == filters.status)
                
            if filters.type:
                query = query.filter(Job.type == filters.type)
                
            if filters.device_id:
                query = query.filter(Job.device_id == filters.device_id)
                
            # Apply date range filters
            if filters.start_date:
                query = query.filter(Job.created_at >= filters.start_date)
                
            if filters.end_date:
                query = query.filter(Job.created_at <= filters.end_date)
                
            # Apply search if provided
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    Job.type.ilike(search_term)
                )
        
        # Order by creation date (newest first)
        query = query.order_by(desc(Job.created_at))
        
        # Use base service pagination
        result = self.list_resources(
            query=query,
            page=page,
            page_size=page_size,
            response_model=JobResponse
        )
        
        # Log audit event
        self._log_audit_event(
            action="job_list",
            resource_type="job",
            result="success",
            details={
                "filters": filters.dict() if filters else None,
                "page": page,
                "page_size": page_size,
                "total_count": result.total_count
            }
        )
        
        return result
    
    def get_job(
        self,
        job_id: Union[str, UUID],
        allow_cross_tenant: bool = False
    ) -> Optional[JobDetailResponse]:
        """
        Get job by ID with detailed information.
        
        Args:
            job_id: Job ID to retrieve
            allow_cross_tenant: Whether to allow cross-tenant access (SuperAdmin only)
            
        Returns:
            Job details if found, None otherwise
            
        Raises:
            HTTPException: If access denied
        """
        # Get job using base service method
        job = self.get_by_id(
            resource_id=job_id,
            model=Job,
            allow_cross_tenant=allow_cross_tenant
        )
        
        if not job:
            return None
        
        # Convert to response schema
        job_response = JobDetailResponse.from_orm(job)
        
        # Log audit event
        self._log_audit_event(
            action="job_get",
            resource_type="job",
            resource_id=job.id,
            result="success"
        )
        
        return job_response
    
    def cancel_job(
        self,
        job_id: Union[str, UUID],
        reason: Optional[str] = None,
        allow_cross_tenant: bool = False
    ) -> Optional[JobResponse]:
        """
        Cancel a pending job.
        
        Args:
            job_id: Job ID to cancel
            reason: Optional reason for cancellation
            allow_cross_tenant: Whether to allow cross-tenant access (SuperAdmin only)
            
        Returns:
            Updated job if successful, None if job not found
            
        Raises:
            HTTPException: If access denied or job cannot be cancelled
        """
        # Get job using base service method
        job = self.get_by_id(
            resource_id=job_id,
            model=Job,
            allow_cross_tenant=allow_cross_tenant
        )
        
        if not job:
            return None
        
        # Check if job can be cancelled
        if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=409,
                detail=f"Cannot cancel job with status '{job.status}'. Only pending or running jobs can be cancelled."
            )
        
        # Update job status
        old_status = job.status
        job.status = JobStatus.CANCELLED
        
        # Add cancellation reason to error_message if provided
        if reason:
            job.error_message = f"Cancelled: {reason}"
        else:
            job.error_message = "Cancelled by user"
        
        # Set finished timestamp
        from datetime import datetime, timezone
        job.finished_at = datetime.now(timezone.utc)
        
        try:
            self.db.commit()
            
            # Log audit event
            self._log_audit_event(
                action="job_cancel",
                resource_type="job",
                resource_id=job.id,
                result="success",
                before_value={"status": old_status.value},
                after_value={"status": job.status.value},
                details={"reason": reason}
            )
            
            # TODO: Cancel the actual Celery task if celery_task_id is available
            # This would require Celery app instance to revoke the task
            
            return JobResponse.from_orm(job)
            
        except Exception as e:
            self.db.rollback()
            
            # Log audit event for failure
            self._log_audit_event(
                action="job_cancel",
                resource_type="job",
                resource_id=job.id,
                result="error",
                details={"error": str(e), "reason": reason}
            )
            
            raise
    
    def get_job_stats(
        self,
        allow_cross_tenant: bool = False
    ) -> Dict[str, Union[int, Dict[str, int]]]:
        """
        Get job statistics.
        
        Args:
            allow_cross_tenant: Whether to allow cross-tenant access (SuperAdmin only)
            
        Returns:
            Dictionary with job statistics
        """
        # Start with base query
        query = self.db.query(Job)
        
        # Apply tenant filtering
        query = self._apply_tenant_filter(query, Job, allow_cross_tenant)
        
        # Get total count
        total_jobs = query.count()
        
        # Get count by status
        status_counts = {}
        for status in JobStatus:
            count = query.filter(Job.status == status).count()
            status_counts[status.value] = count
        
        # Get count by type
        type_counts = {}
        for job_type in JobType:
            count = query.filter(Job.type == job_type).count()
            type_counts[job_type.value] = count
        
        # Get running and failed job counts
        running_jobs = query.filter(Job.status == JobStatus.RUNNING).count()
        failed_jobs = query.filter(Job.status == JobStatus.FAILED).count()
        
        stats = {
            "total_jobs": total_jobs,
            "by_status": status_counts,
            "by_type": type_counts,
            "running_jobs": running_jobs,
            "failed_jobs": failed_jobs
        }
        
        # Log audit event
        self._log_audit_event(
            action="job_stats",
            resource_type="job",
            result="success",
            details={"stats": stats}
        )
        
        return stats