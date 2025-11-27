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
        session = db.get_survey_session(state["session_id"])
        session_context = session.get("session_context", {})
        form_data = session_context.get("form_data", {}) if isinstance(session_context, dict) else {}

        product_context = product_context_agent.generate_context(
            item_id=state["item_id"],
            has_reviews=form_data.get("hasReviews") == "yes",
            form_data=form_data,
        )

        customer_context = customer_context_agent.generate_context(
            user_email=form_data.get("userPersona", {}).get("email", ""),
            item_id=state["item_id"],
            has_purchased_similar=form_data.get("userHasPurchasedSimilar") == "yes",
            form_data=form_data,
        )

        return {
            "product_context": product_context.dict(),
            "customer_context": customer_context.dict(),
            "conversation_history": [
                {
                    "role": "system",
                    "content": f"Product Context: {json.dumps(product_context.dict(), indent=2)}\n\n"
                    f"Customer Context: {json.dumps(customer_context.dict(), indent=2)}",
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

        # Save question to database
        db.save_survey_question(
            session_id=state["session_id"],
            question_text=current_q["question_text"],
            question_options=current_q["options"],
            explanation=current_q.get("reasoning", ""),
            metadata={"index": state["current_question_index"]},
        )

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

        return {
            "answers": updated_answers,
            "current_question_index": next_index,
            "consecutive_skips": consecutive_skips,
            "conversation_history": conversation_update,
        }

    def _generate_followup_questions(self, state: SurveyState) -> Dict[str, Any]:
        """Generate adaptive follow-up questions"""
        if state["total_questions_asked"] >= settings.max_survey_questions:
            return {"next_action": "complete_survey"}

        parser = PydanticOutputParser(pydantic_object=SurveyQuestionnaire)

        answers_summary = "\n".join(
            [
                f"Q{i+1}: {ans['question']}\nA: {ans['answer']}"
                for i, ans in enumerate(state["answers"])
            ]
        )

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

Skipped Questions Count: {skipped_count}
Consecutive Skips: {consecutive_skips}

Generate {num_questions} follow-up questions that build on the conversation.
Pay special attention to avoid repetition and make questions more relevant if user has been skipping.

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
        total_asked = state["total_questions_asked"]
        total_available = len(state["all_questions"])

        if total_asked >= settings.max_survey_questions:
            return "complete_survey"

        if total_asked >= settings.min_survey_questions:
            if total_asked % 3 == 0 and total_asked < settings.max_survey_questions:
                return "generate_followup"
            elif state["current_question_index"] >= total_available:
                return "complete_survey"

        if state["current_question_index"] < total_available:
            return "ask_next"
        else:
            return "generate_followup"

    def start_survey(self, user_id: str, item_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start new survey session, return first question"""
        session_id = db.create_survey_session(
            user_id=user_id,
            item_id=item_id,
            metadata={"form_data": form_data},
        )

        initial_state: SurveyState = {
            "session_id": session_id,
            "user_id": user_id,
            "item_id": item_id,
            "product_context": None,
            "customer_context": None,
            "all_questions": [],
            "current_question_index": 0,
            "answers": [],
            "total_questions_asked": 0,
            "skipped_questions": [],
            "consecutive_skips": 0,
            "asked_question_texts": [],
            "conversation_history": [],
            "next_action": "fetch_contexts",
        }

        result = self.graph.invoke(initial_state)

        db.update_survey_session(
            session_id=session_id,
            conversation_history=result.get("conversation_history", []),
            state="active",
            metadata={"form_data": form_data, "current_state": result},
        )

        current_q = result["all_questions"][result["current_question_index"]]

        return {
            "session_id": session_id,
            "question": current_q,
            "question_number": result["current_question_index"] + 1,
            "total_questions": len(result["all_questions"]),
        }

    def submit_answer(self, session_id: str, answer: str) -> Dict[str, Any]:
        """Submit answer, get next question"""
        session = db.get_survey_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session_context = session.get("session_context", {})
        current_state = session_context.get("current_state", {})

        current_index = current_state.get("current_question_index", 0)
        all_questions = current_state.get("all_questions", [])

        if current_index >= len(all_questions):
            raise ValueError(
                f"Invalid question index {current_index}. "
                f"This may be due to submitting multiple answers rapidly. "
                f"Please wait for the previous answer to be processed."
            )

        state_update = self._process_answer(current_state, answer)
        updated_state = {**current_state, **state_update}

        next_route = self._route_after_answer(updated_state)

        if next_route == "complete_survey":
            db.update_survey_session(
                session_id=session_id,
                conversation_history=updated_state.get("conversation_history", []),
                state="survey_completed",
                metadata={"current_state": updated_state},
            )

            return {
                "session_id": session_id,
                "status": "survey_completed",
            }
        elif next_route == "generate_followup":
            followup_update = self._generate_followup_questions(updated_state)
            updated_state = {**updated_state, **followup_update}

            present_update = self._present_question(updated_state)
            updated_state = {**updated_state, **present_update}

        db.update_survey_session(
            session_id=session_id,
            conversation_history=updated_state.get("conversation_history", []),
            state="active",
            metadata={"current_state": updated_state},
        )

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
        }

    def skip_question(self, session_id: str) -> Dict[str, Any]:
        """Skip question with limits"""
        session = db.get_survey_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session_context = session.get("session_context", {})
        current_state = session_context.get("current_state", {})

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
        all_questions = current_state.get("all_questions", [])
        current_index = current_state.get("current_question_index", 0)
        remaining_questions = len(all_questions) - current_index

        MIN_ANSWERED_QUESTIONS = 3
        if total_answered < MIN_ANSWERED_QUESTIONS and remaining_questions <= 1:
            raise ValueError(
                f"You must answer at least {MIN_ANSWERED_QUESTIONS} questions to complete the survey. "
                f"You've answered {total_answered} so far."
            )

        state_update = self._process_answer(current_state, answer=None, is_skipped=True)
        updated_state = {**current_state, **state_update}

        next_route = self._route_after_answer(updated_state)

        if next_route == "complete_survey":
            if total_answered + 1 < MIN_ANSWERED_QUESTIONS:
                next_route = "generate_followup"

        if next_route == "complete_survey":
            db.update_survey_session(
                session_id=session_id,
                conversation_history=updated_state.get("conversation_history", []),
                state="survey_completed",
                metadata={"current_state": updated_state},
            )

            return {
                "session_id": session_id,
                "status": "survey_completed",
            }
        elif next_route == "generate_followup":
            followup_update = self._generate_followup_questions(updated_state)
            updated_state = {**updated_state, **followup_update}

            present_update = self._present_question(updated_state)
            updated_state = {**updated_state, **present_update}

        db.update_survey_session(
            session_id=session_id,
            conversation_history=updated_state.get("conversation_history", []),
            state="active",
            metadata={"current_state": updated_state},
        )

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
            "skipped_count": len(updated_state.get("skipped_questions", [])),
            "consecutive_skips": updated_state.get("consecutive_skips", 0),
        }

    def edit_answer(self, session_id: str, question_number: int, new_answer: str) -> Dict[str, Any]:
        """Edit previous answer, branch from that point"""
        session = db.get_survey_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session_context = session.get("session_context", {})
        current_state = session_context.get("current_state", {})

        question_index = question_number - 1

        if question_index < 0 or question_index >= len(current_state.get("answers", [])):
            raise ValueError(f"Invalid question number: {question_number}")

        branched_answers = current_state["answers"][:question_index]

        current_q = current_state["all_questions"][question_index]
        new_answer_record = {
            "question_index": question_index,
            "question": current_q["question_text"],
            "answer": new_answer,
            "timestamp": datetime.utcnow().isoformat(),
        }
        branched_answers.append(new_answer_record)

        branched_conversation = []
        for ans in branched_answers:
            branched_conversation.extend([
                {"role": "assistant", "content": ans["question"]},
                {"role": "user", "content": ans["answer"]},
            ])

        branched_state = {
            **current_state,
            "answers": branched_answers,
            "conversation_history": branched_conversation,
            "current_question_index": question_index + 1,
            "total_questions_asked": len(branched_answers),
            "generated_reviews": None,
        }

        db.update_survey_session(
            session_id=session_id,
            conversation_history=branched_conversation,
            state="active",
            metadata={"current_state": branched_state},
        )

        if branched_state["current_question_index"] >= len(branched_state["all_questions"]):
            return {
                "session_id": session_id,
                "status": "completed",
                "message": "Reached end of survey after editing"
            }

        current_q = branched_state["all_questions"][branched_state["current_question_index"]]

        return {
            "session_id": session_id,
            "status": "continue",
            "question": current_q,
            "question_number": branched_state["current_question_index"] + 1,
            "total_questions": len(branched_state["all_questions"]),
        }


survey_agent = SurveyAgent()
