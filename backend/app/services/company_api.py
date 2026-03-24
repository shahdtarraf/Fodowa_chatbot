"""
Company Backend API Integration.

Provides integration with external company backend APIs for:
- User data retrieval
- Order history lookup
- Business data queries
"""

import os
from typing import Optional, Dict, Any
import requests

from app.utils.logger import logger

# Environment variables for API configuration
COMPANY_API_URL = os.getenv("COMPANY_API_URL", "")
COMPANY_API_KEY = os.getenv("COMPANY_API_KEY", "")


def _get_headers() -> Dict[str, str]:
    """Build headers for API requests."""
    headers = {
        "Content-Type": "application/json",
    }
    if COMPANY_API_KEY:
        headers["Authorization"] = f"Bearer {COMPANY_API_KEY}"
    return headers


def is_api_configured() -> bool:
    """Check if company API is configured."""
    return bool(COMPANY_API_URL and COMPANY_API_KEY)


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve user data from company backend.
    
    Args:
        user_id: The user identifier
        
    Returns:
        User data dictionary, or None if not found or API not configured
    """
    if not is_api_configured():
        logger.warning("Company API not configured. Set COMPANY_API_URL and COMPANY_API_KEY.")
        return None
    
    try:
        url = f"{COMPANY_API_URL}/users/{user_id}"
        logger.info("Calling Company API: GET %s", url)
        
        response = requests.get(url, headers=_get_headers(), timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ User data retrieved for user_id=%s", user_id)
            return data
        elif response.status_code == 404:
            logger.warning("User not found: user_id=%s", user_id)
            return None
        else:
            logger.error("API error: status=%d, response=%s", response.status_code, response.text)
            return None
            
    except requests.exceptions.Timeout:
        logger.error("Company API timeout for user_id=%s", user_id)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("Company API request failed: %s", e)
        return None


def get_orders(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve order history from company backend.
    
    Args:
        user_id: The user identifier
        
    Returns:
        Orders data dictionary, or None if not found or API not configured
    """
    if not is_api_configured():
        logger.warning("Company API not configured. Set COMPANY_API_URL and COMPANY_API_KEY.")
        return None
    
    try:
        url = f"{COMPANY_API_URL}/users/{user_id}/orders"
        logger.info("Calling Company API: GET %s", url)
        
        response = requests.get(url, headers=_get_headers(), timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ Orders retrieved for user_id=%s", user_id)
            return data
        elif response.status_code == 404:
            logger.warning("Orders not found for user_id=%s", user_id)
            return None
        else:
            logger.error("API error: status=%d, response=%s", response.status_code, response.text)
            return None
            
    except requests.exceptions.Timeout:
        logger.error("Company API timeout for user_id=%s", user_id)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("Company API request failed: %s", e)
        return None


def get_mock_user(user_id: str) -> Dict[str, Any]:
    """
    Return mock user data for testing/demo purposes.
    
    Used when COMPANY_API_URL is not configured.
    """
    return {
        "user_id": user_id,
        "name": "Demo User",
        "email": "demo@example.com",
        "account_status": "active",
        "created_at": "2024-01-01",
    }


def get_mock_orders(user_id: str) -> Dict[str, Any]:
    """
    Return mock order data for testing/demo purposes.
    
    Used when COMPANY_API_URL is not configured.
    """
    return {
        "user_id": user_id,
        "orders": [
            {
                "order_id": "ORD-001",
                "product": "Product A",
                "quantity": 2,
                "price": 99.99,
                "status": "delivered",
                "date": "2024-03-15",
            },
            {
                "order_id": "ORD-002",
                "product": "Product B",
                "quantity": 1,
                "price": 149.99,
                "status": "shipped",
                "date": "2024-03-20",
            },
        ],
        "total_orders": 2,
    }
