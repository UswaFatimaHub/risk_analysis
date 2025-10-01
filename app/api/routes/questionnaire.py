from fastapi import APIRouter, HTTPException, status
from app.models.schemas import QuestionnaireRequest, QuestionnaireResponse, QuestionnaireStatus
from app.services.risk_service import RiskAssessmentService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
risk_service = RiskAssessmentService()

@router.post("/questionnaire/submit", response_model=QuestionnaireResponse)
async def submit_questionnaire(request: QuestionnaireRequest):
    """
    Submit a CSA questionnaire for risk assessment processing.
    
    Returns:
    - questionnaire_id: Unique identifier for tracking
    - status: Current processing status (submitted, in_progress, completed, failed)
    - message: Status description
    - submitted_at: Timestamp of submission
    """
    try:
        # Process the questionnaire submission
        processed_questionnaire = await risk_service.submit_questionnaire(request)
        
        return QuestionnaireResponse(
            questionnaire_id=processed_questionnaire.questionnaire_id,
            status=processed_questionnaire.status,
            message=f"Questionnaire submitted successfully. Processing started.",
            submitted_at=processed_questionnaire.created_at
        )
        
    except Exception as e:
        logger.error(f"Error submitting questionnaire: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit questionnaire: {str(e)}"
        )

@router.get("/questionnaire/{questionnaire_id}/status")
async def get_questionnaire_status(questionnaire_id: str):
    """
    Get the current processing status of a questionnaire.
    
    Returns:
    - questionnaire_id: The questionnaire identifier
    - status: Current processing status
    - created_at: When the questionnaire was submitted
    - processed_at: When processing completed (if applicable)
    """
    try:
        processed_questionnaire = await risk_service.get_report(questionnaire_id)
        
        if not processed_questionnaire:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Questionnaire with ID {questionnaire_id} not found"
            )
        
        return {
            "questionnaire_id": processed_questionnaire.questionnaire_id,
            "status": processed_questionnaire.status,
            "created_at": processed_questionnaire.created_at,
            "processed_at": processed_questionnaire.processed_at,
            "error_message": processed_questionnaire.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting questionnaire status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get questionnaire status: {str(e)}"
        )
