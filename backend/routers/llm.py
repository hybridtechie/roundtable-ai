from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from logger_config import setup_logger
from features.llm import create_llm_account, update_llm_account, delete_llm_account, get_llm_accounts, set_default_provider, LLMAccountCreate, LLMAccountUpdate
from models import LLMAccountResponse, ListLLMAccountsResponse, DeleteResponse
from auth import UserClaims, validate_token

logger = setup_logger(__name__)

router = APIRouter(prefix="/llm-account", tags=["LLM Accounts"])


@router.post("", response_model=LLMAccountResponse, status_code=201, summary="Create or update an LLM account configuration")
async def create_llm_account_endpoint(llm: LLMAccountCreate, current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        llm.user_id = user_id
        logger.info("User '%s' attempting to create/update LLM account for provider: %s", user_id, llm.provider)
        result = await create_llm_account(llm)
        logger.info("Successfully created/updated LLM account for provider %s, user %s", llm.provider, user_id)
        return result
    except Exception as e:
        logger.error("Failed to create/update LLM account for provider %s, user %s: %s", llm.provider, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create LLM account: {str(e)}")


@router.get("s", response_model=ListLLMAccountsResponse, summary="List all LLM account configurations for the user")
async def list_llm_accounts_endpoint(current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        logger.info("Fetching LLM accounts for user: %s", user_id)
        llm_config = await get_llm_accounts(user_id)
        logger.info("Successfully retrieved %d LLM accounts and default '%s' for user: %s", len(llm_config.get("providers", [])), llm_config.get("default"), user_id)
        return {"accounts": llm_config.get("providers", []), "default": llm_config.get("default")}
    except Exception as e:
        logger.error("Failed to fetch LLM accounts for user %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch LLM accounts: {str(e)}")


@router.put("/{provider}", response_model=LLMAccountResponse, summary="Update an existing LLM account configuration")
async def update_llm_account_endpoint(provider: str, llm: LLMAccountUpdate, current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        llm.user_id = user_id
        logger.info("User '%s' attempting to update LLM account for provider: %s", user_id, provider)
        result = await update_llm_account(provider, llm)
        if result is None:
            logger.warning("LLM account update failed: Provider %s not found for user %s", provider, user_id)
            raise HTTPException(status_code=404, detail="LLM account not found or update failed")
        logger.info("Successfully updated LLM account for provider %s, user %s", provider, user_id)
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to update LLM account for provider %s, user %s: %s", provider, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update LLM account: {str(e)}")


@router.delete("/{provider}", response_model=DeleteResponse, summary="Delete an LLM account configuration")
async def delete_llm_account_endpoint(provider: str, current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        logger.info("User '%s' attempting to delete LLM account for provider: %s", user_id, provider)
        result = await delete_llm_account(provider, user_id)
        logger.info("Successfully deleted LLM account for provider %s, user %s", provider, user_id)
        return {"deleted_id": provider}
    except Exception as e:
        logger.error("Failed to delete LLM account for provider %s, user %s: %s", provider, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete LLM account: {str(e)}")


@router.put("/{provider}/set-default", response_model=LLMAccountResponse, summary="Set an LLM provider as the default for the user")
async def set_default_provider_endpoint(provider: str, current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        logger.info("User '%s' attempting to set default provider to: %s", user_id, provider)
        result = await set_default_provider(provider, user_id)
        if result is None:
            logger.warning("Failed to set default provider: Provider %s not found for user %s", provider, user_id)
            raise HTTPException(status_code=404, detail="LLM provider not found")
        logger.info("Successfully set default provider to %s for user %s", provider, user_id)
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to set default provider to %s for user %s: %s", provider, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to set default provider: {str(e)}")
