from fastapi import APIRouter, Depends, HTTPException
from typing import List
from logger_config import setup_logger

from features.group import create_group, get_group, update_group, delete_group, list_groups, GroupCreate, GroupUpdate

from models import GroupResponse, ListGroupsResponse, DeleteResponse

from auth import UserClaims, validate_token

logger = setup_logger(__name__)

router = APIRouter(prefix="/group", tags=["Groups"])

@router.post("", response_model=GroupResponse, status_code=201, summary="Create a new group")
async def create_group_endpoint(group: GroupCreate, current_user: UserClaims = Depends(validate_token)):
    """
    Creates a new group associated with the authenticated user.
    Requires group details in the request body and a valid authentication token.
    """
    try:
        user_id = current_user.email
        logger.info("User '%s' attempting to create new group: %s", user_id, group.name)
        group.user_id = user_id
        created_group = await create_group(group)
        logger.info("Successfully created group '%s' with ID: %s for user '%s'", created_group.name, created_group.id, user_id)
        return created_group
    except Exception as e:
        logger.error("User '%s' failed to create group '%s': %s", user_id, group.name, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create group: {str(e)}")

@router.get("s", response_model=ListGroupsResponse, summary="List all groups for the authenticated user")
async def list_groups_endpoint(current_user: UserClaims = Depends(validate_token)):
    """
    Retrieves a list of groups associated with the authenticated user.
    Requires a valid authentication token.
    """
    try:
        user_id = current_user.email
        logger.info("Fetching all groups for user: %s", user_id)
        result = await list_groups(user_id)
        logger.info("Successfully retrieved %d groups for user: %s", len(result.get("groups", [])), user_id)
        return result
    except Exception as e:
        logger.error("Failed to fetch groups for user %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch groups: {str(e)}")

@router.get("/{group_id}", response_model=GroupResponse, summary="Get a specific group")
async def get_group_endpoint(group_id: str, current_user: UserClaims = Depends(validate_token)):
    """
    Retrieves details for a specific group by its ID, ensuring it belongs to the authenticated user.
    Requires `group_id` in the path and a valid authentication token.
    """
    try:
        user_id = current_user.email
        logger.info("Fetching group_id: %s for user: %s", group_id, user_id)
        group = await get_group(group_id, user_id)
        if group is None:
            logger.warning("Group %s not found for user %s", group_id, user_id)
            raise HTTPException(status_code=404, detail="Group not found or access denied")
        logger.info("Successfully retrieved group: %s", group_id)
        return group
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to fetch group %s for user %s: %s", group_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch group: {str(e)}")

@router.put("/{group_id}", response_model=GroupResponse, summary="Update an existing group")
async def update_group_endpoint(group_id: str, group: GroupUpdate, current_user: UserClaims = Depends(validate_token)):
    """
    Updates an existing group's details, ensuring it belongs to the authenticated user.
    Requires `group_id` in the path, update data in the request body, and a valid authentication token.
    """
    try:
        user_id = current_user.email
        logger.info("User '%s' attempting to update group_id: %s", user_id, group_id)
        group.user_id = user_id
        updated_group = await update_group(group_id, group)
        if updated_group is None:
            logger.warning("Group %s not found or update failed for user %s", group_id, user_id)
            raise HTTPException(status_code=404, detail="Group not found or update failed")
        logger.info("Successfully updated group: %s by user %s", group_id, user_id)
        return updated_group
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to update group %s for user %s: %s", group_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update group: {str(e)}")

@router.delete("/{group_id}", response_model=DeleteResponse, summary="Delete a group")
async def delete_group_endpoint(group_id: str, current_user: UserClaims = Depends(validate_token)):
    """
    Deletes a group by its ID, ensuring it belongs to the authenticated user.
    Requires `group_id` in the path and a valid authentication token.
    """
    try:
        user_id = current_user.email
        logger.info("User '%s' attempting to delete group_id: %s", user_id, group_id)
        result = await delete_group(group_id, user_id)
        logger.info("Successfully deleted group: %s by user %s", group_id, user_id)
        return result
    except Exception as e:
        logger.error("Failed to delete group %s for user %s: %s", group_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete group: {str(e)}")
