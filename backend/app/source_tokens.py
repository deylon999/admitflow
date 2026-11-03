"""Short owner-bound confirmation; contains no public code, cookie or owner hash."""
import base64
import hashlib
import hmac
import json
import re

from pydantic import BaseModel,ConfigDict,Field,ValidationError


class Confirmation(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True,frozen=True)
    version:int=Field(ge=1,le=1)
    source_id:str=Field(min_length=1,max_length=36)
    group_id:str=Field(min_length=1,max_length=36)
    snapshot_id:str=Field(min_length=1,max_length=36)
    candidate_key:str=Field(pattern='^[a-f0-9]{64}$',repr=False)
    expires:int


class ConfirmationError(Exception):
    def __init__(self,code):self.code=code;super().__init__(code)


def signature(payload,owner,key):
    return hmac.new(key,b'archive-confirmation-v1\0'+owner.encode()+b'\0'+payload.encode(),hashlib.sha256).hexdigest()


def issue(claims,owner,key):
    payload=base64.urlsafe_b64encode(claims.model_dump_json().encode()).decode().rstrip('=')
    return payload+'.'+signature(payload,owner,key)


def verify(token,owner,key,now,*,allow_expired=False):
    if not isinstance(token,str) or len(token)>2048 or not re.fullmatch(r'[A-Za-z0-9_-]+\.[a-f0-9]{64}',token):
        raise ConfirmationError('invalid')
    payload,mac=token.split('.')
    if not hmac.compare_digest(mac,signature(payload,owner,key)):raise ConfirmationError('invalid')
    try:
        claims=Confirmation.model_validate_json(base64.urlsafe_b64decode(payload+'='*(-len(payload)%4)))
    except (ValueError,TypeError,ValidationError):raise ConfirmationError('invalid') from None
    if not allow_expired and now>=claims.expires:raise ConfirmationError('expired')
    return claims
