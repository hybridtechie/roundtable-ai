from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, Field, validator
from uuid import uuid4
from typing import Optional, List, Dict
import re
from logger_config import setup_logger
from cosmos_db import cosmos_client
from blob_db import blob_db
from features.llm import get_llm_client

logger = setup_logger(__name__)

DEFAULT_CHUNK_SIZE = 10000
DEFAULT_CHUNK_OVERLAP = 250

def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, chunk_overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[str]:
    """Splits text into chunks of a specified size with overlap."""
    if chunk_overlap >= chunk_size:
        raise ValueError("Overlap cannot be larger than chunk size.")

    chunks = []
    start_index = 0
    text_length = len(text)

    while start_index < text_length:
        end_index = start_index + chunk_size
        chunk = text[start_index:end_index]
        chunks.append(chunk)
        start_index += chunk_size - chunk_overlap

        if chunk_overlap == 0 and start_index == end_index:
             break
        if start_index >= text_length:
            break

    if len(chunks) > 1 and chunks[-1] == chunks[-2]:
         chunks.pop()

    if start_index < text_length and text_length - start_index < chunk_size:
         last_chunk = text[start_index:]
         if not chunks or last_chunk != chunks[-1]:
             chunks.append(last_chunk)


    return chunks
def generate_persona_description(participant: "ParticipantBase") -> str:
    """Generate a markdown formatted persona description from participant fields."""
    persona_parts = [f"You are {participant.name} with role {participant.role}. Your details are below:\n"]

    field_sections = [
        ("Professional Background", participant.professional_background),
        ("Industry Experience", participant.industry_experience),
        ("Role Overview", participant.role_overview),
        ("Technical Stack", participant.technical_stack),
        ("Soft Skills", participant.soft_skills),
        ("Core Qualities", participant.core_qualities),
        ("Style Preferences", participant.style_preferences),
        ("Additional Information", participant.additional_info),
    ]

    for section_title, content in field_sections:
        if content:
            persona_parts.append(f"\n## {section_title}\n{content}")

    return "\n".join(persona_parts)


def validate_participant_data(data: dict) -> None:
    """Validate Participant data before creation."""
    try:
        required_fields = [
            ("name", 100),
            ("role", 100),
            ("professional_background", 2000),
            ("industry_experience", 1000),
            ("role_overview", 1000),
            ("technical_stack", 1000),
            ("soft_skills", 1000),
            ("core_qualities", 1000),
            ("style_preferences", 1000),
        ]

        for field, max_length in required_fields:
            if not data.get(field) or not str(data[field]).strip():
                logger.error(f"Validation failed: {field} is empty or whitespace")
                raise HTTPException(status_code=400, detail=f"{field.replace('_', ' ').title()} is required")

            if len(str(data[field])) > max_length:
                logger.error(f"Validation failed: {field} length exceeds {max_length} characters")
                raise HTTPException(status_code=400, detail=f"{field.replace('_', ' ').title()} must be less than {max_length} characters")

        logger.debug("Participant data validation successful")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during participant validation: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during validation")


class ParticipantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., min_length=1, max_length=100)
    professional_background: str = Field(..., min_length=1, max_length=2000)
    industry_experience: str = Field(..., min_length=1, max_length=1000)
    role_overview: str = Field(..., min_length=1, max_length=1000)
    technical_stack: Optional[str] = Field(..., min_length=1, max_length=1000)
    soft_skills: Optional[str] = Field(..., min_length=1, max_length=1000)
    core_qualities: Optional[str] = Field(..., min_length=1, max_length=1000)
    style_preferences: Optional[str] = Field(..., min_length=1, max_length=1000)
    additional_info: Optional[str] = Field(default="", max_length=1000)
    user_id: str = Field(default="roundtable_ai_admin", min_length=1)
    persona_description: Optional[str] = Field(default="", max_length=5000)
    docs: Optional[List[Dict]] = Field(default_factory=list)

    @validator('docs')
    def validate_docs(cls, v):
        if v is None:
            return []
        return v


class ParticipantCreate(ParticipantBase):
    id: Optional[str] = None


class ParticipantUpdate(ParticipantBase):
    pass


class ParticipantResponse(ParticipantBase):
    id: str


async def create_participant(participant: ParticipantCreate) -> ParticipantResponse:
    """Create a new Participant and return the created object."""
    logger.info("Creating new participant with name: %s", participant.name)

    participant_dict = participant.dict(exclude_unset=True)
    validate_participant_data(participant_dict)

    generated_id = participant.id if participant.id else str(uuid4())
    logger.debug("Using participant ID: %s", generated_id)

    try:
        persona_description = generate_persona_description(participant)

        participant_data = {
            "id": generated_id,
            "name": participant.name,
            "role": participant.role,
            "professional_background": participant.professional_background,
            "industry_experience": participant.industry_experience,
            "role_overview": participant.role_overview,
            "technical_stack": participant.technical_stack,
            "soft_skills": participant.soft_skills,
            "core_qualities": participant.core_qualities,
            "style_preferences": participant.style_preferences,
            "additional_info": participant.additional_info,
            "user_id": participant.user_id,
            "persona_description": persona_description,
            "docs": []
        }

        await cosmos_client.add_participant(participant.user_id, participant_data)
        logger.info("Successfully created participant: %s", generated_id)

        return ParticipantResponse(**participant_data)

    except Exception as e:
        logger.error("Error creating participant: %s - Error: %s", generated_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while creating participant")


async def update_participant(participant_id: str, participant: ParticipantUpdate) -> ParticipantResponse:
    """Update a Participant and return the updated object."""
    try:
        logger.info("Updating participant with ID: %s", participant_id)

        # Get current participant to check existence
        current_participant = await cosmos_client.get_participant(participant.user_id, participant_id)
        if not current_participant:
            logger.error("Participant not found with ID: %s", participant_id)
            raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")

        # Validate incoming data
        participant_dict = participant.dict(exclude_unset=True)
        validate_participant_data(participant_dict)

        # Generate persona description
        persona_description = generate_persona_description(participant)

        # Prepare the full data object for update in Cosmos DB
        participant_data = {
            "id": participant_id,
            "name": participant.name,
            "role": participant.role,
            "professional_background": participant.professional_background,
            "industry_experience": participant.industry_experience,
            "role_overview": participant.role_overview,
            "technical_stack": participant.technical_stack,
            "soft_skills": participant.soft_skills,
            "core_qualities": participant.core_qualities,
            "style_preferences": participant.style_preferences,
            "additional_info": participant.additional_info,
            "user_id": participant.user_id,
            "persona_description": persona_description,
            "docs": current_participant.get("docs", [])
        }

        await cosmos_client.update_participant(participant.user_id, participant_id, participant_data)
        logger.info("Successfully updated participant: %s", participant_id)

        return ParticipantResponse(**participant_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating participant %s: %s", participant_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while updating participant")



async def delete_participant(participant_id: str, user_id: str) -> dict:
    """
    Deletes a Participant, associated document chunks from Cosmos DB,
    and associated files from Blob Storage.
    """
    logger.info(f"Initiating deletion for participant ID: {participant_id}, user ID: {user_id}")

    participant_exists = await cosmos_client.get_participant(user_id, participant_id)
    if not participant_exists:
        logger.error(f"Participant not found with ID: {participant_id} for user {user_id}")
        raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")

    try:
        doc_container = cosmos_client.get_participant_docs_container()
        query = "SELECT c.path FROM c WHERE c.participant_id = @participant_id"
        parameters = [{"name": "@participant_id", "value": participant_id}]
        associated_docs = list(doc_container.query_items(
            query=query,
            parameters=parameters,
            partition_key=participant_id
        ))

        unique_blob_paths = {doc.get("path") for doc in associated_docs if doc.get("path")}
        for blob_path in unique_blob_paths:
            try:
                await blob_db.delete_file(user_id, participant_id, blob_path)
                logger.debug(f"Deleted blob file: {blob_path}")
            except Exception as e:
                logger.warning(f"Failed to delete blob file {blob_path} for participant {participant_id}: {str(e)}")

        try:
            await cosmos_client.delete_participant_docs(participant_id, user_id)
            logger.info(f"Successfully deleted document chunks from Cosmos DB for participant {participant_id}.")
        except Exception as e:
            logger.error(f"Failed to delete document chunks from Cosmos DB for participant {participant_id}: {str(e)}", exc_info=True)


        await cosmos_client.delete_participant(user_id, participant_id)
        logger.info(f"Successfully deleted participant record: {participant_id} for user: {user_id}")

        return {"deleted_id": participant_id, "message": "Participant and associated data deleted successfully."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during deletion of participant {participant_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during participant deletion process.")


async def get_participant(participant_id: str, user_id: str) -> ParticipantResponse:
    """Get a specific Participant."""
    try:
        logger.info("Fetching participant with ID: %s for user: %s", participant_id, user_id)
        participant = await cosmos_client.get_participant(user_id, participant_id)

        if not participant:
            logger.error("Participant not found with ID: %s", participant_id)
            raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")

        logger.info("Successfully retrieved participant: %s", participant_id)
        return ParticipantResponse(**participant)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching participant %s: %s", participant_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving participant")


async def list_participants(user_id: str) -> dict:
    """List all Participants for a user."""
    try:
        logger.info("Fetching all participants for user: %s", user_id)
        participants_list = await cosmos_client.list_participants(user_id)

        logger.info("Successfully retrieved %d participants for user: %s", len(participants_list), user_id)
        return {"participants": participants_list}

    except Exception as e:
        logger.error("Error listing participants for user %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving participants")


async def list_participant_documents(participant_id: str, user_id: str) -> dict:
    """
    Lists a summary of documents associated with a participant by querying
    the participant_docs container.
    """
    logger.info(f"Fetching document summaries for participant ID: {participant_id}, user ID: {user_id}")

    # 1. Check Participant Existence
    participant = await cosmos_client.get_participant(user_id, participant_id)
    if not participant:
        logger.error(f"Participant not found with ID: {participant_id}")
        raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")

    try:
        # 2. Query participant_docs container
        doc_container = cosmos_client.get_participant_docs_container()
        # Select fields needed for the summary, including file_id for grouping
        query = "SELECT c.file_id, c.name, c.clean_name, c.path, c.size, c.type, c.chunk_no FROM c WHERE c.participant_id = @participant_id"
        parameters = [{"name": "@participant_id", "value": participant_id}]

        all_chunks = list(doc_container.query_items(
            query=query,
            parameters=parameters,
            partition_key=participant_id # Use partition key
        ))

        # 3. Process and Group Chunks into Document Summaries
        document_summaries = {}
        for chunk in all_chunks:
            file_id = chunk.get("file_id")
            if not file_id:
                logger.warning(f"Found chunk without file_id for participant {participant_id}, skipping.")
                continue

            if file_id not in document_summaries:
                # Initialize summary for this file_id
                document_summaries[file_id] = {
                    "id": file_id, # Use file_id as the document ID in the summary
                    "name": chunk.get("name"),
                    "clean_name": chunk.get("clean_name"),
                    "path": chunk.get("path"),
                    "size": chunk.get("size"),
                    "type": chunk.get("type"),
                    "chunk_count": 0
                }

            # Increment chunk count for this document
            document_summaries[file_id]["chunk_count"] += 1

        # Convert the dictionary of summaries to a list
        summaries_list = list(document_summaries.values())

        logger.info(f"Successfully retrieved summaries for {len(summaries_list)} documents for participant: {participant_id}")
        return {"documents": summaries_list}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents for participant {participant_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving documents")


async def upload_participant_document(participant_id: str, user_id: str, file: UploadFile) -> dict:
    """
    Uploads a document (.txt, .md), chunks it, generates embeddings,
    and stores chunks in the participant_docs container.
    """
    logger.info(f"Uploading document '{file.filename}' for participant ID: {participant_id}, user ID: {user_id}")

    allowed_extensions = {".txt", ".md"}
    file_extension = f".{file.filename.split('.')[-1].lower()}" if '.' in file.filename else ""
    if file_extension not in allowed_extensions:
        logger.error(f"Unsupported file type: {file_extension}")
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}")

    participant = await cosmos_client.get_participant(user_id, participant_id)
    if not participant:
        logger.error(f"Participant not found with ID: {participant_id}")
        raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")

    try:
        await file.seek(0)
        doc_info = await blob_db.upload_file(file, user_id, participant_id)
        file_id = doc_info.get("file_id")
        original_filename = doc_info.get("name")
        clean_filename = doc_info.get("clean_name")
        blob_path = doc_info.get("path")
        file_size = doc_info.get("size")
        file_type = doc_info.get("type")

        if not all([file_id, original_filename, clean_filename, blob_path, file_size, file_type]):
             logger.error("Blob storage upload failed to return complete document info.")
             raise HTTPException(status_code=500, detail="Failed to get complete info from blob storage upload.")

        logger.info(f"File '{original_filename}' uploaded to blob storage at path: {blob_path}")

        await file.seek(0)
        content_bytes = await file.read()
        try:
            text_content = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            logger.error(f"Failed to decode file '{original_filename}' as UTF-8.")
            try:
                await blob_db.delete_file(user_id, participant_id, blob_path)
                logger.info(f"Cleaned up blob file '{blob_path}' due to decoding error.")
            except Exception as cleanup_e:
                logger.error(f"Failed to clean up blob file '{blob_path}' after decoding error: {cleanup_e}")
            raise HTTPException(status_code=400, detail="Failed to decode file content as UTF-8.")

        chunks = chunk_text(text_content)
        logger.info(f"Document '{original_filename}' split into {len(chunks)} chunks.")

        llm_client = await get_llm_client(user_id)

        stored_chunk_ids = []
        for i, chunk in enumerate(chunks):
            chunk_no = i + 1
            chunk_id = f"{user_id}::{participant_id}::{file_id}::{chunk_no}"

            try:
                embeddings = llm_client.generate_embeddings(chunk)
                logger.debug(f"Generated embeddings for chunk {chunk_no}/{len(chunks)} of file {file_id}")
            except Exception as emb_e:
                logger.error(f"Failed to generate embeddings for chunk {chunk_no} of file {file_id}: {emb_e}", exc_info=True)
                try:
                    await blob_db.delete_file(user_id, participant_id, blob_path)
                except Exception as cleanup_e:
                    logger.error(f"Failed to clean up blob file '{blob_path}' after embedding error: {cleanup_e}")
                raise HTTPException(status_code=500, detail=f"Failed to generate embeddings for chunk {chunk_no}.")


            doc_chunk_data = {
                "id": chunk_id,
                "chunk_no": chunk_no,
                "file_id": file_id,
                "participant_id": participant_id,
                "user_id": user_id,
                "name": original_filename,
                "clean_name": clean_filename,
                "path": blob_path,
                "size": file_size,
                "type": file_type,
                "text_chunk": chunk,
                "embeddings": embeddings
            }

            try:
                await cosmos_client.add_participant_doc_chunk(doc_chunk_data)
                stored_chunk_ids.append(chunk_id)
                logger.debug(f"Stored chunk {chunk_no}/{len(chunks)} with id {chunk_id}")
            except Exception as db_e:
                logger.error(f"Failed to store chunk {chunk_id} in Cosmos DB: {db_e}", exc_info=True)
                try:
                    await blob_db.delete_file(user_id, participant_id, blob_path)
                except Exception as cleanup_e:
                    logger.error(f"Failed to clean up blob file '{blob_path}' after DB store error: {cleanup_e}")
                raise HTTPException(status_code=500, detail=f"Failed to store document chunk {chunk_no} in database.")

        logger.info(f"Successfully processed and stored {len(stored_chunk_ids)} chunks for document '{original_filename}' (file_id: {file_id})")

        return {
            **doc_info,
            "chunk_count": len(chunks),
            "stored_chunk_ids": stored_chunk_ids
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document for participant {participant_id}: {str(e)}", exc_info=True)
        if 'blob_path' in locals() and blob_path:
             try:
                 await blob_db.delete_file(user_id, participant_id, blob_path)
                 logger.info(f"Cleaned up blob file '{blob_path}' due to overall upload error.")
             except Exception as cleanup_e:
                 logger.error(f"Failed to clean up blob file '{blob_path}' after overall upload error: {cleanup_e}")
        raise HTTPException(status_code=500, detail="Internal server error while uploading and processing document")
    finally:
        await file.close()


async def delete_participant_document(participant_id: str, user_id: str, file_id: str) -> dict:
    """
    Deletes all chunks associated with a specific file_id for a participant
    from the participant_docs container and deletes the corresponding blob file.
    """
    logger.info(f"Deleting document with file_id: {file_id} for participant ID: {participant_id}, user ID: {user_id}")

    participant = await cosmos_client.get_participant(user_id, participant_id)
    if not participant:
        logger.error(f"Participant not found with ID: {participant_id}")
        raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")

    try:
        doc_container = cosmos_client.get_participant_docs_container()
        query = "SELECT c.id, c.path FROM c WHERE c.participant_id = @participant_id AND c.file_id = @file_id"
        parameters = [
            {"name": "@participant_id", "value": participant_id},
            {"name": "@file_id", "value": file_id}
        ]

        chunks_to_delete = list(doc_container.query_items(
            query=query,
            parameters=parameters,
            partition_key=participant_id
        ))

        if not chunks_to_delete:
            logger.error(f"Document with file_id '{file_id}' not found for participant {participant_id}")
            raise HTTPException(status_code=404, detail=f"Document with file_id '{file_id}' not found for this participant.")

        blob_path_to_delete = chunks_to_delete[0].get("path")
        if blob_path_to_delete:
            try:
                await blob_db.delete_file(user_id, participant_id, blob_path_to_delete)
                logger.info(f"Deleted blob file: {blob_path_to_delete}")
            except Exception as e:
                logger.warning(f"Failed to delete blob file {blob_path_to_delete} for file_id {file_id}: {str(e)}")
        else:
            logger.warning(f"No blob path found in chunks for file_id {file_id}, cannot delete from blob storage.")


        deleted_chunk_count = 0
        for chunk in chunks_to_delete:
            chunk_id = chunk.get("id")
            if chunk_id:
                try:
                    doc_container.delete_item(item=chunk_id, partition_key=participant_id)
                    deleted_chunk_count += 1
                    logger.debug(f"Deleted chunk {chunk_id} for file_id {file_id}")
                except Exception as e:
                    logger.error(f"Failed to delete chunk {chunk_id} for file_id {file_id}: {str(e)}", exc_info=True)

        logger.info(f"Attempted deletion of {len(chunks_to_delete)} chunks for file_id {file_id}. Successfully deleted: {deleted_chunk_count}")

        if deleted_chunk_count != len(chunks_to_delete):
             logger.error(f"Partial deletion: Only {deleted_chunk_count}/{len(chunks_to_delete)} chunks deleted for file_id {file_id}.")
        return {"deleted_file_id": file_id, "deleted_chunk_count": deleted_chunk_count}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document file_id {file_id} for participant {participant_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while deleting document")
