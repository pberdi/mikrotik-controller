"""
Unit tests for JobService.

Tests the job service functionality including listing, retrieving,
and canceling jobs with proper tenant isolation.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.models.job import Job, JobStatus, JobType
from app.services.job_service import JobService
from app.schemas.job import JobFilterParams


class TestJobService:
    """Test cases for JobService."""
    
    def test_list_jobs_basic(self, db_session, sample_tenant):
        """Test basic job listing."""
        # Create test jobs
        job1 = Job(
            tenant_id=sample_tenant.id,
            type=JobType.BACKUP,
            status=JobStatus.COMPLETED
        )
        job2 = Job(
            tenant_id=sample_tenant.id,
            type=JobType.CONNECTIVITY_CHECK,
            status=JobStatus.PENDING
        )
        
        db_session.add_all([job1, job2])
        db_session.commit()
        
        # Test service
        service = JobService(db_session, tenant_id=str(sample_tenant.id))
        result = service.list_jobs()
        
        assert result["total_count"] == 2
        assert len(result["items"]) == 2
        assert result["page"] == 1
        assert result["page_size"] == 50
    
    def test_list_jobs_with_status_filter(self, db_session, sample_tenant):
        """Test job listing with status filtering."""
        # Create test jobs with different statuses
        job1 = Job(
            tenant_id=sample_tenant.id,
            type=JobType.BACKUP,
            status=JobStatus.COMPLETED
        )
        job2 = Job(
            tenant_id=sample_tenant.id,
            type=JobType.BACKUP,
            status=JobStatus.PENDING
        )
        job3 = Job(
            tenant_id=sample_tenant.id,
            type=JobType.BACKUP,
            status=JobStatus.FAILED
        )
        
        db_session.add_all([job1, job2, job3])
        db_session.commit()
        
        # Test filtering by status
        service = JobService(db_session, tenant_id=str(sample_tenant.id))
        filters = JobFilterParams(status=JobStatus.PENDING)
        result = service.list_jobs(filters=filters)
        
        assert result["total_count"] == 1
        assert result["items"][0].status == JobStatus.PENDING
    
    def test_get_job_success(self, db_session, sample_tenant):
        """Test successful job retrieval."""
        # Create test job
        job = Job(
            tenant_id=sample_tenant.id,
            type=JobType.BACKUP,
            status=JobStatus.COMPLETED,
            result="Backup completed successfully"
        )
        
        db_session.add(job)
        db_session.commit()
        
        # Test service
        service = JobService(db_session, tenant_id=str(sample_tenant.id))
        result = service.get_job(job.id)
        
        assert result is not None
        assert result.id == job.id
        assert result.type == JobType.BACKUP
        assert result.status == JobStatus.COMPLETED
        assert result.result == "Backup completed successfully"
    
    def test_get_job_not_found(self, db_session, sample_tenant):
        """Test job retrieval when job doesn't exist."""
        service = JobService(db_session, tenant_id=str(sample_tenant.id))
        result = service.get_job(uuid4())
        
        assert result is None
    
    def test_cancel_job_success(self, db_session, sample_tenant):
        """Test successful job cancellation."""
        # Create pending job
        job = Job(
            tenant_id=sample_tenant.id,
            type=JobType.BACKUP,
            status=JobStatus.PENDING
        )
        
        db_session.add(job)
        db_session.commit()
        
        # Test cancellation
        service = JobService(db_session, tenant_id=str(sample_tenant.id))
        result = service.cancel_job(job.id, reason="Test cancellation")
        
        assert result is not None
        assert result.status == JobStatus.CANCELLED
        assert "Test cancellation" in result.error_message
        assert result.finished_at is not None
    
    def test_cancel_job_invalid_status(self, db_session, sample_tenant):
        """Test job cancellation with invalid status."""
        # Create completed job (cannot be cancelled)
        job = Job(
            tenant_id=sample_tenant.id,
            type=JobType.BACKUP,
            status=JobStatus.COMPLETED
        )
        
        db_session.add(job)
        db_session.commit()
        
        # Test cancellation should fail
        service = JobService(db_session, tenant_id=str(sample_tenant.id))
        
        with pytest.raises(Exception) as exc_info:
            service.cancel_job(job.id)
        
        assert "Cannot cancel job" in str(exc_info.value)
    
    def test_tenant_isolation(self, db_session, sample_tenant, other_tenant):
        """Test that jobs are properly isolated by tenant."""
        # Create jobs for different tenants
        job1 = Job(
            tenant_id=sample_tenant.id,
            type=JobType.BACKUP,
            status=JobStatus.COMPLETED
        )
        job2 = Job(
            tenant_id=other_tenant.id,
            type=JobType.BACKUP,
            status=JobStatus.COMPLETED
        )
        
        db_session.add_all([job1, job2])
        db_session.commit()
        
        # Test that service only sees jobs from its tenant
        service = JobService(db_session, tenant_id=str(sample_tenant.id))
        result = service.list_jobs()
        
        assert result["total_count"] == 1
        assert result["items"][0].tenant_id == sample_tenant.id
        
        # Test that job from other tenant is not accessible
        other_job_result = service.get_job(job2.id)
        assert other_job_result is None
    
    def test_get_job_stats(self, db_session, sample_tenant):
        """Test job statistics retrieval."""
        # Create jobs with different statuses and types
        jobs = [
            Job(tenant_id=sample_tenant.id, type=JobType.BACKUP, status=JobStatus.COMPLETED),
            Job(tenant_id=sample_tenant.id, type=JobType.BACKUP, status=JobStatus.FAILED),
            Job(tenant_id=sample_tenant.id, type=JobType.CONNECTIVITY_CHECK, status=JobStatus.RUNNING),
            Job(tenant_id=sample_tenant.id, type=JobType.COMMAND, status=JobStatus.PENDING),
        ]
        
        db_session.add_all(jobs)
        db_session.commit()
        
        # Test stats
        service = JobService(db_session, tenant_id=str(sample_tenant.id))
        stats = service.get_job_stats()
        
        assert stats["total_jobs"] == 4
        assert stats["by_status"]["completed"] == 1
        assert stats["by_status"]["failed"] == 1
        assert stats["by_status"]["running"] == 1
        assert stats["by_status"]["pending"] == 1
        assert stats["by_type"]["backup"] == 2
        assert stats["by_type"]["connectivity_check"] == 1
        assert stats["by_type"]["command"] == 1
        assert stats["running_jobs"] == 1
        assert stats["failed_jobs"] == 1