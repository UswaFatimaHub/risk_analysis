from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Annotated
from datetime import datetime
from enum import Enum

class QuestionnaireStatus(str, Enum):
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"  
    COMPLETED = "completed"
    FAILED = "failed"

class QuestionnaireRequest(BaseModel):
    """Request model for questionnaire submission"""
    questionnaire_data: str = Field(..., description="CSA questionnaire data in text format")
    company_name: str = Field(..., description="Company name")
    department: Optional[str] = Field(None, description="Department submitting the questionnaire")
    submitted_by: Optional[str] = Field(None, description="Person submitting the questionnaire")

class QuestionnaireResponse(BaseModel):
    """Response model for questionnaire submission"""
    questionnaire_id: str = Field(..., description="Unique identifier for the questionnaire")
    status: QuestionnaireStatus = Field(..., description="Current processing status")
    message: str = Field(..., description="Status message")
    submitted_at: datetime = Field(..., description="Submission timestamp")

Risk_Data_Source = Annotated[
    List[
        Literal[
            "Audit Points",
            "Customer Complaints",
            "External Audit",
            "Incidents",
            "Internal Audit",
            "Process Notes",
            "Regulatory Inspection",
            "SOP",
            "Fund Policy",
            "Whistle Blowing",
            "CSA",
            "Emerging Risk",
            "Others",
        ]
    ],
    Field(min_length=1, description="Must contain at least one source (e.g., ['CSA'])."),
]

class Risk(BaseModel):
    Function: Literal[
        "Accounting & Billing", "Budgeting", "Procurement", "All"
    ] = Field(..., description="Select the business function this risk belongs to. Must match one of the predefined categories in the risk register.")

    Process_Name: Optional[str] = Field(
        None, description="Name of the high-level process (e.g., Payroll, Supplier Onboarding, Budgeting). Should align with CSA questionnaire sections."
    )
    Sub_Process: Optional[str] = Field(
        None, description="Specific sub-process or activity (e.g., Payroll Compliance, Vendor Compliance)."
    )

    SOP_Available: Literal["Yes", "No"] = Field(
        ..., description="Whether a Standard Operating Procedure (SOP) exists for the process. If outdated, mark as Yes but include update year in Remarks."
    )

    Risk_Event_Reference: str = Field(
        ..., description="Unique identifier for the risk (e.g., Risk_Finance_1). Each risk must have a distinct ID."
    )
    Risk_Description: str = Field(..., description="Concise description of the risk event in plain language.")

    Risk_Causal_Factors: Literal[
        "People", "Process", "System", "External Factor"
    ] = Field(..., description="Primary driver of the risk. Choose one root factor only.")

    Risk_Category: Literal[
        "Reporting", "Strategic", "Compliance", "IT", "Operational", "ALL"
    ] = Field(..., description="Risk category classification, based on the register’s predefined list.")

    Level2: Optional[str] = Field(
        None, description="Custom secondary classification (e.g., 'Payroll Compliance', 'System Failure'). Free text, used only for sub-categorization."
    )

    Root_Cause: Optional[str] = Field(
        None, description="Underlying cause explaining why the risk exists (e.g., Outdated SOP, lack of monitoring)."
    )
    Risk_Impact_Description: Optional[str] = Field(
        None, description="Detailed description of the consequences if the risk materializes."
    )

    Risk_Data_Sources: Risk_Data_Source

    Risk_Likelihood: Optional[
        Literal["Highly Likely", "Expected", "Possible", "Not Likely", "Remote"]
    ] = Field(None, description="Likelihood rating of the risk occurring, based on CSA or interviews.")

    Risk_Impact: Optional[
        Literal["Severe", "Major", "Moderate", "Minor", "Insignificant"]
    ] = Field(None, description="Impact rating if the risk occurs, based on CSA or interviews.")

    Risk_Owner: Optional[str] = Field(
        None, description="Role or title responsible for managing this risk (e.g., CFO, Procurement Manager)."
    )

    Control_Ref: Optional[str] = Field(
        None, description="Unique identifier for the control. Each risk should reference a distinct control ID (e.g., Control_Procurement_1)."
    )
    Control: Optional[str] = Field(
        None, description="Short name or title of the control (e.g., 'Payroll validation rules in ERP')."
    )
    Control_Description: Optional[str] = Field(
        None, description="Detailed description of how the control works and its purpose."
    )

    Control_Frequency: Optional[
        Literal[
            "On Going",
            "Daily",
            "Weekly",
            "Monthly",
            "Quarterly",
            "Half Yearly",
            "Annually",
            "On Demand",
            "NA",
        ]
    ] = Field(None, description="How often the control is executed (e.g., Monthly, Quarterly).")

    Control_Type: Optional[
        Literal["Preventive", "Detective", "Directive", "NA"]
    ] = Field(None, description="Whether the control is Preventive, Detective, or Directive.")

    Control_Category: Optional[
        Literal["Manual", "Automated", "Both", "NA"]
    ] = Field(None, description="Whether the control is manual, automated, or a hybrid (Both).")

    Control_Classification: Optional[
        Literal[
            "Access Control",
            "Reconciliation",
            "Review",
            "Verification and Authorization",
            "IT / System Control",
            "Process Control",
            "Maker Checker",
            "Physical Control",
            "Other",
            "NA",
        ]
    ] = Field(None, description="Classification of control activity, chosen from the register’s list.")

    Control_Design_Effectiveness: Optional[
        Literal["Poor", "Unsatisfactory", "Satisfactory", "Effective", "Highly Effective"]
    ] = Field(None, description="Assessment of how well the control is designed on paper.")

    Control_Operating_Effectiveness: Optional[
        Literal["Poor", "Unsatisfactory", "Satisfactory", "Effective", "Highly Effective"]
    ] = Field(None, description="Assessment of how well the control operates in practice.")

    Residual_Risk: Optional[str] = Field(
        None, description="Remaining risk after considering control effectiveness. If not provided, leave TBD."
    )

    Remarks: Optional[str] = Field(
        None, description="Context-specific notes or issues (avoid generic remarks; tailor per risk)."
    )
    Action_Required: Optional[str] = Field(
        None, description="Specific mitigation required (e.g., 'Update SOPs', 'Automate GOSI filing'). Must be descriptive, not numeric codes."
    )
    Action_Plan_Reference: Optional[str] = Field(
        None, description="Identifier for the related action plan (e.g., Action_Procurement_1)."
    )
    Action_Plan_Item: Optional[str] = Field(
        None, description="Concrete activity planned to address the risk (e.g., 'Upgrade ERP system')."
    )
    Target_Date: Optional[str] = Field(
        None, description="Planned completion date for the action (e.g., 'Q4 2025')."
    )

class RiskRegister(BaseModel):
    risks: List[Risk] = Field(
        ..., description="List of all risks captured from CSA questionnaire."
    )



class AuditReportSections(BaseModel):
    """Audit report sections based on report.py structure"""
    executive_summary: str = Field(
        ...,
        description=(
            "A detailed, high-level overview of the audit. Summarize the department audited, "
            "the company name, the main objectives of the audit, and the most critical findings. "
            "Provide overall risk posture in plain language (e.g., high, medium, low). "
            "This should help leadership quickly grasp the key risks and overall situation."
        ),
    )
    risk_overview: str = Field(
        ...,
        description=(
            "Bullet-point style summary of the identified risks. Include details such as: "
            "- number of risks identified, "
            "- how many are critical/high/medium/low, "
            "- their categories (e.g., compliance, operational, financial), and "
            "- any significant root causes. "
            "This should act as a quick scan of risk exposure."
        ),
    )
    recommendations: List[str] = Field(
        ...,
        description=(
            "A prioritized list of actionable recommendations tailored to the company and department. "
            "Each item should clearly address the risks and weaknesses identified in the audit. "
            "Recommendations should be practical, implementable, and focused on improving internal controls, "
            "compliance, and process efficiency."
        ),
    )

class AuditReport(BaseModel):
    """Complete audit report with metadata"""
    questionnaire_id: str
    company_name: Optional[str] = None
    department_name: Optional[str] = None
    report_sections: Optional[AuditReportSections] = None
    generated_at: Optional[datetime] = None
    status: QuestionnaireStatus

class ProcessedQuestionnaire(BaseModel):
    """Complete processed questionnaire document"""
    questionnaire_id: str
    original_data: str
    risk_register: Optional[RiskRegister] = None
    audit_report: Optional[AuditReport] = None
    status: QuestionnaireStatus
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    company_name: Optional[str] = None
    department: Optional[str] = None
    submitted_by: Optional[str] = None

class ReportResponse(BaseModel):
    """Response model for report generation"""
    questionnaire_id: str
    status: QuestionnaireStatus
    risk_register: Optional[RiskRegister] = None
    audit_report: Optional[AuditReport] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class AuditReportRegenerateRequest(BaseModel):
    """Request model for regenerating audit report with different company/department info"""
    company_name: Optional[str] = Field(None, description="Override company name (optional)")
    department_name: Optional[str] = Field(None, description="Override department name (optional)")

class AuditReportResponse(BaseModel):
    """Response model for audit report generation"""
    questionnaire_id: str
    status: str
    report: Optional[AuditReportSections] = None
    company_name: Optional[str] = None
    department_name: Optional[str] = None
    generated_at: Optional[datetime] = None
    message: str
