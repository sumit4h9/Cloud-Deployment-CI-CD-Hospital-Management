from fastapi import Header, HTTPException, status, Depends
from typing import Optional, List
from pydantic import BaseModel

class CurrentUser(BaseModel):
    id: str
    role: str  # "doctor", "patient", "admin"
    name: str

def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
) -> CurrentUser:
    """
    Authenticate user via Authorization header or role headers.
    Supports token formats:
    - 'Bearer doctor-ananya' -> doctor (doc_1)
    - 'Bearer patient-1042'  -> patient (pat_1042)
    - Custom header: X-User-Role & X-User-Id
    """
    role = x_user_role
    user_id = x_user_id
    name = "Authenticated User"

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1].lower()
        if "doctor" in token or "ananya" in token:
            role = role or "doctor"
            user_id = user_id or "doc_1"
            name = "Dr. Ananya Mehta"
        elif "patient" in token:
            role = role or "patient"
            user_id = user_id or "pat_1042"
            name = "Patient #1042"
        elif "admin" in token:
            role = role or "admin"
            user_id = user_id or "admin_1"
            name = "System Admin"

    # Fallback default for demo/convenience if no header provided
    if not role:
        role = "doctor"
        user_id = "doc_1"
        name = "Dr. Ananya Mehta"

    return CurrentUser(id=user_id, role=role, name=name)

def require_role(allowed_roles: List[str]):
    def role_checker(user: CurrentUser = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Access requires one of roles: {', '.join(allowed_roles)}"
            )
        return user
    return role_checker

