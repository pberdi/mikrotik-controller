"""
User service for managing users and authentication.

This module provides the UserService class for user management operations
including CRUD operations, role assignment, and password management.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from .base_service import BaseService
from ..models.user import User
from ..models.role import Role
from ..core.security import hash_password, verify_password
from ..schemas.user import UserCreate, UserUpdate, UserFilterParams

logger = logging.getLogger(__name__)


class UserService(BaseService):
    """
    Service class for user management operations.
    
    Provides CRUD operations for users with tenant isolation,
    role assignment, and password management.
    """
    
    def list_users(
        self,
        filters: Optional[UserFilterParams] = None,
        page: int = 1,
        page_size: int = 50,
        allow_cross_tenant: bool = False
    ) -> Dict[str, Any]:
        """
        List users with pagination and filtering.
        
        Args:
            filters: Filter parameters for user listing.
            page: Page number (1-based).
            page_size: Number of items per page.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            dict: Paginated user results with metadata.
        """
        # Start with base query including relationships for efficient loading
        query = self.db.query(User).options(
            joinedload(User.role),
            joinedload(User.tenant)
        )
        
        # Apply tenant filtering
        query = self._apply_tenant_filter(query, User, allow_cross_tenant)
        
        # Apply filters if provided
        if filters:
            filter_dict = filters.model_dump(exclude_none=True)
            
            # Handle email search (partial match)
            if 'email' in filter_dict:
                email_search = filter_dict.pop('email')
                query = query.filter(User.email.ilike(f"%{email_search}%"))
            
            # Apply remaining filters
            for field, value in filter_dict.items():
                if hasattr(User, field) and value is not None:
                    if isinstance(value, list):
                        query = query.filter(getattr(User, field).in_(value))
                    else:
                        query = query.filter(getattr(User, field) == value)
        
        # Order by email
        query = query.order_by(User.email)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        users = query.offset(offset).limit(page_size).all()
        
        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size
        
        result = {
            "items": users,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        # Log audit event
        self._log_audit_event(
            action="list",
            resource_type="user",
            result="success"
        )
        
        logger.info(
            f"Listed {len(users)} users "
            f"(page {page}/{total_pages}, total: {total_count})"
        )
        
        return result
    
    def get_user(
        self,
        user_id: Union[str, UUID],
        allow_cross_tenant: bool = False
    ) -> Optional[User]:
        """
        Get user by ID with tenant isolation.
        
        Args:
            user_id: ID of the user to retrieve.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            User: User if found and accessible, None otherwise.
        """
        # Use base service method with eager loading
        query = self.db.query(User).options(
            joinedload(User.role),
            joinedload(User.tenant)
        ).filter(User.id == user_id)
        
        query = self._apply_tenant_filter(query, User, allow_cross_tenant)
        user = query.first()
        
        if user:
            # Log audit event
            self._log_audit_event(
                action="get",
                resource_type="user",
                resource_id=user.id,
                result="success"
            )
            
            logger.debug(f"Retrieved user {user_id}")
        else:
            # Log failed access attempt
            self._log_audit_event(
                action="get",
                resource_type="user",
                resource_id=user_id,
                result="not_found"
            )
            
            logger.debug(f"User {user_id} not found or not accessible")
        
        return user
    
    def get_user_by_email(
        self,
        email: str,
        allow_cross_tenant: bool = False
    ) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: Email address of the user.
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            User: User if found and accessible, None otherwise.
        """
        query = self.db.query(User).options(
            joinedload(User.role),
            joinedload(User.tenant)
        ).filter(User.email == email.lower())
        
        query = self._apply_tenant_filter(query, User, allow_cross_tenant)
        user = query.first()
        
        if user:
            logger.debug(f"Retrieved user by email: {email}")
        else:
            logger.debug(f"User with email {email} not found or not accessible")
        
        return user
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Create new user with password hashing.
        
        Args:
            user_data: User creation data including password.
            
        Returns:
            User: Created user.
            
        Raises:
            ValueError: If email already exists or role doesn't exist.
            Exception: If user creation fails.
        """
        try:
            # Check if email already exists
            existing_user = self.db.query(User).filter(
                User.email == user_data.email.lower()
            ).first()
            
            if existing_user:
                raise ValueError(f"User with email {user_data.email} already exists")
            
            # Validate role exists
            role = self.db.query(Role).filter(Role.id == user_data.role_id).first()
            if not role:
                raise ValueError(f"Role {user_data.role_id} not found")
            
            # Hash password
            password_hash = hash_password(user_data.password)
            
            # Create user data without password
            user_dict = user_data.model_dump(exclude={'password'})
            user_dict['email'] = user_data.email.lower()  # Normalize email
            user_dict['password_hash'] = password_hash
            
            # Create user using base service method
            user = self.create_resource(User, user_dict)
            
            logger.info(f"Created user {user.id} with email {user.email}")
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            # Log failure (without sensitive data)
            self._log_audit_event(
                action="create",
                resource_type="user",
                result="error"
            )
            raise
    
    def update_user(
        self,
        user_id: Union[str, UUID],
        user_data: UserUpdate
    ) -> Optional[User]:
        """
        Update existing user.
        
        Args:
            user_id: ID of the user to update.
            user_data: Updated user data.
            
        Returns:
            User: Updated user if found and accessible, None otherwise.
            
        Raises:
            ValueError: If email already exists or role doesn't exist.
        """
        # Get existing user
        user = self.get_user(user_id)
        if not user:
            return None
        
        try:
            # Prepare update data
            update_dict = user_data.model_dump(exclude_none=True, exclude={'password'})
            
            # Check if email is being updated and already exists
            if 'email' in update_dict:
                new_email = update_dict['email'].lower()
                existing_user = self.db.query(User).filter(
                    and_(
                        User.email == new_email,
                        User.id != user_id
                    )
                ).first()
                
                if existing_user:
                    raise ValueError(f"User with email {new_email} already exists")
                
                update_dict['email'] = new_email
            
            # Validate role if being updated
            if 'role_id' in update_dict:
                role = self.db.query(Role).filter(Role.id == update_dict['role_id']).first()
                if not role:
                    raise ValueError(f"Role {update_dict['role_id']} not found")
            
            # Handle password update separately
            if user_data.password:
                update_dict['password_hash'] = hash_password(user_data.password)
            
            # Update user using base service method
            updated_user = self.update_resource(user, update_dict)
            
            logger.info(f"Updated user {user_id}")
            
            return updated_user
            
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="update",
                resource_type="user",
                resource_id=user_id,
                result="error"
            )
            raise
    
    def delete_user(self, user_id: Union[str, UUID]) -> bool:
        """
        Delete (deactivate) existing user.
        
        Note: This sets is_active to False rather than deleting the record
        to preserve audit trail and referential integrity.
        
        Args:
            user_id: ID of the user to delete.
            
        Returns:
            bool: True if user was deactivated, False if not found.
        """
        # Get existing user
        user = self.get_user(user_id)
        if not user:
            return False
        
        try:
            # Deactivate user instead of deleting
            user.is_active = False
            self.db.flush()
            
            # Log audit event
            self._log_audit_event(
                action="deactivate",
                resource_type="user",
                resource_id=user_id,
                result="success"
            )
            
            logger.info(f"Deactivated user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate user {user_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="deactivate",
                resource_type="user",
                resource_id=user_id,
                result="error"
            )
            raise
    
    def activate_user(self, user_id: Union[str, UUID]) -> bool:
        """
        Activate a deactivated user.
        
        Args:
            user_id: ID of the user to activate.
            
        Returns:
            bool: True if user was activated, False if not found.
        """
        # Get existing user
        user = self.get_user(user_id)
        if not user:
            return False
        
        try:
            # Activate user
            user.is_active = True
            self.db.flush()
            
            # Log audit event
            self._log_audit_event(
                action="activate",
                resource_type="user",
                resource_id=user_id,
                result="success"
            )
            
            logger.info(f"Activated user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate user {user_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="activate",
                resource_type="user",
                resource_id=user_id,
                result="error"
            )
            raise
    
    def assign_role(
        self,
        user_id: Union[str, UUID],
        role_id: Union[str, UUID]
    ) -> Optional[User]:
        """
        Assign role to user.
        
        Args:
            user_id: ID of the user.
            role_id: ID of the role to assign.
            
        Returns:
            User: Updated user if found and accessible, None otherwise.
            
        Raises:
            ValueError: If role doesn't exist.
        """
        # Get existing user
        user = self.get_user(user_id)
        if not user:
            return None
        
        try:
            # Validate role exists
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ValueError(f"Role {role_id} not found")
            
            # Capture before state
            before_value = {"role_id": str(user.role_id), "role_name": user.role.name}
            
            # Update role
            user.role_id = role_id
            self.db.flush()
            
            # Refresh to get new role relationship
            self.db.refresh(user)
            
            # Capture after state
            after_value = {"role_id": str(user.role_id), "role_name": user.role.name}
            
            # Log audit event
            self._log_audit_event(
                action="assign_role",
                resource_type="user",
                resource_id=user_id,
                before_value=before_value,
                after_value=after_value,
                result="success"
            )
            
            logger.info(f"Assigned role {role_id} to user {user_id}")
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to assign role to user {user_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="assign_role",
                resource_type="user",
                resource_id=user_id,
                result="error"
            )
            raise
    
    def change_password(
        self,
        user_id: Union[str, UUID],
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password with current password verification.
        
        Args:
            user_id: ID of the user.
            current_password: Current password for verification.
            new_password: New password to set.
            
        Returns:
            bool: True if password was changed, False if current password is incorrect.
            
        Raises:
            ValueError: If user not found.
        """
        # Get existing user
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        try:
            # Verify current password
            if not verify_password(current_password, user.password_hash):
                logger.warning(f"Failed password change attempt for user {user_id}: incorrect current password")
                # Log failed attempt
                self._log_audit_event(
                    action="change_password",
                    resource_type="user",
                    resource_id=user_id,
                    result="incorrect_password"
                )
                return False
            
            # Hash new password
            new_password_hash = hash_password(new_password)
            
            # Update password
            user.password_hash = new_password_hash
            self.db.flush()
            
            # Log audit event (without sensitive data)
            self._log_audit_event(
                action="change_password",
                resource_type="user",
                resource_id=user_id,
                result="success"
            )
            
            logger.info(f"Changed password for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to change password for user {user_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="change_password",
                resource_type="user",
                resource_id=user_id,
                result="error"
            )
            raise
    
    def reset_password(
        self,
        user_id: Union[str, UUID],
        new_password: str
    ) -> bool:
        """
        Reset user password (admin function, no current password verification).
        
        Args:
            user_id: ID of the user.
            new_password: New password to set.
            
        Returns:
            bool: True if password was reset, False if user not found.
        """
        # Get existing user
        user = self.get_user(user_id)
        if not user:
            return False
        
        try:
            # Hash new password
            new_password_hash = hash_password(new_password)
            
            # Update password
            user.password_hash = new_password_hash
            self.db.flush()
            
            # Log audit event (without sensitive data)
            self._log_audit_event(
                action="reset_password",
                resource_type="user",
                resource_id=user_id,
                result="success"
            )
            
            logger.info(f"Reset password for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset password for user {user_id}: {e}")
            # Log failure
            self._log_audit_event(
                action="reset_password",
                resource_type="user",
                resource_id=user_id,
                result="error"
            )
            raise
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email address.
            password: User password.
            
        Returns:
            User: Authenticated user if credentials are valid and user is active, None otherwise.
        """
        try:
            # Validate input parameters
            if not email or not password:
                logger.warning("Authentication failed: missing email or password")
                return None
            
            # Normalize email
            email = email.lower().strip()
            
            # Basic email format validation
            if "@" not in email or len(email) < 5:
                logger.warning(f"Authentication failed: invalid email format {email}")
                return None
            
            # Get user by email (cross-tenant for authentication)
            user = self.db.query(User).options(
                joinedload(User.role),
                joinedload(User.tenant)
            ).filter(User.email == email).first()
            
            if not user:
                logger.debug(f"Authentication failed: user {email} not found")
                # Log failed attempt
                self._log_audit_event(
                    action="authenticate",
                    resource_type="user",
                    result="user_not_found"
                )
                return None
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Authentication failed: user {email} is inactive")
                # Log failed attempt
                self._log_audit_event(
                    action="authenticate",
                    resource_type="user",
                    resource_id=user.id,
                    result="user_inactive"
                )
                return None
            
            # Verify password
            if not verify_password(password, user.password_hash):
                logger.warning(f"Authentication failed: incorrect password for user {email}")
                # Log failed attempt
                self._log_audit_event(
                    action="authenticate",
                    resource_type="user",
                    resource_id=user.id,
                    result="incorrect_password"
                )
                return None
            
            # Log successful authentication
            self._log_audit_event(
                action="authenticate",
                resource_type="user",
                resource_id=user.id,
                result="success"
            )
            
            logger.info(f"User {email} authenticated successfully")
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication error for user {email}: {e}")
            # Log error
            self._log_audit_event(
                action="authenticate",
                resource_type="user",
                result="error"
            )
            return None
    
    def get_user_stats(self, allow_cross_tenant: bool = False) -> Dict[str, Any]:
        """
        Get user statistics for the current tenant.
        
        Args:
            allow_cross_tenant: Whether to allow cross-tenant access for SuperAdmin.
            
        Returns:
            dict: User statistics including counts by role, active/inactive, etc.
        """
        try:
            # Base query with tenant filtering
            query = self.db.query(User).options(joinedload(User.role))
            query = self._apply_tenant_filter(query, User, allow_cross_tenant)
            
            # Get all users for statistics
            users = query.all()
            
            # Calculate statistics
            total_users = len(users)
            active_users = sum(1 for u in users if u.is_active)
            inactive_users = total_users - active_users
            
            # Count by role
            by_role = {}
            for user in users:
                role_name = user.role.name
                by_role[role_name] = by_role.get(role_name, 0) + 1
            
            stats = {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "by_role": by_role
            }
            
            # Log audit event
            self._log_audit_event(
                action="get_stats",
                resource_type="user",
                result="success"
            )
            
            logger.debug(f"Generated user statistics: {total_users} total users")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get user statistics: {e}")
            # Log failure
            self._log_audit_event(
                action="get_stats",
                resource_type="user",
                result="error"
            )
            raise
