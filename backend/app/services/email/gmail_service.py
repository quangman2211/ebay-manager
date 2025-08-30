"""
Gmail API service for email retrieval and authentication
Following SOLID principles - Single Responsibility for Gmail API interactions
YAGNI compliance: Basic email reading and OAuth2 authentication only
"""

from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import email
from datetime import datetime, timedelta
import os
import pickle

from app.core.config import settings
from app.core.exceptions import ExternalServiceError, AuthenticationError


class GmailCredentialsManager:
    """
    SOLID: Single Responsibility - Handle Gmail authentication only
    YAGNI: Simple OAuth flow, no complex credential management
    """
    
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        self.credentials_path = settings.GMAIL_CREDENTIALS_PATH
        self.token_path = settings.GMAIL_TOKEN_PATH
    
    def get_credentials(self, user_id: int) -> Optional[Credentials]:
        """Get Gmail credentials for user"""
        token_file = f"{self.token_path}/gmail_token_{user_id}.pickle"
        
        creds = None
        # Load existing token
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, initiate OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    # Refresh failed, need new authorization
                    return None
            else:
                return None
        
        # Save refreshed credentials
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
        
        return creds
    
    def initiate_oauth_flow(self, user_id: int) -> str:
        """Initiate OAuth flow and return authorization URL"""
        if not os.path.exists(self.credentials_path):
            raise AuthenticationError("Gmail credentials file not found")
        
        flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_path, self.SCOPES
        )
        
        # Generate authorization URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=str(user_id)  # Include user_id in state
        )
        
        return auth_url
    
    def complete_oauth_flow(self, user_id: int, authorization_code: str) -> bool:
        """Complete OAuth flow with authorization code"""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, self.SCOPES
            )
            
            flow.fetch_token(code=authorization_code)
            
            # Save credentials
            token_file = f"{self.token_path}/gmail_token_{user_id}.pickle"
            os.makedirs(os.path.dirname(token_file), exist_ok=True)
            
            with open(token_file, 'wb') as token:
                pickle.dump(flow.credentials, token)
            
            return True
            
        except Exception as e:
            raise AuthenticationError(f"OAuth flow failed: {str(e)}")


class GmailService:
    """
    SOLID: Single Responsibility - Gmail API interactions only
    YAGNI: Basic email reading, no complex operations
    """
    
    def __init__(self, credentials_manager: GmailCredentialsManager):
        self.credentials_manager = credentials_manager
        self.service = None
        self.current_user_id = None
    
    def authenticate(self, user_id: int) -> bool:
        """Authenticate with Gmail for specific user"""
        try:
            creds = self.credentials_manager.get_credentials(user_id)
            if not creds:
                return False
            
            self.service = build('gmail', 'v1', credentials=creds)
            self.current_user_id = user_id
            return True
            
        except Exception as e:
            raise AuthenticationError(f"Gmail authentication failed: {str(e)}")
    
    def list_messages(
        self, 
        query: str = "", 
        max_results: int = 100,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List Gmail messages with query
        YAGNI: Basic message listing, no complex filtering
        """
        if not self.service:
            raise AuthenticationError("Not authenticated with Gmail")
        
        try:
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results,
                pageToken=page_token
            ).execute()
            
            return {
                'messages': result.get('messages', []),
                'next_page_token': result.get('nextPageToken'),
                'result_size_estimate': result.get('resultSizeEstimate', 0)
            }
            
        except HttpError as e:
            raise ExternalServiceError(f"Gmail API error: {str(e)}")
    
    def get_message(self, message_id: str, format_type: str = 'full') -> Dict[str, Any]:
        """Get full message details"""
        if not self.service:
            raise AuthenticationError("Not authenticated with Gmail")
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format=format_type
            ).execute()
            
            return message
            
        except HttpError as e:
            raise ExternalServiceError(f"Failed to get message {message_id}: {str(e)}")
    
    def get_messages_batch(self, message_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple messages in batch"""
        if not self.service:
            raise AuthenticationError("Not authenticated with Gmail")
        
        messages = []
        
        # Process in batches of 100 (Gmail API limit)
        for i in range(0, len(message_ids), 100):
            batch_ids = message_ids[i:i + 100]
            
            try:
                batch = self.service.new_batch_http_request()
                
                def callback(request_id, response, exception):
                    if exception:
                        print(f"Error getting message {request_id}: {exception}")
                    else:
                        messages.append(response)
                
                for msg_id in batch_ids:
                    batch.add(
                        self.service.users().messages().get(userId='me', id=msg_id),
                        callback=callback
                    )
                
                batch.execute()
                
            except HttpError as e:
                raise ExternalServiceError(f"Batch message retrieval failed: {str(e)}")
        
        return messages
    
    def search_messages(
        self,
        from_email: Optional[str] = None,
        to_email: Optional[str] = None,
        subject_contains: Optional[str] = None,
        after_date: Optional[datetime] = None,
        before_date: Optional[datetime] = None,
        has_attachment: Optional[bool] = None,
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        Search messages with common filters
        YAGNI: Basic search parameters, no complex query building
        """
        query_parts = []
        
        if from_email:
            query_parts.append(f"from:{from_email}")
        
        if to_email:
            query_parts.append(f"to:{to_email}")
        
        if subject_contains:
            query_parts.append(f"subject:{subject_contains}")
        
        if after_date:
            date_str = after_date.strftime("%Y/%m/%d")
            query_parts.append(f"after:{date_str}")
        
        if before_date:
            date_str = before_date.strftime("%Y/%m/%d")
            query_parts.append(f"before:{date_str}")
        
        if has_attachment:
            query_parts.append("has:attachment")
        
        query = " ".join(query_parts)
        
        return self.list_messages(query, max_results)
    
    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        """Get email thread with all messages"""
        if not self.service:
            raise AuthenticationError("Not authenticated with Gmail")
        
        try:
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id,
                format='full'
            ).execute()
            
            return thread
            
        except HttpError as e:
            raise ExternalServiceError(f"Failed to get thread {thread_id}: {str(e)}")