"""
Agent 3: Survey generation with adaptive questioning.
Reviews handled by Agent 4.
"""

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any, TypedDict, Annotated, Sequence, Optional
from typing_extensions import TypedDict
import operator
from config import settings
from database import db
from .product_context_agent import product_context_agent, ProductContext
from .customer_context_agent import customer_context_agent, CustomerContext
import json
from datetime import datetime
import asyncio


class SurveyQuestion(BaseModel):
    question_text: str = Field(description="The question to ask the user")
    options: List[str] = Field(description="4-6 multiple choice options")
    allow_multiple: bool = Field(description="True if multiple options can be selected")
    reasoning: str = Field(description="Why this question is relevant")


class SurveyQuestionnaire(BaseModel):
    questions: List[SurveyQuestion] = Field(description="List of 3-5 survey questions")
    survey_goal: str = Field(description="Overall goal of this survey batch")


class SurveyState(TypedDict):
    session_id: str
    user_id: str
    item_id: str
    product_context: Optional[Dict[str, Any]]
    customer_context: Optional[Dict[str, Any]]
    all_questions: List[Dict[str, Any]]
    current_question_index: int
    answers: List[Dict[str, Any]]
    total_questions_asked: int
    answered_questions_count: int  # Count of answered questions (excluding skips)
    skipped_questions: List[int]
    consecutive_skips: int
    asked_question_texts: List[str]
    conversation_history: Annotated[Sequence[Dict[str, str]], operator.add]
    next_action: str


class SurveyAgent:

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key,
        )
        self.graph = self._build_graph()
        # In-memory session state cache (session_id -> state dict)
        # Avoids database writes on every answer
        self._session_state_cache: Dict[str, Dict[str, Any]] = {}

    def _log_event_async(
        self,
        session_id: str,
        event_type: str,
        event_detail: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Fire-and-forget async event logging

        Non-blocking - errors are logged but don't crash user flow.
        Events are logged to survey_details table for analytics.

        Args:
            session_id: Session UUID
            event_type: Event type (question_generated, answer_submitted, etc.)
            event_detail: Optional JSONB event data
        """
        async def _log():
            try:
                await db.insert_survey_detail_async(session_id, event_type, event_detail)
            except Exception as e:
                print(f"Background event log failed ({event_type}): {e}")

        # Fire-and-forget
        asyncio.create_task(_log())

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(SurveyState)
        workflow.add_node("fetch_contexts", self._fetch_contexts)
        workflow.add_node("generate_initial_questions", self._generate_initial_questions)
        workflow.add_node("present_question", self._present_question)
        workflow.set_entry_point("fetch_contexts")
        workflow.add_edge("fetch_contexts", "generate_initial_questions")
        workflow.add_edge("generate_initial_questions", "present_question")
        workflow.add_conditional_edges(
            "present_question",
            self._route_after_question,
            {"wait_for_answer": END, "complete_survey": END},
        )
        return workflow.compile()

    def _fetch_contexts(self, state: SurveyState) -> Dict[str, Any]:
        """
        Legacy node - contexts are now fetched in start_survey() before graph invocation.
        This node is skipped by setting next_action="generate_initial_questions".
        Kept for backwards compatibility with LangGraph structure.
        """
        # Contexts already in state from start_survey()
        # Just return them with conversation_history
        return {
            "product_context": state.get("product_context", {}),
            "customer_context": state.get("customer_context", {}),
            "conversation_history": [
                {
                    "role": "system",
                    "content": f"Product Context: {json.dumps(state.get('product_context', {}), indent=2)}\n\n"
                    f"Customer Context: {json.dumps(state.get('customer_context', {}), indent=2)}",
                }
            ],
        }

    def _generate_initial_questions(self, state: SurveyState) -> Dict[str, Any]:
        parser = PydanticOutputParser(pydantic_object=SurveyQuestionnaire)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert survey designer. Generate personalized survey questions based on:
1. Product context (features, concerns, pros/cons)
2. Customer context (expectations, pain points, motivations)

Create {num_questions} engaging multiple-choice questions that will help understand the user's experience and generate an authentic review.

Guidelines:
- Questions should be specific and actionable
- Options should cover diverse perspectives
- Build on both product and customer insights
- Questions should flow naturally
- Avoid generic questions
- Set allow_multiple=true for questions where multiple options can logically be selected together (e.g., "What features do you use?", "What concerns do you have?")
- Set allow_multiple=false for mutually exclusive questions (e.g., "How satisfied are you?", "Would you recommend?")

CRITICAL GUARDRAILS:
- NEVER repeat questions - each question must be unique in wording and intent
- NEVER repeat options across questions - ensure option diversity
- Options within a question must be mutually distinct (no similar/overlapping options)
- If a question allows multiple choices and conceptually could have "All of the above", include it as the last option
- If appropriate, include "Other" as the last option to allow user input for unlisted choices
- Track previously asked questions to ensure no repetition throughout the survey""",
                ),
                (
                    "human",
                    """Product Context:
{product_context}

Customer Context:
{customer_context}

Generate {num_questions} initial survey questions. Each question should have 4-6 options.

{format_instructions}""",
                ),
            ]
        )

        chain = prompt | self.llm | parser

        questionnaire = chain.invoke(
            {
                "product_context": json.dumps(state["product_context"], indent=2),
                "customer_context": json.dumps(state["customer_context"], indent=2),
                "num_questions": settings.initial_questions_count,
                "format_instructions": parser.get_format_instructions(),
            }
        )

        # Convert questions to dict format and validate
        questions = []
        for q in questionnaire.questions:
            q_dict = q.dict()
            # Ensure question has at least 2 options
            if not q_dict.get("options") or len(q_dict["options"]) < 2:
                print(f"WARNING: Question has insufficient options, skipping: {q_dict.get('question_text')}")
                continue
            questions.append(q_dict)

        # If no valid questions, raise error
        if not questions:
            raise ValueError("No valid questions generated - all questions missing options")

        return {
            "all_questions": questions,
            "current_question_index": 0,
            "total_questions_asked": 0,
            "next_action": "ask_question",
        }

    def _present_question(self, state: SurveyState) -> Dict[str, Any]:
        """
        Node 3: Present current question to user
        Returns question for UI to display
        """
        if state["current_question_index"] >= len(state["all_questions"]):
            # No more questions, survey complete - return to API (which will invoke Agent 4)
            return {"next_action": "complete_survey"}

        current_q = state["all_questions"][state["current_question_index"]]

        # Track asked question to prevent repetition
        asked_texts = list(state.get("asked_question_texts", []))
        if current_q["question_text"] not in asked_texts:
            asked_texts.append(current_q["question_text"])

        # Note: Questions are logged via question_generated events in survey_details table
        # No need to save to old survey table (removed for new schema)

        return {
            "total_questions_asked": state["total_questions_asked"] + 1,
            "asked_question_texts": asked_texts,
            "next_action": "wait_for_answer",
        }

    def _process_answer(self, state: SurveyState, answer, is_skipped: bool = False) -> Dict[str, Any]:
        """Process user's answer or skip, update state"""
        current_q = state["all_questions"][state["current_question_index"]]

        if is_skipped:
            skipped_list = list(state.get("skipped_questions", []))
            skipped_list.append(state["current_question_index"])
            consecutive_skips = state.get("consecutive_skips", 0) + 1

            conversation_update = list(state.get("conversation_history", [])) + [
                {"role": "assistant", "content": current_q["question_text"]},
                {"role": "user", "content": "[SKIPPED - User found this question irrelevant to their feedback]"},
            ]

            next_index = state["current_question_index"] + 1

            return {
                "current_question_index": next_index,
                "skipped_questions": skipped_list,
                "consecutive_skips": consecutive_skips,
                "conversation_history": conversation_update,
            }

        answer_text = ", ".join(answer) if isinstance(answer, list) else answer

        answer_record = {
            "question_index": state["current_question_index"],
            "question": current_q["question_text"],
            "answer": answer_text,
            "timestamp": datetime.utcnow().isoformat(),
        }

        updated_answers = list(state["answers"]) + [answer_record]

        conversation_update = list(state.get("conversation_history", [])) + [
            {"role": "assistant", "content": current_q["question_text"]},
            {"role": "user", "content": answer_text},
        ]

        consecutive_skips = 0
        next_index = state["current_question_index"] + 1
        # Increment answered questions count (excluding skips)
        answered_count = state.get("answered_questions_count", 0) + 1

        return {
            "answers": updated_answers,
            "current_question_index": next_index,
            "answered_questions_count": answered_count,
            "consecutive_skips": consecutive_skips,
            "conversation_history": conversation_update,
        }

    def _generate_followup_questions(self, state: SurveyState) -> Dict[str, Any]:
        """Generate adaptive follow-up questions with skip context"""
        if state["total_questions_asked"] >= settings.max_survey_questions:
            return {"next_action": "complete_survey"}

        parser = PydanticOutputParser(pydantic_object=SurveyQuestionnaire)

        # Build answers summary including answered questions only
        answers_summary = "\n".join(
            [
                f"Q{i+1}: {ans['question']}\nA: {ans['answer']}"
                for i, ans in enumerate(state["answers"])
            ]
        )

        # Build skipped questions context
        skipped_questions = state.get("skipped_questions", [])
        skipped_context = ""
        if skipped_questions:
            skipped_q_texts = []
            all_qs = state.get("all_questions", [])
            for idx in skipped_questions:
                if idx < len(all_qs):
                    skipped_q_texts.append(f"- {all_qs[idx]['question_text']}")
            if skipped_q_texts:
                skipped_context = "\n\nSkipped Questions (user found these irrelevant):\n" + "\n".join(skipped_q_texts)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert survey designer conducting an adaptive survey.
Based on the user's previous answers, generate {num_questions} relevant follow-up questions.

Guidelines:
- Build on previous answers to dig deeper
- Explore interesting angles from their responses
- Keep questions focused and specific
- Ensure questions flow naturally from the conversation
- Help gather insights for an authentic review
- Set allow_multiple=true for questions where multiple options can logically be selected together
- Set allow_multiple=false for mutually exclusive questions

CRITICAL GUARDRAILS:
- NEVER repeat questions - check asked_questions list and ensure each question is unique
- NEVER repeat options across questions - ensure option diversity
- Options within a question must be mutually distinct (no similar/overlapping options)
- If user has been skipping questions, generate more relevant and specific questions
- Pay attention to skipped questions - they indicate topics the user finds irrelevant
- If a question allows multiple choices and conceptually could have "All of the above", include it as the last option
- If appropriate, include "Other" as the last option to allow user input""",
                ),
                (
                    "human",
                    """Product Context:
{product_context}

Customer Context:
{customer_context}

Previous Q&A:
{previous_qa}

Already Asked Questions (DO NOT REPEAT):
{asked_questions}
{skipped_context}

Skipped Questions Count: {skipped_count}
Consecutive Skips: {consecutive_skips}

Generate {num_questions} follow-up questions that build on the conversation.
CRITICAL: If user has been skipping questions, AVOID topics similar to skipped questions.
Focus on topics the user HAS engaged with through their answers.
Make questions more specific, relevant, and actionable based on their actual responses.

{format_instructions}""",
                ),
            ]
        )

        chain = prompt | self.llm | parser

        num_followup = min(2, settings.max_survey_questions - state["total_questions_asked"])

        asked_questions_list = "\n".join(
            [f"- {q_text}" for q_text in state.get("asked_question_texts", [])]
        ) or "None yet"

        questionnaire = chain.invoke(
            {
                "product_context": json.dumps(state["product_context"], indent=2),
                "customer_context": json.dumps(state["customer_context"], indent=2),
                "previous_qa": answers_summary,
                "asked_questions": asked_questions_list,
                "skipped_context": skipped_context,
                "skipped_count": len(state.get("skipped_questions", [])),
                "consecutive_skips": state.get("consecutive_skips", 0),
                "num_questions": num_followup,
                "format_instructions": parser.get_format_instructions(),
            }
        )

        new_questions = []
        for q in questionnaire.questions:
            q_dict = q.dict()
            if not q_dict.get("options") or len(q_dict["options"]) < 2:
                print(f"WARNING: Followup question has insufficient options, skipping: {q_dict.get('question_text')}")
                continue
            new_questions.append(q_dict)

        updated_questions = list(state["all_questions"]) + new_questions

        return {
            "all_questions": updated_questions,
            "next_action": "ask_question",
        }

    def _route_after_question(self, state: SurveyState) -> str:
        if state["next_action"] == "complete_survey":
            return "complete_survey"
        return "wait_for_answer"

    def _route_after_answer(self, state: SurveyState) -> str:
        """
        Route logic based on answered questions count (excluding skips).
        Survey completes when 10-15 answered questions are reached.
        """
        total_asked = state["total_questions_asked"]
        answered_count = state.get("answered_questions_count", 0)
        total_available = len(state["all_questions"])

        # Complete if we've reached max answered questions (10-15 range)
        if answered_count >= settings.max_answered_questions:
            return "complete_survey"

        # Generate follow-ups if we've reached min answered questions and need more questions
        if answered_count >= settings.min_answered_questions:
            # Survey is now comprehensive - complete it
            return "complete_survey"

        # Safety check - don't exceed total question limit
        if total_asked >= settings.max_survey_questions:
            if answered_count >= settings.min_answered_questions:
                return "complete_survey"
            else:
                # Need more answered questions - generate follow-ups
                return "generate_followup"

        # Generate follow-ups every few questions or when running out of questions
        if answered_count > 0 and answered_count % 3 == 0:
            return "generate_followup"

        if state["current_question_index"] < total_available:
            return "ask_next"
        else:
            return "generate_followup"

    def _complete_survey(self, session_id: str, final_state: Dict[str, Any]) -> None:
        """
        Complete survey session with final Q&A and complete state

        Called when survey reaches completion criteria.
        Populates questions_and_answers and session_context JSONB in survey_sessions table.

        Args:
            session_id: Session UUID
            final_state: Final survey state with all answers
        """
        # Build questions_and_answers JSONB from state
        questions_and_answers = []
        for ans in final_state["answers"]:
            questions_and_answers.append({
                "question_number": ans["question_index"] + 1,
                "question_text": ans["question"],
                "selected_option": ans["answer"],
                "timestamp": ans["timestamp"]
            })

        # Update survey_sessions with final Q&A
        db.complete_survey_session(
            session_id=session_id,
            questions_and_answers=questions_and_answers
        )

        # Store complete survey state in session_context
        db.update_session_context(
            session_id=session_id,
            session_context=final_state  # Complete survey agent state
        )

        # LOG EVENT: survey_completed (ASYNC)
        self._log_event_async(
            session_id=session_id,
            event_type="survey_completed",
            event_detail={
                "total_questions": len(final_state.get("all_questions", [])),
                "answered_count": final_state.get("answered_questions_count", 0),
                "skipped_count": len(final_state.get("skipped_questions", [])),
                "completion_time": datetime.utcnow().isoformat()
            }
        )

    def start_survey(self, user_id: str, item_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start new survey session (SMP → SVP transition)

        Creates session with frozen agent contexts at start.
        Populates product_context and customer_context JSONB immediately.

        Args:
            user_id: User UUID
            item_id: Product item_id
            form_data: Frontend form data (for backwards compatibility)

        Returns:
            dict: First question and session metadata
        """
        # STEP 1: Fetch agent contexts FIRST (frozen after start)
        product_context = product_context_agent.generate_context(item_id=item_id)
        customer_context = customer_context_agent.generate_context(user_id=user_id, item_id=item_id)

        # STEP 2: Get transaction (MUST exist from data engineering step)
        existing_txn = db.get_user_transaction_for_product(user_id, item_id)
        if not existing_txn:
            raise ValueError(
                f"Transaction not found for user {user_id} and product {item_id}. "
                f"The transaction MUST be created during the data engineering step (mock data generation). "
                f"Please ensure the current transaction was created properly."
            )

        transaction_id = existing_txn["transaction_id"]

        # STEP 3: Create session with contexts (NEW SCHEMA)
        session_id = db.create_survey_session(
            user_id=user_id,
            item_id=item_id,
            transaction_id=transaction_id,
            product_context=product_context.dict(),  # JSONB - frozen
            customer_context=customer_context.dict()   # JSONB - frozen
        )

        # STEP 4: Generate initial questions (existing LangGraph logic)
        initial_state: SurveyState = {
            "session_id": session_id,
            "user_id": user_id,
            "item_id": item_id,
            "product_context": product_context.dict(),
            "customer_context": customer_context.dict(),
            "all_questions": [],
            "current_question_index": 0,
            "answers": [],
            "total_questions_asked": 0,
            "answered_questions_count": 0,
            "skipped_questions": [],
            "consecutive_skips": 0,
            "asked_question_texts": [],
            "conversation_history": [],
            "next_action": "generate_initial_questions",  # Skip fetch_contexts (already done)
        }

        result = self.graph.invoke(initial_state)

        # STEP 5: Store state in-memory cache (lazy DB update - only at start and end)
        self._session_state_cache[session_id] = result

        # STEP 6: Log first question_generated event (ASYNC - fast update)
        current_q = result["all_questions"][result["current_question_index"]]
        self._log_event_async(
            session_id=session_id,
            event_type="question_generated",
            event_detail={
                "question_number": result["current_question_index"] + 1,
                "question_text": current_q["question_text"],
                "options": current_q["options"],
                "allow_multiple": current_q.get("allow_multiple", False),
                "reasoning": current_q.get("reasoning", "")
            }
        )

        return {
            "session_id": session_id,
            "question": current_q,
            "question_number": result["current_question_index"] + 1,
            "total_questions": len(result["all_questions"]),
            "answered_questions_count": result.get("answered_questions_count", 0),
        }

    def submit_answer(self, session_id: str, answer: str) -> Dict[str, Any]:
        """
        Submit answer, get next question

        Uses in-memory state cache (lazy DB update - only at completion).
        Logs answer_submitted event to survey_details (async fast update).
        """
        # Get state from in-memory cache
        current_state = self._session_state_cache.get(session_id)
        if not current_state:
            raise ValueError(f"Session state not found: {session_id}")

        current_index = current_state.get("current_question_index", 0)
        all_questions = current_state.get("all_questions", [])

        if current_index >= len(all_questions):
            raise ValueError(
                f"Invalid question index {current_index}. "
                f"This may be due to submitting multiple answers rapidly. "
                f"Please wait for the previous answer to be processed."
            )

        # Process answer
        state_update = self._process_answer(current_state, answer)
        updated_state = {**current_state, **state_update}

        # LOG EVENT: answer_submitted (ASYNC - fast update to survey_details)
        current_q = all_questions[current_index]
        self._log_event_async(
            session_id=session_id,
            event_type="answer_submitted",
            event_detail={
                "question_number": current_index + 1,
                "question_text": current_q["question_text"],
                "selected_option": answer,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        next_route = self._route_after_answer(updated_state)

        if next_route == "complete_survey":
            # COMPLETE SURVEY - Lazy update to survey_sessions
            self._complete_survey(session_id, updated_state)

            # Clear from cache
            del self._session_state_cache[session_id]

            return {
                "session_id": session_id,
                "status": "survey_completed",
                "answered_questions_count": updated_state.get("answered_questions_count", 0),
            }
        elif next_route == "generate_followup":
            # Generate follow-up questions
            followup_update = self._generate_followup_questions(updated_state)
            updated_state = {**updated_state, **followup_update}

            present_update = self._present_question(updated_state)
            updated_state = {**updated_state, **present_update}

            # LOG EVENT: question_generated (ASYNC - fast update to survey_details)
            next_q = updated_state["all_questions"][updated_state["current_question_index"]]
            self._log_event_async(
                session_id=session_id,
                event_type="question_generated",
                event_detail={
                    "question_number": updated_state["current_question_index"] + 1,
                    "question_text": next_q["question_text"],
                    "options": next_q["options"],
                    "allow_multiple": next_q.get("allow_multiple", False),
                    "reasoning": next_q.get("reasoning", "")
                }
            )

        # Update in-memory cache (NO DB write - lazy update only at completion)
        self._session_state_cache[session_id] = updated_state

        next_index = updated_state["current_question_index"]
        all_questions = updated_state["all_questions"]

        if next_index >= len(all_questions):
            raise ValueError(
                f"Question index {next_index} is out of bounds. "
                f"Total questions: {len(all_questions)}"
            )

        current_q = all_questions[next_index]

        return {
            "session_id": session_id,
            "question": current_q,
            "question_number": next_index + 1,
            "total_questions": len(all_questions),
            "answered_questions_count": updated_state.get("answered_questions_count", 0),
        }

    def skip_question(self, session_id: str) -> Dict[str, Any]:
        """Skip question with limits - uses in-memory cache"""
        # Get state from in-memory cache
        current_state = self._session_state_cache.get(session_id)
        if not current_state:
            raise ValueError(f"Session state not found in cache: {session_id}")

        consecutive_skips = current_state.get("consecutive_skips", 0)
        MAX_CONSECUTIVE_SKIPS = 3

        if consecutive_skips >= MAX_CONSECUTIVE_SKIPS:
            raise ValueError(
                f"You've skipped {consecutive_skips} questions in a row. "
                f"Please answer this question to continue the survey. "
                f"This helps us generate better, more relevant questions for you."
            )

        total_skipped = len(current_state.get("skipped_questions", []))
        total_answered = len(current_state.get("answers", []))
        answered_count = current_state.get("answered_questions_count", 0)
        all_questions = current_state.get("all_questions", [])
        current_index = current_state.get("current_question_index", 0)
        remaining_questions = len(all_questions) - current_index

        # Check if skipping would prevent reaching minimum answered questions
        if answered_count < settings.min_answered_questions and remaining_questions <= 1:
            raise ValueError(
                f"You must answer at least {settings.min_answered_questions} questions to complete the survey. "
                f"You've answered {answered_count} so far. Please answer this question."
            )

        # Get current question before processing skip
        current_q = current_state["all_questions"][current_state["current_question_index"]]

        state_update = self._process_answer(current_state, answer=None, is_skipped=True)
        updated_state = {**current_state, **state_update}

        # LOG EVENT: answer_skipped (ASYNC)
        self._log_event_async(
            session_id=session_id,
            event_type="answer_skipped",
            event_detail={
                "question_number": current_state["current_question_index"] + 1,
                "question_text": current_q["question_text"],
                "skip_count": len(updated_state.get("skipped_questions", [])),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        next_route = self._route_after_answer(updated_state)

        if next_route == "complete_survey":
            # Ensure we have minimum answered questions before completing
            if updated_state.get("answered_questions_count", 0) < settings.min_answered_questions:
                next_route = "generate_followup"

        if next_route == "complete_survey":
            # COMPLETE SURVEY - Lazy update
            self._complete_survey(session_id, updated_state)
            del self._session_state_cache[session_id]

            return {
                "session_id": session_id,
                "status": "survey_completed",
                "answered_questions_count": updated_state.get("answered_questions_count", 0),
            }
        elif next_route == "generate_followup":
            followup_update = self._generate_followup_questions(updated_state)
            updated_state = {**updated_state, **followup_update}

            present_update = self._present_question(updated_state)
            updated_state = {**updated_state, **present_update}

            # LOG EVENT: question_generated (ASYNC)
            next_q = updated_state["all_questions"][updated_state["current_question_index"]]
            self._log_event_async(
                session_id=session_id,
                event_type="question_generated",
                event_detail={
                    "question_number": updated_state["current_question_index"] + 1,
                    "question_text": next_q["question_text"],
                    "options": next_q["options"],
                    "allow_multiple": next_q.get("allow_multiple", False),
                    "reasoning": next_q.get("reasoning", "")
                }
            )

        # Update in-memory cache (NO DB write during survey)
        self._session_state_cache[session_id] = updated_state

        next_index = updated_state["current_question_index"]
        all_questions = updated_state["all_questions"]

        if next_index >= len(all_questions):
            raise ValueError(f"Question index out of bounds after skip")

        current_q = all_questions[next_index]

        return {
            "session_id": session_id,
            "question": current_q,
            "question_number": next_index + 1,
            "total_questions": len(all_questions),
            "answered_questions_count": updated_state.get("answered_questions_count", 0),
            "skipped_count": len(updated_state.get("skipped_questions", [])),
            "consecutive_skips": updated_state.get("consecutive_skips", 0),
        }

    def get_question_for_edit(self, session_id: str, question_number: int) -> Dict[str, Any]:
        """Get the original question for editing - uses in-memory cache"""
        # Get state from in-memory cache
        current_state = self._session_state_cache.get(session_id)
        if not current_state:
            raise ValueError(f"Session state not found in cache: {session_id}")

        question_index = question_number - 1
        all_questions = current_state.get("all_questions", [])

        if question_index < 0 or question_index >= len(all_questions):
            raise ValueError(f"Invalid question number: {question_number}")

        original_question = all_questions[question_index]

        return {
            "session_id": session_id,
            "question": original_question,
            "question_number": question_number,
            "is_edit_mode": True,
        }

    def edit_answer(self, session_id: str, question_number: int, new_answer: str) -> Dict[str, Any]:
        """Edit previous answer, branch from that point - uses in-memory cache"""
        # Get state from in-memory cache
        current_state = self._session_state_cache.get(session_id)
        if not current_state:
            raise ValueError(f"Session state not found in cache: {session_id}")

        question_index = question_number - 1
        all_questions = current_state.get("all_questions", [])

        # Allow editing both answered and skipped questions
        if question_index < 0 or question_index >= len(all_questions):
            raise ValueError(f"Invalid question number: {question_number}")

        # Get old answer for event logging
        old_answer = None
        for ans in current_state["answers"]:
            if ans["question_index"] == question_index:
                old_answer = ans["answer"]
                break

        branched_answers = current_state["answers"][:question_index]

        current_q = current_state["all_questions"][question_index]
        new_answer_record = {
            "question_index": question_index,
            "question": current_q["question_text"],
            "answer": new_answer,
            "timestamp": datetime.utcnow().isoformat(),
        }
        branched_answers.append(new_answer_record)

        # LOG EVENT: answer_updated (ASYNC)
        self._log_event_async(
            session_id=session_id,
            event_type="answer_updated",
            event_detail={
                "question_number": question_number,
                "question_text": current_q["question_text"],
                "old_option": old_answer,
                "new_option": new_answer,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        branched_conversation = []
        for ans in branched_answers:
            branched_conversation.extend([
                {"role": "assistant", "content": ans["question"]},
                {"role": "user", "content": ans["answer"]},
            ])

        # Recalculate answered_questions_count (excluding skipped questions)
        skipped_set = set(current_state.get("skipped_questions", []))
        # Update skipped set - remove skips from branched portion
        skipped_set = {idx for idx in skipped_set if idx < question_index}
        # Count only answered (non-skipped) questions in branched_answers
        answered_count = sum(1 for ans in branched_answers if ans["question_index"] not in skipped_set)

        branched_state = {
            **current_state,
            "answers": branched_answers,
            "conversation_history": branched_conversation,
            "current_question_index": question_index + 1,
            "total_questions_asked": len(branched_answers),
            "answered_questions_count": answered_count,
            "skipped_questions": list(skipped_set),
            "consecutive_skips": 0,  # Reset consecutive skips after edit
            "generated_reviews": None,
        }

        # Update in-memory cache (NO DB write during survey)
        self._session_state_cache[session_id] = branched_state

        if branched_state["current_question_index"] >= len(branched_state["all_questions"]):
            return {
                "session_id": session_id,
                "status": "completed",
                "answered_questions_count": branched_state.get("answered_questions_count", 0),
                "message": "Reached end of survey after editing"
            }

        current_q = branched_state["all_questions"][branched_state["current_question_index"]]

        return {
            "session_id": session_id,
            "status": "continue",
            "question": current_q,
            "question_number": branched_state["current_question_index"] + 1,
            "total_questions": len(branched_state["all_questions"]),
            "answered_questions_count": branched_state.get("answered_questions_count", 0),
        }

    def get_survey_state(self, session_id: str) -> Dict[str, Any]:
        """
        Get current survey state from in-memory cache or database

        Used for review generation to access survey answers.
        If survey is completed, state will be in database (session_context).
        If survey is in progress, state will be in in-memory cache.

        Args:
            session_id: Session UUID

        Returns:
            Complete survey state dict with answers, questions, etc.

        Raises:
            ValueError: If session not found in cache or database
        """
        # Try in-memory cache first (survey in progress)
        current_state = self._session_state_cache.get(session_id)
        if current_state:
            return current_state

        # Survey completed - retrieve from database session_context
        from database.supabase_client import db
        session = db.get_survey_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session_context = session.get("session_context")
        if not session_context:
            raise ValueError(f"Session state not found (survey may not be completed): {session_id}")

        return session_context


survey_agent = SurveyAgent()
