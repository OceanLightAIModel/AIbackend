# app/route/__init__.py

from .auth import auth_router
from .token import router as token_router
from .thread import threads_router
from .message import router as message_router


