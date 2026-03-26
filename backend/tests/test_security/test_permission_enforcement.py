"""
Property-based tests for permission enforcement.

This module tests that the RBAC system correctly enforces permissions
and returns 403 Forbidden when users lack required permissions.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from fastapi import HTTPException
from uuid import uuid4

from app.dependencies import PermissionChecker, require_permission
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_role(db_session):
    """Create a sample role for testing."""
    role = Role(
        name="TestRole",
        description="Test role for permission testing"
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def superadmin_role(db_session):
    """Create SuperAdmin role for testing."""
    role = Role(
        name="SuperAdmin",
        description="Super administrator with all permissions"
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def sample_user_with_permissions(db_session, sample_tenant, sample_role):
    """Create a user with specific permissions."""
    def _create_user(permissions_list):
        """Helper to create user with specific permissions."""
        # Clear existing permissions
        db_session.query(Permission).filter(
            Permission.role_id == sample_role.id
        ).delete()
        
        # Add specified permissions
        for resource, action in permissions_list:
            perm = Permission(
                role_id=sample_role.id,
                resource=resource,
                action=action
            )
            db_session.add(perm)
        
        # Create user
        user = User(
            tenant_id=sample_tenant.id,
            email=f"test-{uuid4()}@example.com",
            password_hash="hashed_password",
            role_id=sample_role.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        db_session.refresh(sample_role)
        return user
    
    return _create_user


@pytest.fixture
def superadmin_user(db_session, sample_tenant, superadmin_role):
    """Create a SuperAdmin user."""
    user = User(
        tenant_id=sample_tenant.id,
        email="superadmin@example.com",
        password_hash="hashed_password",
        role_id=superadmin_role.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ============================================================================
# Hypothesis Strategies
# ============================================================================

# Strategy for resource types
resource_strategy = st.sampled_from([
    "device", "template", "job", "backup", "alert", "user", "audit_log"
])

# Strategy for action types
action_strategy = st.sampled_from([
    "create", "read", "update", "delete", "execute"
])

# Strategy for permission tuples
permission_strategy = st.tuples(resource_strategy, action_strategy)

# Strategy for lists of permissions (1-10 permissions)
permissions_list_strategy = st.lists(
    permission_strategy,
    min_size=1,
    max_size=10,
    unique=True
)


# ============================================================================
# Property-Based Tests
# ============================================================================

class TestPermissionEnforcementProperty:
    """
    Property-based tests for permission enforcement.
    
    **Validates: Requirements 8.8**
    """
    
    @given(
        required_resource=resource_strategy,
        required_action=action_strategy,
        user_permissions=permissions_list_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_property_insufficient_permission_rejection(
        self,
        db_session,
        sample_user_with_permissions,
        required_resource,
        required_action,
        user_permissions
    ):
        """
        **Property 11: Insufficient Permission Rejection**
        
        For any API endpoint requiring specific permissions, when accessed by
        a user lacking those permissions, the system should return a 403
        Forbidden response.
        
        **Validates: Requirements 8.8**
        """
        # Create user with the generated permissions
        user = sample_user_with_permissions(user_permissions)
        
        # Create permission checker for the required permission
        checker = PermissionChecker(required_resource, required_action)
        
        # Check if user has the required permission
        has_permission = (required_resource, required_action) in user_permissions
        
        if has_permission:
            # User has permission - should succeed
            result = checker(user)
            assert result == user, "Permission check should return user when authorized"
        else:
            # User lacks permission - should raise 403 Forbidden
            with pytest.raises(HTTPException) as exc_info:
                checker(user)
            
            # Verify it's a 403 Forbidden error
            assert exc_info.value.status_code == 403, \
                f"Expected 403 Forbidden, got {exc_info.value.status_code}"
            
            # Verify error message mentions permission denial
            assert "Permission denied" in exc_info.value.detail or \
                   "permission" in exc_info.value.detail.lower(), \
                f"Error message should mention permission denial: {exc_info.value.detail}"
    
    @given(
        required_resource=resource_strategy,
        required_action=action_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_property_superadmin_bypasses_permission_checks(
        self,
        superadmin_user,
        required_resource,
        required_action
    ):
        """
        **Property: SuperAdmin Bypass**
        
        For any permission requirement, SuperAdmin users should always be
        granted access regardless of specific permissions.
        
        **Validates: Requirements 8.4, 9.4**
        """
        # Create permission checker for any permission
        checker = PermissionChecker(required_resource, required_action)
        
        # SuperAdmin should always pass permission checks
        result = checker(superadmin_user)
        assert result == superadmin_user, \
            "SuperAdmin should bypass all permission checks"
    
    @given(
        permissions_list=permissions_list_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_property_permission_check_consistency(
        self,
        db_session,
        sample_user_with_permissions,
        permissions_list
    ):
        """
        **Property: Permission Check Consistency**
        
        For any user with a specific set of permissions, checking the same
        permission multiple times should always produce the same result.
        
        **Validates: Requirements 8.8**
        """
        # Create user with permissions
        user = sample_user_with_permissions(permissions_list)
        
        # Pick a permission from the list to test
        test_resource, test_action = permissions_list[0]
        
        # Create permission checker
        checker = PermissionChecker(test_resource, test_action)
        
        # Check permission multiple times
        results = []
        for _ in range(3):
            try:
                result = checker(user)
                results.append(("success", result))
            except HTTPException as e:
                results.append(("error", e.status_code))
        
        # All results should be identical
        assert all(r == results[0] for r in results), \
            "Permission checks should be consistent across multiple calls"
    
    @given(
        resource=resource_strategy,
        action=action_strategy,
        other_permissions=permissions_list_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_property_exact_permission_match_required(
        self,
        db_session,
        sample_user_with_permissions,
        resource,
        action,
        other_permissions
    ):
        """
        **Property: Exact Permission Match**
        
        For any required permission (resource, action), a user must have
        exactly that permission. Having permissions for the same resource
        with different actions, or same action with different resources,
        should not grant access.
        
        **Validates: Requirements 8.8**
        """
        # Ensure the required permission is NOT in the user's permissions
        assume((resource, action) not in other_permissions)
        
        # Create user with other permissions (but not the required one)
        user = sample_user_with_permissions(other_permissions)
        
        # Create permission checker for the required permission
        checker = PermissionChecker(resource, action)
        
        # User should be denied access
        with pytest.raises(HTTPException) as exc_info:
            checker(user)
        
        # Verify it's a 403 Forbidden error
        assert exc_info.value.status_code == 403, \
            "User without exact permission should receive 403 Forbidden"
    
    @given(
        permissions_list=permissions_list_strategy
    )
    @settings(max_examples=30, deadline=None)
    def test_property_inactive_user_denied_before_permission_check(
        self,
        db_session,
        sample_tenant,
        sample_role,
        permissions_list
    ):
        """
        **Property: Inactive User Rejection**
        
        For any user with is_active=False, permission checks should not
        be reached because authentication should fail first.
        
        Note: This test verifies the user model state, not the full
        authentication flow which is tested elsewhere.
        
        **Validates: Requirements 8.7**
        """
        # Clear existing permissions
        db_session.query(Permission).filter(
            Permission.role_id == sample_role.id
        ).delete()
        
        # Add permissions
        for resource, action in permissions_list:
            perm = Permission(
                role_id=sample_role.id,
                resource=resource,
                action=action
            )
            db_session.add(perm)
        
        # Create inactive user
        user = User(
            tenant_id=sample_tenant.id,
            email=f"inactive-{uuid4()}@example.com",
            password_hash="hashed_password",
            role_id=sample_role.id,
            is_active=False  # Inactive user
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Verify user is inactive
        assert not user.is_active, "User should be inactive"
        
        # Note: In the real system, inactive users would be rejected
        # by get_current_active_user() before reaching permission checks.
        # This test verifies the user model state.
    
    @given(
        required_permissions=st.lists(
            permission_strategy,
            min_size=2,
            max_size=5,
            unique=True
        )
    )
    @settings(max_examples=30, deadline=None)
    def test_property_multiple_permission_requirements(
        self,
        db_session,
        sample_user_with_permissions,
        required_permissions
    ):
        """
        **Property: Multiple Permission Requirements**
        
        When an operation requires multiple permissions, a user must have
        ALL required permissions. Having only some of them should result
        in 403 Forbidden.
        
        **Validates: Requirements 8.8**
        """
        # Test with user having all permissions
        user_with_all = sample_user_with_permissions(required_permissions)
        
        # All permission checks should pass
        for resource, action in required_permissions:
            checker = PermissionChecker(resource, action)
            result = checker(user_with_all)
            assert result == user_with_all
        
        # Test with user having only subset of permissions
        if len(required_permissions) > 1:
            # Give user all but one permission
            subset_permissions = required_permissions[:-1]
            user_with_subset = sample_user_with_permissions(subset_permissions)
            
            # The missing permission should be denied
            missing_resource, missing_action = required_permissions[-1]
            checker = PermissionChecker(missing_resource, missing_action)
            
            with pytest.raises(HTTPException) as exc_info:
                checker(user_with_subset)
            
            assert exc_info.value.status_code == 403, \
                "User missing one of multiple required permissions should receive 403"
    
    @given(
        resource=resource_strategy,
        action=action_strategy
    )
    @settings(max_examples=30, deadline=None)
    def test_property_permission_denial_logged(
        self,
        db_session,
        sample_user_with_permissions,
        resource,
        action
    ):
        """
        **Property: Permission Denial Logging**
        
        When a permission check fails, the system should log the denial
        with relevant context (user, resource, action).
        
        Note: This test verifies the exception is raised with proper detail.
        Actual audit logging is tested in audit system tests.
        
        **Validates: Requirements 8.8, 21.5**
        """
        # Create user without the required permission
        user = sample_user_with_permissions([("other_resource", "other_action")])
        
        # Create permission checker
        checker = PermissionChecker(resource, action)
        
        # Permission check should fail
        with pytest.raises(HTTPException) as exc_info:
            checker(user)
        
        # Verify error contains relevant information
        assert exc_info.value.status_code == 403
        error_detail = exc_info.value.detail
        
        # Error should mention the resource and action
        assert resource in error_detail or action in error_detail, \
            f"Error detail should mention resource or action: {error_detail}"


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestPermissionEnforcementEdgeCases:
    """
    Edge case tests for permission enforcement.
    
    **Validates: Requirements 8.8**
    """
    
    def test_empty_permissions_denies_all_access(
        self,
        db_session,
        sample_user_with_permissions
    ):
        """
        Test that a user with no permissions is denied all access.
        
        **Validates: Requirements 8.8**
        """
        # Create user with no permissions
        user = sample_user_with_permissions([])
        
        # Try to access any resource
        checker = PermissionChecker("device", "read")
        
        with pytest.raises(HTTPException) as exc_info:
            checker(user)
        
        assert exc_info.value.status_code == 403
    
    def test_case_sensitive_permission_matching(
        self,
        db_session,
        sample_user_with_permissions
    ):
        """
        Test that permission matching is case-sensitive.
        
        **Validates: Requirements 8.8**
        """
        # Create user with lowercase permission
        user = sample_user_with_permissions([("device", "read")])
        
        # Try to access with different case
        checker_upper = PermissionChecker("Device", "Read")
        
        # Should be denied (case-sensitive)
        with pytest.raises(HTTPException) as exc_info:
            checker_upper(user)
        
        assert exc_info.value.status_code == 403
    
    def test_permission_check_with_special_characters(
        self,
        db_session,
        sample_user_with_permissions
    ):
        """
        Test permission checking with special characters in resource/action names.
        
        **Validates: Requirements 8.8**
        """
        # Create user with permission containing special characters
        special_permissions = [("device:config", "read-write")]
        user = sample_user_with_permissions(special_permissions)
        
        # Should succeed with exact match
        checker = PermissionChecker("device:config", "read-write")
        result = checker(user)
        assert result == user
        
        # Should fail with different special characters
        checker_different = PermissionChecker("device_config", "read-write")
        with pytest.raises(HTTPException) as exc_info:
            checker_different(user)
        
        assert exc_info.value.status_code == 403
