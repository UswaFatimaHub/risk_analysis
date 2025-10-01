import logging
from datetime import datetime, timezone
from typing import Optional

from app.models.schemas import (
    AuditReportSections, AuditReport, ProcessedQuestionnaire, 
    QuestionnaireStatus, RiskRegister
)
from app.services.llm_service import LLMService
from app.database.mongodb import get_database

logger = logging.getLogger(__name__)

class ReportService:
    """Service for generating audit reports from risk registers"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.system_prompt = """You are a risk assessment and internal audit reporting agent.
You will be given a Risk Register and audit context.

Your job is to generate a structured Internal Audit Report in JSON format following the given schema.

Guidelines:
1. Strictly follow the schema fields (executive_summary, risk_overview, recommendations).
2. Do not invent or add fields outside the schema.
3. Incorporate the company name and department name in the Executive Summary.
4. Risk Overview should provide a clear, structured summary of identified risks, with focus on criticality and categories.
5. Recommendations should be specific, practical, and clearly address the risks noted.

Return only valid JSON that matches the schema exactly.
"""

    async def generate_audit_report(self, questionnaire_id: str, company_name: str, department_name: Optional[str] = None, force_regenerate: bool = False) -> Optional[AuditReportSections]:
        """Generate audit report from existing risk register"""
        
        try:
            # Get the processed questionnaire with risk register
            db = get_database()
            document = await db.questionnaires.find_one(
                {"questionnaire_id": questionnaire_id}
            )
            
            if not document:
                logger.error(f"Questionnaire {questionnaire_id} not found")
                return None
            
            processed_questionnaire = ProcessedQuestionnaire(**document)
            
            # Check if audit report already exists and we don't want to force regenerate
            if (processed_questionnaire.audit_report and 
                processed_questionnaire.audit_report.report_sections and 
                not force_regenerate):
                logger.info(f"Audit report already exists for questionnaire {questionnaire_id}")
                return processed_questionnaire.audit_report.report_sections
            
            # Check if risk register is available
            if not processed_questionnaire.risk_register:
                logger.error(f"Risk register not available for questionnaire {questionnaire_id}")
                return None
            
            # Use stored company and department info from the questionnaire
            stored_company = processed_questionnaire.company_name or company_name
            stored_department = processed_questionnaire.department or department_name
            
            # Prepare the prompt for report generation
            risk_data = {
                "risks": [risk.model_dump() for risk in processed_questionnaire.risk_register.risks]
            }
            
            user_prompt = f"""Company: {stored_company}
Department: {stored_department or 'Not specified'}
Risk Register: {risk_data}"""
            
            # Generate report using LLM
            logger.info(f"Generating audit report for questionnaire {questionnaire_id}")
            report_sections = await self.llm_service.parse_response(
                schema=AuditReportSections,
                system_prompt=self.system_prompt,
                user_prompt=user_prompt
            )
            
            if report_sections:
                # Store the report in database using consistent data
                await self._store_audit_report(
                    questionnaire_id, 
                    stored_company, 
                    stored_department, 
                    report_sections
                )
                logger.info(f"Successfully generated audit report for questionnaire {questionnaire_id}")
                return report_sections
            else:
                logger.error(f"Failed to generate audit report for questionnaire {questionnaire_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating audit report for {questionnaire_id}: {e}")
            return None

    async def _store_audit_report( self, questionnaire_id: str, company_name: str, department_name: Optional[str], report_sections: AuditReportSections):
        """Store generated audit report in database"""
        
        try:
            db = get_database()
            
            audit_report = AuditReport(
                questionnaire_id=questionnaire_id,
                company_name=company_name,
                department_name=department_name,
                report_sections=report_sections,
                generated_at=datetime.now(timezone.utc),
                status=QuestionnaireStatus.COMPLETED
            )
            
            # Update the questionnaire document with the audit report
            await db.questionnaires.update_one(
                {"questionnaire_id": questionnaire_id},
                {
                    "$set": {
                        "audit_report": audit_report.model_dump(),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            logger.info(f"Audit report stored for questionnaire {questionnaire_id}")
            
        except Exception as e:
            logger.error(f"Error storing audit report for {questionnaire_id}: {e}")
            raise

    async def get_audit_report(self, questionnaire_id: str) -> Optional[AuditReport]:
        """Retrieve existing audit report"""
        
        try:
            db = get_database()
            document = await db.questionnaires.find_one(
                {"questionnaire_id": questionnaire_id}
            )
            
            if not document:
                logger.warning(f"Questionnaire {questionnaire_id} not found")
                return None
            
            processed_questionnaire = ProcessedQuestionnaire(**document)
            
            if processed_questionnaire.audit_report:
                return processed_questionnaire.audit_report
            else:
                logger.info(f"No audit report found for questionnaire {questionnaire_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving audit report for {questionnaire_id}: {e}")
            return None

    async def get_processed_questionnaire_with_report(self, questionnaire_id: str) -> Optional[ProcessedQuestionnaire]:
        """Get complete processed questionnaire including audit report"""
        
        try:
            db = get_database()
            document = await db.questionnaires.find_one(
                {"questionnaire_id": questionnaire_id},
                {"_id": 0}
            )
            
            if not document:
                logger.warning(f"Questionnaire {questionnaire_id} not found")
                return None
            
            return ProcessedQuestionnaire(**document)
            
        except Exception as e:
            logger.error(f"Error retrieving questionnaire with report for {questionnaire_id}: {e}")
            return None
