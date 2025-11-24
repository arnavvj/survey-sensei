"""
Agent 3: SURVEY_AND_REVIEW_AGENT
Stateful LangGraph agent for survey generation and review creation

Workflow:
1. Invoke Agent 1 and Agent 2 in parallel to get contexts
2. Generate initial survey questions (3 questions) based on contexts
3. Present questions one by one, collect answers
4. Generate follow-up questions based on previous answers (adaptive)
5. Handle question navigation (back/forward with state updates)
6. After survey completion, generate natural language review options
7. Save selected review to database

This is a stateful agent that maintains conversation history and adapts questions.
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


# ============================================================================
# STATE DEFINITIONS
# ============================================================================


class SurveyQuestion(BaseModel):
    """Single survey question with options"""

    question_text: str = Field(description="The question to ask the user")
    options: List[str] = Field(description="4-6 multiple choice options")
    allow_multiple: bool = Field(
        description="True if multiple options can be selected (non-mutually exclusive), False for single choice"
    )
    reasoning: str = Field(
        description="Why this question is relevant based on context"
    )


class SurveyQuestionnaire(BaseModel):
    """Collection of survey questions"""

    questions: List[SurveyQuestion] = Field(
        description="List of 3-5 survey questions"
    )
    survey_goal: str = Field(
        description="Overall goal of this survey batch"
    )


class ReviewOption(BaseModel):
    """Natural language review option"""

    review_text: str = Field(description="Complete review text")
    rating: int = Field(description="Star rating 1-5")
    sentiment: str = Field(description="positive, neutral, or negative")
    tone: str = Field(description="formal, casual, enthusiastic, critical, etc.")


class ReviewOptions(BaseModel):
    """Collection of review options for user to choose from"""

    options: List[ReviewOption] = Field(
        description="3 different review options"
    )


class SurveyState(TypedDict):
    """State for the survey conversation graph"""

    # Session info
    session_id: str
    user_id: str
    item_id: str

    # Contexts from Agent 1 and 2
    product_context: Optional[Dict[str, Any]]
    customer_context: Optional[Dict[str, Any]]

    # Survey state
    all_questions: List[Dict[str, Any]]  # All generated questions
    current_question_index: int
    answers: List[Dict[str, Any]]  # User's answers
    total_questions_asked: int

    # Conversation history for LLM
    conversation_history: Annotated[Sequence[Dict[str, str]], operator.add]

    # Review generation
    generated_reviews: Optional[List[Dict[str, Any]]]
    selected_review: Optional[Dict[str, Any]]

    # Control flow
    next_action: str  # 'ask_question', 'generate_followup', 'generate_review', 'end'


# ============================================================================
# AGENT DEFINITION
# ============================================================================


class SurveyAndReviewAgent:
    """Agent 3: Stateful survey generation and review agent"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key,
        )
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(SurveyState)

        # Add nodes
        workflow.add_node("fetch_contexts", self._fetch_contexts)
        workflow.add_node("generate_initial_questions", self._generate_initial_questions)
        workflow.add_node("present_question", self._present_question)
        workflow.add_node("generate_reviews", self._generate_review_options)

        # Define edges
        workflow.set_entry_point("fetch_contexts")
        workflow.add_edge("fetch_contexts", "generate_initial_questions")
        workflow.add_edge("generate_initial_questions", "present_question")

        # Conditional routing after question presentation
        workflow.add_conditional_edges(
            "present_question",
            self._route_after_question,
            {
                "wait_for_answer": END,  # Return to user, wait for answer
                "generate_reviews": "generate_reviews",
            },
        )

        workflow.add_edge("generate_reviews", END)

        return workflow.compile()

    # ========================================================================
    # NODE FUNCTIONS
    # ========================================================================

    def _fetch_contexts(self, state: SurveyState) -> Dict[str, Any]:
        """
        Node 1: Invoke Agent 1 and Agent 2 in parallel
        Fetch product and customer contexts
        """
        # Get form data from session metadata (stored in session_context)
        session = db.get_survey_session(state["session_id"])
        session_context = session.get("session_context", {})
        form_data = session_context.get("form_data", {}) if isinstance(session_context, dict) else {}

        # Invoke Agent 1: Product Context
        # Use item_id from state instead of product_url from form_data
        product_context = product_context_agent.generate_context(
            item_id=state["item_id"],
            has_reviews=form_data.get("hasReviews") == "yes",
            form_data=form_data,
        )

        # Invoke Agent 2: Customer Context
        # Use item_id from state instead of product_url from form_data
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
        """
        Node 2: Generate initial 3 questions based on contexts
        """
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
- Set allow_multiple=false for mutually exclusive questions (e.g., "How satisfied are you?", "Would you recommend?")""",
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
            # No more questions, move to review generation
            return {"next_action": "generate_review"}

        current_q = state["all_questions"][state["current_question_index"]]

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
            "next_action": "wait_for_answer",
        }

    def _process_answer(self, state: SurveyState, answer) -> Dict[str, Any]:
        """
        Node 4: Process user's answer
        Update state and determine next action

        Args:
            answer: Can be a string (single choice) or list of strings (multi-select)
        """
        current_q = state["all_questions"][state["current_question_index"]]

        # Convert answer to string for storage in conversation history
        answer_text = ", ".join(answer) if isinstance(answer, list) else answer

        # Record answer
        answer_record = {
            "question_index": state["current_question_index"],
            "question": current_q["question_text"],
            "answer": answer_text,
            "timestamp": datetime.utcnow().isoformat(),
        }

        updated_answers = list(state["answers"]) + [answer_record]

        # Add to conversation history (use text version)
        conversation_update = list(state.get("conversation_history", [])) + [
            {"role": "assistant", "content": current_q["question_text"]},
            {"role": "user", "content": answer_text},
        ]

        # Move to next question
        next_index = state["current_question_index"] + 1

        return {
            "answers": updated_answers,
            "current_question_index": next_index,
            "conversation_history": conversation_update,
        }

    def _generate_followup_questions(self, state: SurveyState) -> Dict[str, Any]:
        """
        Node 5: Generate follow-up questions based on answers so far
        Adaptive questioning based on conversation history
        """
        # Check if we've reached max questions
        if state["total_questions_asked"] >= settings.max_survey_questions:
            return {"next_action": "complete_survey"}

        parser = PydanticOutputParser(pydantic_object=SurveyQuestionnaire)

        # Prepare conversation summary
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
- Set allow_multiple=false for mutually exclusive questions""",
                ),
                (
                    "human",
                    """Product Context:
{product_context}

Customer Context:
{customer_context}

Previous Q&A:
{previous_qa}

Generate {num_questions} follow-up questions that build on the conversation.

{format_instructions}""",
                ),
            ]
        )

        chain = prompt | self.llm | parser

        # Generate 2 follow-up questions
        num_followup = min(2, settings.max_survey_questions - state["total_questions_asked"])

        questionnaire = chain.invoke(
            {
                "product_context": json.dumps(state["product_context"], indent=2),
                "customer_context": json.dumps(state["customer_context"], indent=2),
                "previous_qa": answers_summary,
                "num_questions": num_followup,
                "format_instructions": parser.get_format_instructions(),
            }
        )

        # Add new questions to the list and validate
        new_questions = []
        for q in questionnaire.questions:
            q_dict = q.dict()
            # Ensure question has at least 2 options
            if not q_dict.get("options") or len(q_dict["options"]) < 2:
                print(f"WARNING: Followup question has insufficient options, skipping: {q_dict.get('question_text')}")
                continue
            new_questions.append(q_dict)

        updated_questions = list(state["all_questions"]) + new_questions

        return {
            "all_questions": updated_questions,
            "next_action": "ask_question",
        }

    def _generate_review_options(self, state: SurveyState) -> Dict[str, Any]:
        """
        Node 6: Generate natural language review options
        Creates 3 review options for user to select from
        """
        parser = PydanticOutputParser(pydantic_object=ReviewOptions)

        # Prepare survey summary
        qa_summary = "\n".join(
            [
                f"Q: {ans['question']}\nA: {ans['answer']}\n"
                for ans in state["answers"]
            ]
        )

        # Get product info
        session = db.get_survey_session(state["session_id"])
        product = db.get_product_by_id(state["item_id"])

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert at writing authentic product reviews.
Based on the survey responses, generate {num_options} different natural language review options.

Guidelines:
- Reviews should sound authentic and personal
- Reflect the user's actual survey responses
- Vary in tone (enthusiastic, balanced, critical)
- Vary in length (short, medium, detailed)
- Include specific details from their answers
- Assign appropriate star ratings (1-5) based on sentiment
- Write like a real customer, not an AI""",
                ),
                (
                    "human",
                    """Product: {product_title}

Survey Responses:
{survey_qa}

Product Context:
{product_context}

Customer Profile:
{customer_context}

Generate {num_options} authentic review options that reflect the user's survey responses.
Create variety: one enthusiastic, one balanced, one more critical/honest.

{format_instructions}""",
                ),
            ]
        )

        chain = prompt | self.llm | parser

        review_options = chain.invoke(
            {
                "product_title": product.get("title", "this product"),
                "survey_qa": qa_summary,
                "product_context": json.dumps(state["product_context"], indent=2),
                "customer_context": json.dumps(state["customer_context"], indent=2),
                "num_options": settings.review_options_count,
                "format_instructions": parser.get_format_instructions(),
            }
        )

        return {
            "generated_reviews": [opt.dict() for opt in review_options.options],
            "next_action": "present_reviews",
        }

    def _save_selected_review(
        self, state: SurveyState, selected_review: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Node 7: Save user's selected review to database
        """
        # Save review to database
        review_id = db.save_generated_review(
            user_id=state["user_id"],
            item_id=state["item_id"],
            review_text=selected_review["review_text"],
            rating=selected_review["rating"],
            sentiment_label=selected_review["sentiment"],
            metadata={
                "session_id": state["session_id"],
                "tone": selected_review.get("tone", "neutral"),
                "generated_by": "survey_agent",
            },
        )

        # Update session as completed
        db.update_survey_session(
            session_id=state["session_id"],
            conversation_history=list(state["conversation_history"]),
            state="completed",
            metadata={"review_id": review_id},
        )

        return {
            "selected_review": selected_review,
            "next_action": "end",
        }

    # ========================================================================
    # ROUTING FUNCTIONS
    # ========================================================================

    def _route_after_question(self, state: SurveyState) -> str:
        """Determine next step after presenting a question"""
        if state["next_action"] == "generate_review":
            return "generate_reviews"
        return "wait_for_answer"

    def _route_after_answer(self, state: SurveyState) -> str:
        """Determine next step after processing an answer"""
        total_asked = state["total_questions_asked"]
        total_available = len(state["all_questions"])

        # Check if we should end survey
        if total_asked >= settings.max_survey_questions:
            return "complete_survey"

        if total_asked >= settings.min_survey_questions:
            # Can optionally end or continue
            # For now, generate followup every 3 questions
            if total_asked % 3 == 0 and total_asked < settings.max_survey_questions:
                return "generate_followup"
            elif state["current_question_index"] >= total_available:
                return "complete_survey"

        # Continue with next question if available
        if state["current_question_index"] < total_available:
            return "ask_next"
        else:
            return "generate_followup"

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def start_survey(self, user_id: str, item_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a new survey session
        Returns the first question
        """
        # Create survey session in database
        session_id = db.create_survey_session(
            user_id=user_id,
            item_id=item_id,
            metadata={"form_data": form_data},
        )

        # Initialize state
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
            "conversation_history": [],
            "generated_reviews": None,
            "selected_review": None,
            "next_action": "fetch_contexts",
        }

        # Run graph until first question
        result = self.graph.invoke(initial_state)

        # Save state to database for later retrieval
        db.update_survey_session(
            session_id=session_id,
            conversation_history=result.get("conversation_history", []),
            state="active",
            metadata={"form_data": form_data, "current_state": result},
        )

        # Return first question
        current_q = result["all_questions"][result["current_question_index"]]

        return {
            "session_id": session_id,
            "question": current_q,
            "question_number": result["current_question_index"] + 1,
            "total_questions": len(result["all_questions"]),
        }

    def submit_answer(
        self, session_id: str, answer: str
    ) -> Dict[str, Any]:
        """
        Submit answer and get next question
        """
        # Load session state from database
        session = db.get_survey_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Reconstruct state from database
        # (In production, you'd use a proper state store like Redis)
        # For now, we'll store state in session_context

        session_context = session.get("session_context", {})
        current_state = session_context.get("current_state", {})

        # Process answer (returns partial update)
        state_update = self._process_answer(current_state, answer)

        # Merge update with current state
        updated_state = {**current_state, **state_update}

        # Determine next action and execute
        next_route = self._route_after_answer(updated_state)

        if next_route == "complete_survey":
            # Generate review options (returns partial update)
            review_update = self._generate_review_options(updated_state)
            # Merge with current state
            final_state = {**updated_state, **review_update}

            # Save final state
            db.update_survey_session(
                session_id=session_id,
                conversation_history=final_state.get("conversation_history", []),
                state="completed",
                metadata={"current_state": final_state},
            )

            return {
                "session_id": session_id,
                "status": "completed",
                "review_options": final_state["generated_reviews"],
            }
        elif next_route == "generate_followup":
            # Generate followup questions (returns partial update)
            followup_update = self._generate_followup_questions(updated_state)
            updated_state = {**updated_state, **followup_update}

            # Present next question (returns partial update)
            present_update = self._present_question(updated_state)
            updated_state = {**updated_state, **present_update}

        # Save updated state
        db.update_survey_session(
            session_id=session_id,
            conversation_history=updated_state.get("conversation_history", []),
            state="active",
            metadata={"current_state": updated_state},
        )

        # Get next question
        current_q = updated_state["all_questions"][updated_state["current_question_index"]]

        return {
            "session_id": session_id,
            "question": current_q,
            "question_number": updated_state["current_question_index"] + 1,
            "total_questions": len(updated_state["all_questions"]),
        }

    def submit_review(
        self, session_id: str, selected_review_index: int
    ) -> Dict[str, Any]:
        """
        Save selected review and complete survey
        """
        session = db.get_survey_session(session_id)
        session_context = session.get("session_context", {})
        current_state = session_context.get("current_state", {})

        selected_review = current_state["generated_reviews"][selected_review_index]

        result = self._save_selected_review(current_state, selected_review)

        return {
            "session_id": session_id,
            "status": "review_saved",
            "review": selected_review,
        }

    def edit_answer(
        self, session_id: str, question_number: int, new_answer: str
    ) -> Dict[str, Any]:
        """
        Edit a previous answer and branch from that question

        This implements LangGraph-style branching:
        1. Load current state
        2. Revert to the specified question
        3. Update the answer
        4. Discard all subsequent answers
        5. Return to continue from that point
        """
        # Load session state
        session = db.get_survey_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session_context = session.get("session_context", {})
        current_state = session_context.get("current_state", {})

        # Convert question_number (1-indexed) to question_index (0-indexed)
        question_index = question_number - 1

        if question_index < 0 or question_index >= len(current_state.get("answers", [])):
            raise ValueError(f"Invalid question number: {question_number}")

        # Branch: Keep only answers up to (but not including) the edited question
        branched_answers = current_state["answers"][:question_index]

        # Update the answer at this position
        current_q = current_state["all_questions"][question_index]
        new_answer_record = {
            "question_index": question_index,
            "question": current_q["question_text"],
            "answer": new_answer,
            "timestamp": datetime.utcnow().isoformat(),
        }
        branched_answers.append(new_answer_record)

        # Rebuild conversation history up to this point
        branched_conversation = []
        for ans in branched_answers:
            branched_conversation.extend([
                {"role": "assistant", "content": ans["question"]},
                {"role": "user", "content": ans["answer"]},
            ])

        # Create branched state
        branched_state = {
            **current_state,
            "answers": branched_answers,
            "conversation_history": branched_conversation,
            "current_question_index": question_index + 1,  # Move to next question
            "total_questions_asked": len(branched_answers),
            "generated_reviews": None,  # Clear any generated reviews
        }

        # Save branched state
        db.update_survey_session(
            session_id=session_id,
            conversation_history=branched_conversation,
            state="active",
            metadata={"current_state": branched_state},
        )

        # Return next question (same as submit_answer flow)
        if branched_state["current_question_index"] >= len(branched_state["all_questions"]):
            # Reached end, need to complete survey
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


# Global agent instance
survey_agent = SurveyAndReviewAgent()
