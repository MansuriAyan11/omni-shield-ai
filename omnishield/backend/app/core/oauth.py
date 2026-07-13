"""
OAuth2 Integration for Google, GitHub, Microsoft
Uses authlib for OAuth2 client implementation
"""

from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from loguru import logger

from app.core.config import settings

# Initialize OAuth registry
oauth = OAuth()

# Configure OAuth providers if credentials are available
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    logger.info("Google OAuth2 provider registered")

if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
    oauth.register(
        name='github',
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        access_token_url='https://github.com/login/oauth/access_token',
        access_token_params=None,
        authorize_url='https://github.com/login/oauth/authorize',
        authorize_params=None,
        api_base_url='https://api.github.com/',
        client_kwargs={'scope': 'user:email'},
    )
    logger.info("GitHub OAuth2 provider registered")


async def get_oauth_user_info(provider: str, token: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Fetch user information from OAuth provider
    
    Args:
        provider: Provider name ('google', 'github')
        token: OAuth token dict
    
    Returns:
        User info dict with email, name, picture
    """
    try:
        if provider == 'google':
            # Google returns user info directly in the ID token
            if 'userinfo' in token:
                userinfo = token['userinfo']
                return {
                    'email': userinfo.get('email'),
                    'name': userinfo.get('name'),
                    'picture': userinfo.get('picture'),
                    'email_verified': userinfo.get('email_verified', False)
                }
        
        elif provider == 'github':
            # GitHub requires API call for user info
            # This would be done in the OAuth callback handler
            pass
        
        return None
    except Exception as e:
        logger.error(f"Failed to get OAuth user info from {provider}: {e}")
        return None


def is_oauth_configured(provider: str) -> bool:
    """Check if OAuth provider is configured"""
    if provider == 'google':
        return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    elif provider == 'github':
        return bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET)
    return False
