import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.models.schemas import (
    ProcessedQuestionnaire, QuestionnaireStatus, RiskRegister, 
    QuestionnaireRequest, RiskLLMInputRegister, Risk
)
from app.services.llm_service import LLMService
from app.database.mongodb import get_database
from app.services.report_service import ReportService

logger = logging.getLogger(__name__)

class RiskAssessmentService:
    """Service for processing risk assessments"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.system_prompt = """You are a risk assessment agent. 
You will be given Control Self-Assessment (CSA) questionnaire and interview answers.

Your task is to generate a complete Risk Register, identifying maximum risks in JSON format following the schema below.

Rules:
1. Populate fields only with detailed information explicitly provided in CSA.
2. If information is missing, use "TBD" or null — never invent data.
3. SOP_Available: If SOPs exist but are outdated, write "Yes (last updated YYYY)".
4. Do not use placeholders or generic text.
5. Controls: Always use CSA-provided Preventive, Detective, Corrective controls. Multiple may apply.
6. Do not add fields not in the schema. Do not invent new risks.
7. Identify and describe every risk separately and in detail — do not merge multiple risks into one.

Return valid JSON that matches the schema exactly.
"""

    async def submit_questionnaire(
        self, 
        request: QuestionnaireRequest
    ) -> ProcessedQuestionnaire:
        """Submit questionnaire and return initial response"""
        
        questionnaire_id = str(uuid.uuid4())
        
        # Create initial document in database
        document = ProcessedQuestionnaire(
            questionnaire_id=questionnaire_id,
            original_data=request.questionnaire_data,
            status=QuestionnaireStatus.SUBMITTED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            company_name=request.company_name,
            department=request.department,
            submitted_by=request.submitted_by
        )
        
        # Save to database
        db = get_database()
        await db.questionnaires.insert_one(document.model_dump())
        
        # Start background processing
        asyncio.create_task(self._process_questionnaire_async(questionnaire_id))
        
        return document

    async def _process_questionnaire_async(self, questionnaire_id: str):
        """Background task to process questionnaire with LLM and auto-generate audit report"""
        db = get_database()
        
        try:
            # Update status to in_progress
            await db.questionnaires.update_one(
                {"questionnaire_id": questionnaire_id},
                {
                    "$set": {
                        "status": QuestionnaireStatus.IN_PROGRESS,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Get questionnaire data
            document = await db.questionnaires.find_one({"questionnaire_id": questionnaire_id})
            if not document:
                raise Exception("Questionnaire not found")
            
            questionnaire_data = document["original_data"]
            company_name = document.get("company_name", "Unknown Company")
            department = document.get("department", "Unknown Department")
            
            # Process with LLM to generate risk register
            logger.info(f"Processing questionnaire {questionnaire_id} with LLM")
            llm_risks = await self.llm_service.parse_response(
                schema=RiskLLMInputRegister,
                system_prompt=self.system_prompt,
                user_prompt=questionnaire_data
            )
            if not llm_risks or not llm_risks.risks:
                raise Exception("Failed to generate risks from LLM")
            
            enriched_risks = []
            for idx, risk in enumerate(llm_risks.risks, start=1):
                # Get the model data and update with generated references
                risk_data = risk.model_dump()
                risk_data.update({
                    "Risk_Event_Reference": f"Risk_{department}_{idx}",
                    "Control_Ref": f"Control_{department}_{idx}",
                    "Action_Plan_Reference": f"Action_{department}_{idx}",
                    "Risk_Data_Sources": ["CSA"],
                })
                enriched = Risk(**risk_data)
                enriched_risks.append(enriched)

            risk_register = RiskRegister(risks=enriched_risks)

            if risk_register:
                # Update with risk register
                await db.questionnaires.update_one(
                    {"questionnaire_id": questionnaire_id},
                    {
                        "$set": {
                            "risk_register": risk_register.model_dump(),
                            "processed_at": datetime.now(timezone.utc),
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                logger.info(f"Successfully processed risk register for questionnaire {questionnaire_id}")
                
                # Auto-generate audit report using stored company and department info

                report_service = ReportService()
                
                logger.info(f"Auto-generating audit report for questionnaire {questionnaire_id}")
                
                audit_report_sections = await report_service.generate_audit_report(
                    questionnaire_id=questionnaire_id,
                    company_name=company_name,
                    department_name=department
                )
                
                if audit_report_sections:
                    logger.info(f"Successfully auto-generated audit report for questionnaire {questionnaire_id}")
                    # Final status update to completed
                    await db.questionnaires.update_one(
                        {"questionnaire_id": questionnaire_id},
                        {
                            "$set": {
                                "status": QuestionnaireStatus.COMPLETED,
                                "updated_at": datetime.now(timezone.utc)
                            }
                        }
                    )
                else:
                    logger.warning(f"Failed to auto-generate audit report for questionnaire {questionnaire_id}, but risk register is available")
                    # Still mark as completed since risk register is ready
                    await db.questionnaires.update_one(
                        {"questionnaire_id": questionnaire_id},
                        {
                            "$set": {
                                "status": QuestionnaireStatus.COMPLETED,
                                "updated_at": datetime.now(timezone.utc)
                            }
                        }
                    )
            else:
                raise Exception("Failed to generate risk register")
                
        except Exception as e:
            logger.error(f"Error processing questionnaire {questionnaire_id}: {e}")
            # Update with error status
            await db.questionnaires.update_one(
                {"questionnaire_id": questionnaire_id},
                {
                    "$set": {
                        "status": QuestionnaireStatus.FAILED,
                        "error_message": str(e),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

    async def get_report(self, questionnaire_id: str) -> Optional[ProcessedQuestionnaire]:
        """Get processed questionnaire report"""
        start_time = datetime.now(timezone.utc)
        logger.info(f"Getting report for questionnaire {questionnaire_id}")
        
        try:
            db = get_database()
            logger.info(f"Database connection obtained in {(datetime.now(timezone.utc) - start_time).total_seconds():.3f}s")
            
            query_start = datetime.now(timezone.utc)
            
            # Add timeout protection to database query
            try:
                # Use projection to only get necessary fields for status checks
                document = await asyncio.wait_for(
                    db.questionnaires.find_one(
                        {"questionnaire_id": questionnaire_id},
                        {"_id": 0}  # Exclude MongoDB's internal _id field
                    ),
                    timeout=2.0  # 2 second timeout for DB queries
                )
            except asyncio.TimeoutError:
                logger.error(f"Database query timeout for {questionnaire_id}")
                raise Exception("Database query timeout")
                
            logger.info(f"Database query completed in {(datetime.now(timezone.utc) - query_start).total_seconds():.3f}s")
            
            if not document:
                logger.warning(f"No document found for questionnaire_id: {questionnaire_id}")
                return None
            
            result = ProcessedQuestionnaire(**document)
            
            total_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(f"Total get_report time: {total_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting report for {questionnaire_id}: {e}")
            raise
