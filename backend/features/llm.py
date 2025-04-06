from fastapi import HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from logger_config import setup_logger
from cosmos_db import cosmos_client

# Set up logger
logger = setup_logger(__name__)

class LLMProvider(BaseModel):
    provider: str
    api_key: str = Field(..., min_length=1)
    model: Optional[str] = None
    deployment_name: Optional[str] = None
    endpoint: Optional[str] = None
    api_version: Optional[str] = None

class LLMAccounts(BaseModel):
    default: str
    providers: List[LLMProvider]
    
    @validator('default')
    def validate_default(cls, v, values):
        if 'providers' in values:
            providers = [p.provider for p in values['providers']]
            if v not in providers:
                raise ValueError(f"Default provider '{v}' must be one of: {providers}")
        return v

class LLMAccountCreate(BaseModel):
    provider: str = Field(..., min_length=1)
    api_key: str = Field(..., min_length=1)
    model: Optional[str] = None
    deployment_name: Optional[str] = None
    endpoint: Optional[str] = None
    api_version: Optional[str] = None
    user_id: str = Field(default="roundtable_ai_admin", min_length=1)

class LLMAccountUpdate(LLMAccountCreate):
    pass

async def create_llm_account(llm: LLMAccountCreate):
    """Create a new LLM account."""
    try:
        logger.info("Creating new LLM account for provider: %s", llm.provider)
        
        # Get existing LLM accounts
        user_data = await cosmos_client.get_user_data(llm.user_id)
        if not user_data:
            logger.error("User not found: %s", llm.user_id)
            raise HTTPException(status_code=404, detail="User not found")
            
        llm_accounts = user_data.get('llmAccounts', {})
        providers = llm_accounts.get('providers', [])
        
        # Check if provider already exists
        if any(p['provider'] == llm.provider for p in providers):
            logger.error("Provider already exists: %s", llm.provider)
            raise HTTPException(status_code=400, detail=f"Provider '{llm.provider}' already exists")
            
        # Create provider data
        provider_data = {
            "provider": llm.provider,
            "api_key": llm.api_key
        }
        if llm.model:
            provider_data["model"] = llm.model
        if llm.deployment_name:
            provider_data["deployment_name"] = llm.deployment_name
        if llm.endpoint:
            provider_data["endpoint"] = llm.endpoint
        if llm.api_version:
            provider_data["api_version"] = llm.api_version
            
        # If this is the first provider, set it as default
        if not providers:
            llm_accounts['default'] = llm.provider
            
        providers.append(provider_data)
        llm_accounts['providers'] = providers
        
        # Update user data
        await cosmos_client.update_user(llm.user_id, {'llmAccounts': llm_accounts})
        
        logger.info("Successfully created LLM account for provider: %s", llm.provider)
        return {"message": f"LLM account for provider '{llm.provider}' created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating LLM account: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while creating LLM account")

async def update_llm_account(provider: str, llm: LLMAccountUpdate):
    """Update an LLM account."""
    try:
        logger.info("Updating LLM account for provider: %s", provider)
        
        # Get existing LLM accounts
        user_data = await cosmos_client.get_user_data(llm.user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
            
        llm_accounts = user_data.get('llmAccounts', {})
        providers = llm_accounts.get('providers', [])
        
        # Find and update provider
        for p in providers:
            if p['provider'] == provider:
                p.update({
                    "api_key": llm.api_key
                })
                if llm.model:
                    p["model"] = llm.model
                if llm.deployment_name:
                    p["deployment_name"] = llm.deployment_name
                if llm.endpoint:
                    p["endpoint"] = llm.endpoint
                if llm.api_version:
                    p["api_version"] = llm.api_version
                break
        else:
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")
            
        await cosmos_client.update_user(llm.user_id, {'llmAccounts': llm_accounts})
        
        logger.info("Successfully updated LLM account for provider: %s", provider)
        return {"message": f"LLM account for provider '{provider}' updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating LLM account: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while updating LLM account")

async def delete_llm_account(provider: str, user_id: str):
    """Delete an LLM account."""
    try:
        logger.info("Deleting LLM account for provider: %s", provider)
        
        # Get existing LLM accounts
        user_data = await cosmos_client.get_user_data(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
            
        llm_accounts = user_data.get('llmAccounts', {})
        
        # Cannot delete default provider
        if llm_accounts.get('default') == provider:
            raise HTTPException(status_code=400, detail="Cannot delete the default provider")
            
        # Remove provider
        providers = [p for p in llm_accounts.get('providers', []) if p['provider'] != provider]
        if len(providers) == len(llm_accounts.get('providers', [])):
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")
            
        llm_accounts['providers'] = providers
        
        await cosmos_client.update_user(user_id, {'llmAccounts': llm_accounts})
        
        logger.info("Successfully deleted LLM account for provider: %s", provider)
        return {"message": f"LLM account for provider '{provider}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting LLM account: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while deleting LLM account")

async def get_llm_accounts(user_id: str):
    """Get all LLM accounts for a user."""
    try:
        logger.info("Fetching LLM accounts for user: %s", user_id)
        
        user_data = await cosmos_client.get_user_data(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
            
        llm_accounts = user_data.get('llmAccounts', {'default': '', 'providers': []})
        
        logger.info("Successfully retrieved LLM accounts")
        return llm_accounts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching LLM accounts: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while fetching LLM accounts")

async def set_default_provider(provider: str, user_id: str):
    """Set the default LLM provider."""
    try:
        logger.info("Setting default LLM provider to: %s", provider)
        
        # Get existing LLM accounts
        user_data = await cosmos_client.get_user_data(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
            
        llm_accounts = user_data.get('llmAccounts', {})
        providers = llm_accounts.get('providers', [])
        
        # Verify provider exists
        if not any(p['provider'] == provider for p in providers):
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")
            
        # Update default provider
        llm_accounts['default'] = provider
        
        await cosmos_client.update_user(user_id, {'llmAccounts': llm_accounts})
        
        logger.info("Successfully set default provider to: %s", provider)
        return {"message": f"Default provider set to '{provider}' successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error setting default provider: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while setting default provider")