"""Authenticated profile and companion endpoints."""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, model_validator

from app.models.auth import AuthenticatedUser
from app.models.conversation import ConversationTurn
from app.models.profile import ProfilePreferences
from app.services import wellness_service
from app.services.gemini_text import CompanionUnavailable
from app.utils.auth import get_current_user

router = APIRouter(tags=["wellbeing"])
User = Annotated[AuthenticatedUser, Depends(get_current_user)]


class ChatRequest(BaseModel):
    turns: list[ConversationTurn] = Field(min_length=1, max_length=40)

    @model_validator(mode="after")
    def validate_context(self) -> "ChatRequest":
        if (
            self.turns[-1].role != "user"
            or sum(len(t.text) for t in self.turns) > 12000
        ):
            raise ValueError(
                "Chat must end with a user message and stay within 12,000 characters"
            )
        return self


async def execute(function: Callable[..., Any], *args: Any) -> Any:
    try:
        return await run_in_threadpool(function, *args)
    except CompanionUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            503, "Your wellbeing data could not be loaded. Please try again."
        ) from exc


@router.get("/profile", response_model=ProfilePreferences)
async def get_profile(user: User) -> ProfilePreferences:
    return await execute(wellness_service.read_profile, user.uid)


@router.put("/profile", response_model=ProfilePreferences)
async def put_profile(payload: ProfilePreferences, user: User) -> ProfilePreferences:
    return await execute(wellness_service.save_profile, user.uid, payload)


@router.get("/mood/streak")
async def get_streak(user: User) -> dict[str, int | bool]:
    return await execute(wellness_service.streak_for_user, user.uid)


@router.post("/assistant/chat")
async def post_chat(payload: ChatRequest, user: User) -> dict[str, str]:
    return {
        "reply": await execute(wellness_service.chat_reply, user.uid, payload.turns)
    }


@router.post("/mood/insight")
async def post_insight(
    user: User, days: Annotated[int, Query(ge=1, le=30)] = 7
) -> dict[str, str]:
    return {"message": await execute(wellness_service.mood_insight, user.uid, days)}
