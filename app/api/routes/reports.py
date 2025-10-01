from fastapi import APIRouter, HTTPException, status
from app.models.schemas import (
    ReportResponse, QuestionnaireStatus, AuditReportRegenerateRequest, 
    AuditReportResponse
)
from app.services.risk_service import RiskAssessmentService
from app.services.report_service import ReportService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
risk_service = RiskAssessmentService()
report_service = ReportService()

@router.get("/reports/{questionnaire_id}", response_model=ReportResponse)
async def get_complete_report(questionnaire_id: str):
    """
    Get the complete report for a questionnaire (risk register + audit report).
    
    Parameters:
    - questionnaire_id: The unique identifier of the questionnaire
    
    Returns:
    - Complete risk register with all processed risks
    - Auto-generated audit report (if available)
    - Processing status and timestamps
    - Error information if processing failed
    
    Note: Audit reports are automatically generated after risk register completion.
    """
    try:
        processed_questionnaire = await risk_service.get_report(questionnaire_id)
        
        if not processed_questionnaire:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Questionnaire with ID {questionnaire_id} not found"
            )
        
        # Check if processing is still in progress
        if processed_questionnaire.status == QuestionnaireStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Questionnaire is still being processed. Please check back later."
            )
        
        if processed_questionnaire.status == QuestionnaireStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Risk assessment is currently in progress. Please check back later."
            )
            
        if processed_questionnaire.status == QuestionnaireStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Risk assessment processing failed: {processed_questionnaire.error_message}"
            )
        
        return ReportResponse(
            questionnaire_id=processed_questionnaire.questionnaire_id,
            status=processed_questionnaire.status,
            risk_register=processed_questionnaire.risk_register,
            audit_report=processed_questionnaire.audit_report,
            created_at=processed_questionnaire.created_at,
            processed_at=processed_questionnaire.processed_at,
            error_message=processed_questionnaire.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk register report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get risk register report: {str(e)}"
        )

@router.get("/reports/{questionnaire_id}/export")
async def export_risk_register(questionnaire_id: str, format: str = "json"):
    """
    Export risk register in different formats.
    
    Parameters:
    - questionnaire_id: The unique identifier of the questionnaire  
    - format: Export format (json, csv) - default is json
    
    Returns:
    - Risk register data in requested format
    """
    try:
        processed_questionnaire = await risk_service.get_report(questionnaire_id)
        
        if not processed_questionnaire:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Questionnaire with ID {questionnaire_id} not found"
            )
            
        if processed_questionnaire.status != QuestionnaireStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Risk register is not ready for export. Processing may still be in progress or failed."
            )
        
        if format.lower() == "json":
            return {
                "questionnaire_id": questionnaire_id,
                "export_format": "json",
                "data": processed_questionnaire.risk_register.model_dump() if processed_questionnaire.risk_register else None
            }
        elif format.lower() == "csv":
            # For CSV export, we would typically return the data in a format suitable for CSV conversion
            # This is a simplified version - in production you might want to use pandas or similar
            if not processed_questionnaire.risk_register:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="No risk data available for export"
                )
            
            return {
                "questionnaire_id": questionnaire_id,
                "export_format": "csv",
                "data": [risk.model_dump() for risk in processed_questionnaire.risk_register.risks]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format. Supported formats: json, csv"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting risk register: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export risk register: {str(e)}"
        )

# @router.post("/reports/{questionnaire_id}/audit-report", response_model=AuditReportResponse)
# async def regenerate_audit_report(questionnaire_id: str, request: AuditReportRegenerateRequest, force_regenerate: bool = True):
#     """
#     Regenerate an audit report with optional company/department override.
    
#     Parameters:
#     - questionnaire_id: The unique identifier of the questionnaire
#     - request: Optional company_name and department_name overrides
#     - force_regenerate: Always true for this endpoint (regenerate existing reports)
    
#     Returns:
#     - Complete audit report with executive summary, risk overview, and recommendations
    
#     Note: Audit reports are automatically generated when questionnaires are processed.
#     Use this endpoint only to regenerate reports with different company/department info.
#     """
#     try:
#         # Check if risk register exists and is completed
#         processed_questionnaire = await risk_service.get_report(questionnaire_id)
        
#         if not processed_questionnaire:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Questionnaire with ID {questionnaire_id} not found"
#             )
        
#         if processed_questionnaire.status != QuestionnaireStatus.COMPLETED:
#             raise HTTPException(
#                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#                 detail=f"Risk register must be completed before regenerating audit report. Current status: {processed_questionnaire.status}"
#             )
        
#         if not processed_questionnaire.risk_register:
#             raise HTTPException(
#                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#                 detail="No risk register available for report generation"
#             )
        
#         # Use stored values or overrides from request
#         company_name = request.company_name or processed_questionnaire.company_name or "Unknown Company"
#         department_name = request.department_name or processed_questionnaire.department
        
#         # Generate the audit report (force regenerate)
#         report_sections = await report_service.generate_audit_report(
#             questionnaire_id=questionnaire_id,
#             company_name=company_name,
#             department_name=department_name,
#             force_regenerate=force_regenerate
#         )
        
#         if not report_sections:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Failed to generate audit report"
#             )
        
#         return AuditReportResponse(
#             questionnaire_id=questionnaire_id,
#             status="completed",
#             report=report_sections,
#             company_name=company_name,
#             department_name=department_name,
#             generated_at=datetime.now(),
#             message="Audit report regenerated successfully"
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error generating audit report: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to generate audit report: {str(e)}"
#         )

@router.get("/reports/{questionnaire_id}/audit-report", response_model=AuditReportResponse)
async def get_audit_report(questionnaire_id: str):
    """
    Retrieve an existing audit report.
    
    Parameters:
    - questionnaire_id: The unique identifier of the questionnaire
    
    Returns:
    - Previously generated audit report or 404 if not found
    """
    try:
        # Get the complete questionnaire with audit report
        processed_questionnaire = await report_service.get_processed_questionnaire_with_report(
            questionnaire_id
        )
        
        if not processed_questionnaire:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Questionnaire with ID {questionnaire_id} not found"
            )
        
        if not processed_questionnaire.audit_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No audit report found for questionnaire {questionnaire_id}. Generate one first using POST endpoint."
            )
        
        audit_report = processed_questionnaire.audit_report
        
        return AuditReportResponse(
            questionnaire_id=questionnaire_id,
            status="completed",
            report=audit_report.report_sections,
            company_name=audit_report.company_name,
            department_name=audit_report.department_name,
            generated_at=audit_report.generated_at,
            message="Audit report retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit report: {str(e)}"
        )