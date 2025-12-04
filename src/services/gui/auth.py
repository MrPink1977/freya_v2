"""
Authentication and Session Management for GUI Service

Provides JWT token generation/validation and session tracking for WebSocket security.

Author: Claude (AI Assistant)
Version: 0.1.0
Date: 2025-12-04
"""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import jwt
import uuid
import asyncio
from loguru import logger


class TokenManager:
    """
    Manages JWT tokens for WebSocket authentication.
    
    Handles token generation, validation, and refresh logic.
    
    Attributes:
        secret_key: Secret key for JWT signing
        algorithm: JWT algorithm (default: HS256)
        token_expiry: Token expiration time in seconds
    """
    
    def __init__(
        self,
        secret_key: str,
        token_expiry: int = 3600,
        algorithm: str = "HS256"
    ) -> None:
        """
        Initialize TokenManager.
        
        Args:
            secret_key: Secret key for JWT signing
            token_expiry: Token expiration time in seconds (default: 3600 = 1 hour)
            algorithm: JWT algorithm (default: HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expiry = token_expiry
        
        logger.debug(f"[TokenManager] Initialized with expiry: {token_expiry}s")
    
    def generate_token(
        self,
        session_id: str,
        client_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a JWT token for a session.
        
        Args:
            session_id: Unique session identifier
            client_info: Optional client metadata (e.g., IP, user agent)
        
        Returns:
            JWT token string
        """
        try:
            now = datetime.utcnow()
            expiry = now + timedelta(seconds=self.token_expiry)
            
            payload = {
                "session_id": session_id,
                "iat": now,  # Issued at
                "exp": expiry,  # Expiration
                "jti": str(uuid.uuid4()),  # JWT ID (unique token identifier)
            }
            
            # Add optional client info
            if client_info:
                payload["client"] = client_info
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.debug(
                f"[TokenManager] Generated token for session {session_id}, "
                f"expires at {expiry.isoformat()}"
            )
            
            return token
            
        except Exception as e:
            logger.error(f"[TokenManager] Error generating token: {e}")
            raise
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            Token payload if valid, None if invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            logger.debug(
                f"[TokenManager] Token validated for session {payload.get('session_id')}"
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("[TokenManager] Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"[TokenManager] Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"[TokenManager] Error validating token: {e}")
            return None
    
    def refresh_token(self, old_token: str) -> Optional[str]:
        """
        Refresh a JWT token if it's still valid.
        
        Args:
            old_token: Existing JWT token
        
        Returns:
            New token if refresh successful, None otherwise
        """
        try:
            payload = self.validate_token(old_token)
            
            if not payload:
                logger.warning("[TokenManager] Cannot refresh invalid token")
                return None
            
            # Generate new token with same session ID
            session_id = payload.get("session_id")
            client_info = payload.get("client")
            
            new_token = self.generate_token(session_id, client_info)
            
            logger.info(f"[TokenManager] Token refreshed for session {session_id}")
            
            return new_token
            
        except Exception as e:
            logger.error(f"[TokenManager] Error refreshing token: {e}")
            return None
    
    def get_session_id(self, token: str) -> Optional[str]:
        """
        Extract session ID from a token without full validation.
        
        Args:
            token: JWT token string
        
        Returns:
            Session ID if extractable, None otherwise
        """
        try:
            # Decode without verification to get session_id
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            return payload.get("session_id")
        except Exception:
            return None


class SessionManager:
    """
    Manages active WebSocket sessions.
    
    Tracks session metadata, handles cleanup, and enforces session limits.
    
    Attributes:
        sessions: Dict of active sessions {session_id: session_data}
        max_sessions: Maximum number of concurrent sessions
        session_timeout: Session timeout in seconds
    """
    
    def __init__(
        self,
        max_sessions: int = 100,
        session_timeout: int = 3600
    ) -> None:
        """
        Initialize SessionManager.
        
        Args:
            max_sessions: Maximum concurrent sessions (default: 100)
            session_timeout: Session timeout in seconds (default: 3600)
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.debug(
            f"[SessionManager] Initialized with max_sessions={max_sessions}, "
            f"timeout={session_timeout}s"
        )
    
    def create_session(
        self,
        client_ip: str,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Create a new session.
        
        Args:
            client_ip: Client IP address
            user_agent: Client user agent string
        
        Returns:
            Session ID
        
        Raises:
            RuntimeError: If max sessions limit reached
        """
        if len(self.sessions) >= self.max_sessions:
            logger.error(
                f"[SessionManager] Max sessions ({self.max_sessions}) reached, "
                "cannot create new session"
            )
            raise RuntimeError("Maximum number of sessions reached")
        
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            "id": session_id,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "message_count": 0,
        }
        
        logger.info(
            f"[SessionManager] Created session {session_id} for {client_ip}"
        )
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session data if exists, None otherwise
        """
        return self.sessions.get(session_id)
    
    def update_activity(self, session_id: str) -> bool:
        """
        Update session last activity timestamp.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if session exists, False otherwise
        """
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = datetime.utcnow()
            self.sessions[session_id]["message_count"] += 1
            return True
        return False
    
    def remove_session(self, session_id: str) -> bool:
        """
        Remove a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if session was removed, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"[SessionManager] Removed session {session_id}")
            return True
        return False
    
    def get_active_sessions(self) -> int:
        """
        Get count of active sessions.
        
        Returns:
            Number of active sessions
        """
        return len(self.sessions)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information for monitoring.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session information dict or None
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        return {
            "session_id": session["id"],
            "client_ip": session["client_ip"],
            "created_at": session["created_at"].isoformat(),
            "last_activity": session["last_activity"].isoformat(),
            "message_count": session["message_count"],
            "duration": (datetime.utcnow() - session["created_at"]).total_seconds()
        }
    
    async def start_cleanup_task(self) -> None:
        """Start background task to cleanup expired sessions."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("[SessionManager] Cleanup task started")
    
    async def stop_cleanup_task(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("[SessionManager] Cleanup task stopped")
    
    async def _cleanup_loop(self) -> None:
        """Background loop to cleanup expired sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Run cleanup every minute
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[SessionManager] Cleanup error: {e}")
    
    async def _cleanup_expired_sessions(self) -> None:
        """Remove sessions that have timed out."""
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            last_activity = session["last_activity"]
            time_since_activity = (now - last_activity).total_seconds()
            
            if time_since_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.remove_session(session_id)
            logger.info(
                f"[SessionManager] Removed expired session {session_id}"
            )
        
        if expired_sessions:
            logger.info(
                f"[SessionManager] Cleaned up {len(expired_sessions)} expired sessions"
            )
