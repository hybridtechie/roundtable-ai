import os
import requests
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jws, jwt, ExpiredSignatureError, JWTError, JWSError
from jose.exceptions import JWTClaimsError
from pydantic import BaseModel
from typing import Annotated
from logger_config import setup_logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logger
logger = setup_logger(__name__)

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")  # Keep for potential future use with access tokens
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")  # Add Client ID for ID token validation

if not AUTH0_DOMAIN or not AUTH0_CLIENT_ID:
    logger.warning("Auth0 environment variables (AUTH0_DOMAIN, AUTH0_CLIENT_ID) are not fully configured.")
    # Depending on strictness, you might raise an error here
    # raise EnvironmentError("Auth0 environment variables not set")

jwks = {}
if AUTH0_DOMAIN:
    try:
        jwks_endpoint = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        response = requests.get(jwks_endpoint)
        response.raise_for_status()  # Raise an exception for bad status codes
        jwks = response.json().get("keys", [])
        if not jwks:
            logger.error("No keys found in JWKS endpoint: %s", jwks_endpoint)
    except requests.exceptions.RequestException as e:
        logger.error("Failed to fetch JWKS: %s", e, exc_info=True)
        # Handle the error appropriately, maybe raise or use a default empty jwks
    except Exception as e:
        logger.error("An unexpected error occurred while fetching JWKS: %s", e, exc_info=True)


security = HTTPBearer()


class UserClaims(BaseModel):
    """Pydantic model for expected user claims in the token."""

    name: str
    email: str
    # Add other claims you expect or need, e.g., sub (subject/user ID)
    # sub: str


def find_public_key(kid: str):
    """Finds the appropriate public key from the JWKS based on the key ID (kid)."""
    if not jwks:
        logger.error("JWKS keys are not available. Cannot find public key.")
        raise HTTPException(status_code=500, detail="Authentication service configuration error: JWKS not loaded.")

    for key in jwks:
        if key.get("kid") == kid:
            # Typically, you'd convert the JWK to a PEM format or use it directly
            # depending on the library. `python-jose` handles JWK dictionaries directly.
            return key
    logger.warning("Public key not found for kid: %s", kid)
    raise HTTPException(status_code=401, detail=f"Public key not found for kid: {kid}")


def validate_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> UserClaims:
    if not AUTH0_DOMAIN or not AUTH0_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Auth0 configuration missing on server.")

    token = credentials.credentials
    try:
        unverified_headers = jws.get_unverified_header(token)
        public_key = find_public_key(unverified_headers.get("kid"))

        token_payload = jwt.decode(
            token=token,
            key=public_key,  # Provide the JWK dictionary
            algorithms=["RS256"],  # Specify the expected algorithm
            audience=AUTH0_CLIENT_ID,  # Validate the audience (client ID for ID tokens)
            issuer=f"https://{AUTH0_DOMAIN}/",  # Validate the issuer
        )

        # Extract claims and return as UserClaims object
        # Ensure required claims exist
        if "name" not in token_payload or "email" not in token_payload:
            logger.error("Token missing required claims (name, email): %s", token_payload)
            raise HTTPException(status_code=401, detail="Token missing required claims.")

        return UserClaims(
            name=token_payload["name"],
            email=token_payload["email"],
            # sub=token_payload.get("sub") # Example: include subject if needed
        )
    except ExpiredSignatureError:
        logger.warning("Token validation failed: Expired signature")
        raise HTTPException(status_code=401, detail="Token has expired.")
    except JWTClaimsError as error:
        logger.warning("Token validation failed: Invalid claims - %s", str(error))
        raise HTTPException(status_code=401, detail=f"Invalid token claims: {error}")
    except JWTError as error:  # Catch broader JWT errors
        logger.warning("Token validation failed: JWTError - %s", str(error))
        raise HTTPException(status_code=401, detail=f"Invalid token: {error}")
    except JWSError as error:  # Catch JOSE library specific errors
        logger.error("Token validation failed: JWSError - %s", str(error), exc_info=True)
        raise HTTPException(status_code=401, detail=f"Token validation error: {error}")
    except HTTPException as http_exc:  # Re-raise HTTPExceptions from find_public_key
        raise http_exc
    except Exception as error:  # Catch unexpected errors during validation
        logger.error("Unexpected error during token validation: %s", str(error), exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during authentication.")


# Example of how to use the dependency in an endpoint (will be used in routers)
# from fastapi import APIRouter
# router = APIRouter()
# @router.get("/secure-data")
# async def get_secure_data(current_user: UserClaims = Depends(validate_token)):
#     return {"message": f"Hello {current_user.name} ({current_user.email})", "data": "secure"}
