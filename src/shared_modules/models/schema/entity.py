from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LocationMap(BaseModel):
    address: Optional[str] = Field(
        None,
        description='Physical location address - used to assess geographical proximity and local market understanding',
    )
    latlng: Optional[Dict[str, float]] = Field(
        None,
        description='Geographical coordinates for precise location matching and distance calculations',
    )


class ContactMap(BaseModel):
    platform: Optional[str] = Field(
        None,
        description='Communication platform type - helps understand preferred communication channels',
    )
    value: Optional[str] = Field(
        None, description='Contact details - enables direct communication between matched parties'
    )


class InvestmentCriteriaMap(BaseModel):
    criteriaName: Optional[str] = Field(
        None,
        description='Specific investment requirement - key factor in determining startup-enabler compatibility',
    )
    details: Optional[str] = Field(
        None,
        description='Detailed explanation of investment criteria - provides context for better matching accuracy',
    )


class PortfolioItemMap(BaseModel):
    supportedStartupProject: Optional[str] = Field(
        None,
        description="Previously supported startup - indicates enabler's experience and success patterns",
    )
    dateSupported: Optional[str] = Field(
        None, description="Support timeline - shows enabler's historical engagement patterns"
    )
    isSupportingToPresent: Optional[bool] = Field(
        None, description='Current support status - indicates long-term commitment capability'
    )
    roleAndImpact: Optional[str] = Field(
        None, description="Contribution details - demonstrates enabler's value addition capacity"
    )


class MilestoneMap(BaseModel):
    title: Optional[str] = Field(
        None, description="Achievement title - indicates startup's progress and growth trajectory"
    )
    dateAchieved: Optional[str] = Field(
        None, description="Achievement date - shows startup's development pace"
    )
    description: Optional[str] = Field(
        None,
        description="Milestone details - provides context about startup's achievements and capabilities",
    )


class FounderMap(BaseModel):
    founderId: Optional[str] = Field(
        None,
        description="Unique founder identifier - for tracking founder's history and connections",
    )
    name: Optional[str] = Field(
        None, description="Founder's name - for personal identification and networking"
    )
    role: Optional[str] = Field(
        None, description='Position in startup - indicates leadership structure and expertise areas'
    )
    dateJoined: Optional[str] = Field(
        None, description="Start date - shows founder's commitment and experience length"
    )
    overview: Optional[str] = Field(
        None,
        description="Founder's background - helps assess expertise fit with enabler's requirements",
    )
    photoObjectkey: Optional[str] = Field(
        None, description='Profile photo reference - for visual identification'
    )
    contacts: Optional[List[ContactMap]] = Field(
        None, description="Founder's contact information - enables direct communication"
    )


class EntitySchema(BaseModel):
    model_config = ConfigDict(extra='ignore')

    # Common attributes
    description: Optional[str] = Field(
        None, description='Entity overview - crucial for initial matching assessment'
    )
    location: Optional[LocationMap] = Field(
        None, description='Geographic information - important for local ecosystem matching'
    )
    dateFounded: Optional[str] = Field(
        None, description='Establishment date - indicates maturity and experience level'
    )
    email: Optional[str] = Field(
        None, description='Email address - for communication and verification purposes'
    )
    logoObjectKey: Optional[str] = Field(None, description='Logo object key - for the entity logo')

    # ENABLER attributes
    enablerId: Optional[str] = Field(
        None, description='Unique enabler identifier - for tracking and matching purposes'
    )
    enablerName: Optional[str] = Field(
        None, description='Organization name - for identification and branding'
    )
    organizationType: Optional[List[str]] = Field(
        None, description='Enabler category - crucial for matching appropriate support type'
    )
    industryFocus: Optional[List[str]] = Field(
        None, description='Target sectors - primary factor in matching with relevant startups'
    )
    supportType: Optional[List[str]] = Field(
        None, description="Available support services - key in matching startups' needs"
    )
    fundingStageFocus: Optional[List[str]] = Field(
        None, description='Investment stage preference - critical for funding alignment'
    )
    investmentAmount: Optional[float] = Field(
        None, description='Funding capacity - important for financial matching'
    )
    startupStagePreference: Optional[List[str]] = Field(
        None,
        description='Preferred startup maturity - ensures appropriate development stage matching',
    )
    preferredBusinessModels: Optional[List[str]] = Field(
        None, description='Favored business types - helps match compatible business approaches'
    )
    investmentCriteria: Optional[List[InvestmentCriteriaMap]] = Field(
        None, description='Specific requirements - detailed matching criteria'
    )
    portfolio: Optional[List[PortfolioItemMap]] = Field(
        None, description='Past investments - indicates experience and success patterns'
    )

    # STARTUP attributes
    startupId: Optional[str] = Field(
        None, description='Unique startup identifier - for tracking and matching purposes'
    )
    startUpName: Optional[str] = Field(
        None, description='Company name - for identification and branding'
    )
    industries: Optional[List[str]] = Field(
        None, description='Operating sectors - crucial for industry alignment matching'
    )
    startupStage: Optional[str] = Field(
        None, description='Development phase - key for matching with appropriate enablers'
    )
    revenueModel: Optional[List[str]] = Field(
        None, description='Business model types - important for business approach alignment'
    )
    milestones: Optional[List[MilestoneMap]] = Field(
        None, description='Achievements - demonstrates growth potential and track record'
    )
    founders: Optional[List[FounderMap]] = Field(
        None, description='Founding team - important for assessing leadership capability'
    )

    # Contacts (shared between ENABLER and STARTUP)
    contacts: Optional[List[ContactMap]] = Field(
        None,
        description='Organization contact details - facilitates communication between matched parties',
    )
