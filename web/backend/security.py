import secrets
from fastapi import Request, HTTPException, status

async def require_csrf(request: Request) -> None:
    session_csrf = request.session.get("csrf_token")
    if not session_csrf:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing session CSRF token"
        )
        
    client_csrf = request.headers.get("X-CSRF-Token")
    
    if not client_csrf:
        # Check form data if it's a form post
        try:
            form_data = await request.form()
            client_csrf = form_data.get("csrf_token")
        except Exception:
            pass

    if not client_csrf:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing client CSRF token"
        )
        
    if not secrets.compare_digest(session_csrf, client_csrf):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token"
        )
