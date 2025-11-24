"""
FastAPI Backend for Survey Sensei
Main entry point for the agent orchestration API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Union
from config import settings
from agents import survey_agent
from database import db
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Survey Sensei Backend",
    description="AI-powered survey generation and review creation backend",
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class StartSurveyRequest(BaseModel):
    """Request to start a new survey session"""

    user_id: str
    item_id: str
    form_data: Dict[str, Any]


class StartSurveyResponse(BaseModel):
    """Response with first survey question"""

    session_id: str
    question: Dict[str, Any]
    question_number: int
    total_questions: int


class SubmitAnswerRequest(BaseModel):
    """Request to submit an answer"""

    session_id: str
    answer: Union[str, List[str]]  # Can be single string or array for multi-select


class EditAnswerRequest(BaseModel):
    """Request to edit a previous answer"""

    session_id: str
    question_number: int
    answer: str


class SubmitAnswerResponse(BaseModel):
    """Response with next question or review options"""

    session_id: str
    status: str  # 'continue' or 'completed'
    question: Optional[Dict[str, Any]] = None
    question_number: Optional[int] = None
    total_questions: Optional[int] = None
    review_options: Optional[List[Dict[str, Any]]] = None


class SubmitReviewRequest(BaseModel):
    """Request to submit selected review"""

    session_id: str
    selected_review_index: int


class SubmitReviewResponse(BaseModel):
    """Response after saving review"""

    session_id: str
    status: str
    review: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    environment: str


# ============================================================================
# ENDPOINTS
# ============================================================================


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment,
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment,
    }


@app.post("/api/survey/start", response_model=StartSurveyResponse)
async def start_survey(request: StartSurveyRequest):
    """
    Start a new survey session

    This endpoint:
    1. Invokes Agent 1 (Product Context) and Agent 2 (Customer Context) in parallel
    2. Generates initial survey questions using Agent 3
    3. Returns the first question to display

    Args:
        request: User ID, item ID, and form data

    Returns:
        First survey question with session ID
    """
    try:
        result = survey_agent.start_survey(
            user_id=request.user_id,
            item_id=request.item_id,
            form_data=request.form_data,
        )

        return StartSurveyResponse(
            session_id=result["session_id"],
            question=result["question"],
            question_number=result["question_number"],
            total_questions=result["total_questions"],
        )

    except Exception as e:
        import traceback
        print(f"ERROR in start_survey: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to start survey: {str(e)}")


@app.post("/api/survey/answer", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """
    Submit an answer and get next question

    This endpoint:
    1. Records the user's answer
    2. Updates conversation state
    3. Determines if more questions needed or survey complete
    4. Returns next question OR review options

    Args:
        request: Session ID and user's answer

    Returns:
        Next question or review options if survey complete
    """
    try:
        result = survey_agent.submit_answer(
            session_id=request.session_id,
            answer=request.answer,
        )

        if result.get("status") == "completed":
            return SubmitAnswerResponse(
                session_id=result["session_id"],
                status="completed",
                review_options=result["review_options"],
            )
        else:
            return SubmitAnswerResponse(
                session_id=result["session_id"],
                status="continue",
                question=result["question"],
                question_number=result["question_number"],
                total_questions=result["total_questions"],
            )

    except Exception as e:
        import traceback
        print(f"ERROR in submit_answer: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@app.post("/api/survey/edit", response_model=SubmitAnswerResponse)
async def edit_answer(request: EditAnswerRequest):
    """
    Edit a previous answer and branch from that question

    This endpoint:
    1. Reverts the survey state to the specified question
    2. Updates the answer
    3. Discards all subsequent answers
    4. Returns the next question to continue from

    Args:
        request: Session ID, question number, and new answer

    Returns:
        Next question to continue the survey
    """
    try:
        result = survey_agent.edit_answer(
            session_id=request.session_id,
            question_number=request.question_number,
            new_answer=request.answer,
        )

        if result.get("status") == "completed":
            return SubmitAnswerResponse(
                session_id=result["session_id"],
                status="completed",
                review_options=result.get("review_options"),
            )
        else:
            return SubmitAnswerResponse(
                session_id=result["session_id"],
                status="continue",
                question=result["question"],
                question_number=result["question_number"],
                total_questions=result["total_questions"],
            )

    except Exception as e:
        import traceback
        print(f"ERROR in edit_answer: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to edit answer: {str(e)}")


@app.post("/api/survey/review", response_model=SubmitReviewResponse)
async def submit_review(request: SubmitReviewRequest):
    """
    Submit selected review and complete survey

    This endpoint:
    1. Saves the user's selected review to database
    2. Marks survey session as completed
    3. Returns confirmation

    Args:
        request: Session ID and selected review index (0-2)

    Returns:
        Confirmation with saved review details
    """
    try:
        result = survey_agent.submit_review(
            session_id=request.session_id,
            selected_review_index=request.selected_review_index,
        )

        return SubmitReviewResponse(
            session_id=result["session_id"],
            status=result["status"],
            review=result["review"],
        )

    except Exception as e:
        import traceback
        print(f"ERROR in submit_review: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to submit review: {str(e)}")


@app.get("/api/survey/session/{session_id}")
async def get_survey_session(session_id: str):
    """
    Get survey session details

    Args:
        session_id: Survey session ID

    Returns:
        Session state and conversation history
    """
    try:
        session = db.get_survey_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return session

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch session: {str(e)}")


@app.get("/api/survey/questions/{session_id}")
async def get_session_questions(session_id: str):
    """
    Get all questions for a survey session

    Args:
        session_id: Survey session ID

    Returns:
        List of all questions asked in this session
    """
    try:
        questions = db.get_session_questions(session_id)
        return {"session_id": session_id, "questions": questions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch questions: {str(e)}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=settings.environment == "development",
    )
