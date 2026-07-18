import uuid
from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_company, get_current_active_user, get_service, get_db
from app.models.models import User, Company
from app.schemas.responses import APIResponse
from app.schemas.portfolio import PortfolioResponse, PortfolioSummary
from app.services.services import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("", response_model=APIResponse[PortfolioResponse])
def get_portfolio_summary(
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_active_user),
    portfolio_service: PortfolioService = Depends(get_service(PortfolioService))
) -> APIResponse[PortfolioResponse]:
    """
    Retrieves the complete dynamic portfolio view for the caller's company.
    Includes Company profile, Portfolio Summary (totals), and list of owned credit batches.
    Accessible to authenticated Company Admin, Trader, Auditor, and Viewer roles.
    """
    portfolio_data = portfolio_service.get_portfolio(company.id)
    return APIResponse(
        message="Portfolio summary retrieved successfully",
        data=PortfolioResponse.model_validate(portfolio_data)
    )


@router.get("/statistics", response_model=APIResponse[PortfolioSummary])
def get_portfolio_statistics(
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_active_user),
    portfolio_service: PortfolioService = Depends(get_service(PortfolioService))
) -> APIResponse[PortfolioSummary]:
    """
    Retrieves only the aggregated portfolio statistics (total, available, listed, and retired credit counts,
    and estimated portfolio book value) for the caller's company.
    Accessible to all authenticated company users.
    """
    stats = portfolio_service.get_statistics(company.id)
    return APIResponse(
        message="Portfolio statistics generated successfully",
        data=PortfolioSummary.model_validate(stats)
    )


@router.get("/summary", response_model=APIResponse[dict])
def get_portfolio_summary(
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_active_user),
    portfolio_service: PortfolioService = Depends(get_service(PortfolioService))
) -> APIResponse[dict]:
    """
    Retrieves aggregated portfolio summary stats mapped with camelCase keys for the React frontend.
    """
    stats = portfolio_service.get_statistics(company.id)
    data = {
        "portfolioValue": stats["estimated_portfolio_value"],
        "ownedCredits": stats["owned_credit_count"],
        "availableCredits": stats["available_credit_count"],
        "listedCredits": stats["listed_credit_count"],
        "retiredCredits": stats["retired_credit_count"],
    }
    return APIResponse(
        message="Portfolio summary retrieved successfully",
        data=data
    )


@router.get("/batches", response_model=APIResponse[list])
def get_portfolio_batches(
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_active_user),
    portfolio_service: PortfolioService = Depends(get_service(PortfolioService))
) -> APIResponse[list]:
    """
    Retrieves only the list of carbon credit batches currently owned by the caller's company,
    detailing ownership values, available credits, and average purchase prices.
    Accessible to all authenticated company users.
    """
    batches = portfolio_service.get_owned_batches(company.id)
    return APIResponse(
        message="Owned batches list retrieved successfully",
        data=batches
    )
