from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from logger_config import setup_logger

# Feature imports
from features.llm import (
    create_llm_account, update_llm_account, delete_llm_account,
    get_llm_accounts, set_default_provider,
    LLMAccountCreate, LLMAccountUpdate # Input models
)

# Model imports
# Use absolute import from 'backend' directory perspective
from models import LLMAccountResponse, ListLLMAccountsResponse, DeleteResponse # Assuming DeleteResponse is suitable for LLM delete

# Auth imports
from auth import UserClaims, validate_token

# Logger setup
logger = setup_logger(__name__)

# Create an APIRouter instance
router = APIRouter(
    prefix="/llm-account",    # Prefix for all routes in this router
    tags=["LLM Accounts"]     # Tag for OpenAPI documentation
)

# --- LLM Account Management Endpoints ---

# Create LLM Account
@router.post("", response_model=LLMAccountResponse, status_code=201, summary="Create or update an LLM account configuration")
async def create_llm_account_endpoint(llm: LLMAccountCreate, current_user: UserClaims = Depends(validate_token)):
    """
    Creates or updates an LLM provider configuration for the authenticated user.
    Requires LLM account details in the request body and a valid authentication token.
    """
    try:
        user_id = current_user.email
        llm.user_id = user_id # Assign user_id from token
        logger.info("User '%s' attempting to create/update LLM account for provider: %s", user_id, llm.provider)
        # Assuming create_llm_account returns the created/updated account object matching LLMAccountResponse
        result = await create_llm_account(llm)
        logger.info("Successfully created/updated LLM account for provider %s, user %s", llm.provider, user_id)
        return result
    except Exception as e:
        logger.error("Failed to create/update LLM account for provider %s, user %s: %s", llm.provider, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create LLM account: {str(e)}")


# List LLM Accounts
@router.get("s", response_model=ListLLMAccountsResponse, summary="List all LLM account configurations for the user") # Route is /llm-accounts
async def list_llm_accounts_endpoint(current_user: UserClaims = Depends(validate_token)):
    """
    Retrieves a list of LLM account configurations associated with the authenticated user.
    Requires a valid authentication token.
    """
    try:
        user_id = current_user.email
        logger.info("Fetching LLM accounts for user: %s", user_id)
        # Assuming get_llm_accounts returns a dict like {'providers': [...], 'default': '...'}
        llm_config = await get_llm_accounts(user_id)
        logger.info("Successfully retrieved %d LLM accounts and default '%s' for user: %s", len(llm_config.get('providers', [])), llm_config.get('default'), user_id)
        # Structure the response to match ListLLMAccountsResponse model
        return {"accounts": llm_config.get('providers', []), "default": llm_config.get('default')}
    except Exception as e:
        logger.error("Failed to fetch LLM accounts for user %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch LLM accounts: {str(e)}")


# Update LLM Account (Note: Original POST might handle updates, but PUT is more conventional)
# Keeping PUT as per original main.py structure for now.
@router.put("/{provider}", response_model=LLMAccountResponse, summary="Update an existing LLM account configuration")
async def update_llm_account_endpoint(provider: str, llm: LLMAccountUpdate, current_user: UserClaims = Depends(validate_token)):
    """
    Updates an existing LLM provider configuration for the authenticated user.
    Requires provider name in path, update data in body, and a valid token.
    """
    try:
        user_id = current_user.email
        llm.user_id = user_id # Assign user_id from token
        logger.info("User '%s' attempting to update LLM account for provider: %s", user_id, provider)
        # Assuming update_llm_account returns the updated account object
        result = await update_llm_account(provider, llm)
        if result is None: # Handle case where account doesn't exist for the user
            logger.warning("LLM account update failed: Provider %s not found for user %s", provider, user_id)
            raise HTTPException(status_code=404, detail="LLM account not found or update failed")
        logger.info("Successfully updated LLM account for provider %s, user %s", provider, user_id)
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to update LLM account for provider %s, user %s: %s", provider, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update LLM account: {str(e)}")


# Delete LLM Account
@router.delete("/{provider}", response_model=DeleteResponse, summary="Delete an LLM account configuration") # Using generic DeleteResponse
async def delete_llm_account_endpoint(provider: str, current_user: UserClaims = Depends(validate_token)):
    """
    Deletes an LLM provider configuration for the authenticated user.
    Requires provider name in the path and a valid authentication token.
    """
    try:
        user_id = current_user.email
        logger.info("User '%s' attempting to delete LLM account for provider: %s", user_id, provider)
        # Assuming delete_llm_account returns a dict like {"deleted_provider": provider} or similar
        # Adapt the response model or return value as needed. Using DeleteResponse for now.
        result = await delete_llm_account(provider, user_id)
        # Add check if deletion failed (e.g., provider not found for user)
        # if result is None:
        #     raise HTTPException(status_code=404, detail="LLM account not found or cannot be deleted")
        logger.info("Successfully deleted LLM account for provider %s, user %s", provider, user_id)
        # Return a standard delete response
        return {"deleted_id": provider} # Adapt if delete_llm_account returns something different
    except Exception as e:
        logger.error("Failed to delete LLM account for provider %s, user %s: %s", provider, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete LLM account: {str(e)}")


# Set Default LLM Provider
@router.put("/{provider}/set-default", response_model=LLMAccountResponse, summary="Set an LLM provider as the default for the user")
async def set_default_provider_endpoint(provider: str, current_user: UserClaims = Depends(validate_token)):
    """
    Sets a specific LLM provider configuration as the default for the authenticated user.
    Requires provider name in the path and a valid authentication token.
    """
    try:
        user_id = current_user.email
        logger.info("User '%s' attempting to set default provider to: %s", user_id, provider)
        # Assuming set_default_provider returns the updated default account object
        result = await set_default_provider(provider, user_id)
        if result is None: # Handle case where provider doesn't exist for user
             logger.warning("Failed to set default provider: Provider %s not found for user %s", provider, user_id)
             raise HTTPException(status_code=404, detail="LLM provider not found")
        logger.info("Successfully set default provider to %s for user %s", provider, user_id)
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to set default provider to %s for user %s: %s", provider, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to set default provider: {str(e)}")