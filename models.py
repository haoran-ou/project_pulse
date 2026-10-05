from pydantic import BaseModel

class Meeting(BaseModel):
    project_name: str 
    meeting_text: str 

class MeetingUpdate(BaseModel):
    project_name: str | None = None
    meeting_text: str | None = None

class AnalysisTask(BaseModel):
    task: str
    owner: str
    status: str

class MeetingAnalysis(BaseModel):
    summary: str
    tasks: list[AnalysisTask]
    risks: list[str]