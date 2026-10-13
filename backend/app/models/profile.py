"""Optional preference questionnaire without identity information."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class ProfilePreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goal: Literal[
        "",
        "Understand my feelings",
        "Manage everyday stress",
        "Build a reflection habit",
        "Feel more balanced",
    ] = ""
    support_style: Literal[
        "", "Gentle encouragement", "Practical small steps", "Questions to reflect on"
    ] = ""
    calming_activity: Literal[
        "", "Music", "Walking", "Breathing", "Writing", "Talking to someone"
    ] = ""
    check_in_time: Literal["", "Morning", "Afternoon", "Evening", "Whenever works"] = ""
    onboarding_complete: bool = False
