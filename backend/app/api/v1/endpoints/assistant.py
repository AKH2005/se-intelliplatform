"""Intelli Assistant Conversational & Engineering Action API Endpoints."""

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import (
    get_assistant_context_builder,
    get_assistant_reasoning_service,
    get_db,
    get_engineering_action_service,
)
from app.core.exceptions import NotFoundError
from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.project import Project
from app.schemas.assistant import (
    ActionResult,
    ActionStatus,
    AssistantConversationListResponse,
    AssistantConversationResponse,
    AssistantMessageResponse,
    AssistantRole,
    ConfirmActionRequest,
    DirectExecuteActionRequest,
    SendMessageRequest,
)
from app.services.assistant_context_builder import AssistantContextBuilder
from app.services.assistant_reasoning_service import AssistantReasoningService
from app.services.engineering_action_service import EngineeringActionService

router = APIRouter()


async def _resolve_project(project_id: uuid.UUID, session: AsyncSession) -> Project:
    """Verify that project exists or raise NotFoundError (404)."""
    stmt = select(Project).where(Project.id == project_id)
    res = await session.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", str(project_id))
    return project


@router.post(
    "/messages",
    response_model=AssistantMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send message to Intelli Assistant and trigger reasoning/actions",
    description="Submits a developer prompt, evaluates bounded context, infers structured candidate action, and executes or gates action with confirmation.",
)
async def send_message(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    request: SendMessageRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    context_builder: Annotated[AssistantContextBuilder, Depends(get_assistant_context_builder)],
    reasoning_service: Annotated[AssistantReasoningService, Depends(get_assistant_reasoning_service)],
    action_service: Annotated[EngineeringActionService, Depends(get_engineering_action_service)],
) -> AssistantMessageResponse:
    """Process a user conversational turn with the Intelli Assistant."""
    await _resolve_project(project_id, session)

    # 1. Resolve or initialize conversation
    if request.conversation_id:
        stmt = select(AssistantConversation).where(
            AssistantConversation.id == request.conversation_id,
            AssistantConversation.project_id == project_id,
        )
        res = await session.execute(stmt)
        conversation = res.scalar_one_or_none()
        if not conversation:
            raise NotFoundError("AssistantConversation", str(request.conversation_id))
    else:
        title = request.content.strip()[:60]
        if len(request.content.strip()) > 60:
            title += "..."
        conversation = AssistantConversation(
            project_id=project_id,
            title=title or "New Conversation",
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)

    # 2. Persist incoming user message
    user_msg = AssistantMessage(
        conversation_id=conversation.id,
        role=AssistantRole.USER.value,
        content=request.content,
    )
    session.add(user_msg)
    await session.commit()
    await session.refresh(user_msg)

    # 3. Retrieve recent history for conversational continuity
    stmt_history = (
        select(AssistantMessage)
        .where(AssistantMessage.conversation_id == conversation.id)
        .order_by(AssistantMessage.created_at.asc())
    )
    history_res = await session.execute(stmt_history)
    all_msgs = history_res.scalars().all()
    history_payload = [{"role": m.role, "content": m.content} for m in all_msgs[:-1]]

    # 4. Fast-path intent detection for natural conversational development requests
    dev_intent = reasoning_service.classify_development_intent(request.content)
    action_result = None
    action_id = None
    action_status = None
    target_id = None
    referenced_entity_type = None
    referenced_entity_id = None
    reply_content = None

    if dev_intent:
        if dev_intent.get("is_destructive"):
            action_id = "FAST_PATH_UPDATE"
            action_status = ActionStatus.PENDING_CONFIRMATION
            reply_content = (
                f"{dev_intent['acknowledgment']}\n\n"
                f"Proposed Changes:\n" + "\n".join(f"• {item}" for item in dev_intent["plan_items"]) + "\n\n"
                f"Because this is a potentially destructive change, confirmation is required before proceeding."
            )
            action_result = ActionResult(
                action_id="FAST_PATH_UPDATE",
                status=ActionStatus.PENDING_CONFIRMATION,
                summary=f"Confirmation required: {dev_intent['summary']}",
                requires_confirmation=True,
                confirmation_prompt=f"Confirm deletion and removal of {dev_intent['summary']}.",
                confirmation_token=f"anti-replay-{uuid.uuid4()}",
                data={"is_destructive": True, "feature": dev_intent["intent"]},
            )
        else:
            # Safe development change: execute via preview runtime manager directly
            from app.runtime.preview_runtime_manager import preview_runtime_manager

            ok, apply_msg, details = await preview_runtime_manager.apply_development_change(
                project_id=str(project_id),
                feature_type=dev_intent["intent"],
            )

            if ok:
                action_id = "FAST_PATH_UPDATE"
                action_status = ActionStatus.SUCCESS
                reply_content = (
                    f"{dev_intent['acknowledgment']}\n\n"
                    f"Plan:\n" + "\n".join(f"• {item}" for item in dev_intent["plan_items"]) + "\n\n"
                    f"● Applying changes...\n"
                    f"✓ Application runtime updated on port 8001.\n"
                    f"✓ {dev_intent['completed_summary']}\n\n"
                    f"{dev_intent['conclusion']}"
                )
                action_result = ActionResult(
                    action_id="FAST_PATH_UPDATE",
                    status=ActionStatus.SUCCESS,
                    summary=f"Application runtime updated with {dev_intent['summary']} on port 8001.",
                    data={
                        "runtime_updated": True,
                        "feature": dev_intent["intent"],
                        "port": 8001,
                        "details": details,
                    },
                )
            else:
                action_id = "FAST_PATH_UPDATE"
                action_status = ActionStatus.FAILED
                reply_content = (
                    f"I couldn't complete that change.\n\n"
                    f"{dev_intent['summary']} was requested, but the application runtime failed verification: {apply_msg}\n\n"
                    f"Actions:\n"
                    f"[Ask AI to Fix]\n"
                    f"[View Details]"
                )
                action_result = ActionResult(
                    action_id="FAST_PATH_UPDATE",
                    status=ActionStatus.FAILED,
                    summary=f"Application runtime update failed: {apply_msg}",
                    errors=[apply_msg],
                    data={"runtime_updated": False, "port": 8001},
                )

    if reply_content is None:
        # Standard workflow: context snapshot -> LLM structured reasoning -> engineering action
        context_snapshot = await context_builder.build_context(project_id)
        reasoning_output = await reasoning_service.generate_response(
            user_message=request.content,
            context=context_snapshot,
            history_messages=history_payload,
        )
        reply_content = reasoning_output.message
        referenced_entity_type = reasoning_output.referenced_entity_type
        referenced_entity_id = reasoning_output.referenced_entity_id

        if reasoning_output.suggested_action:
            candidate = reasoning_output.suggested_action
            action_id = candidate.action_id
            target_id = candidate.target_id

            action_result = await action_service.execute_action(
                project_id=project_id,
                action_id=candidate.action_id,
                parameters=candidate.parameters,
                target_id=candidate.target_id,
                conversation_id=conversation.id,
                message_id=None,
            )
            action_status = action_result.status

    # 5. Persist Assistant Reply
    assistant_msg = AssistantMessage(
        conversation_id=conversation.id,
        role=AssistantRole.ASSISTANT.value,
        content=reply_content,
        action_id=action_id,
        action_status=action_status.value if action_status else None,
        target_id=str(target_id) if target_id else None,
        structured_payload=action_result.model_dump(mode="json") if action_result else None,
        referenced_entity_type=referenced_entity_type,
        referenced_entity_id=referenced_entity_id,
    )
    session.add(assistant_msg)
    await session.commit()
    await session.refresh(assistant_msg)

    return AssistantMessageResponse(
        message_id=assistant_msg.id,
        conversation_id=conversation.id,
        role=AssistantRole.ASSISTANT,
        content=assistant_msg.content,
        action_id=action_id,
        action_status=action_status,
        action_result=action_result,
        referenced_entity_type=assistant_msg.referenced_entity_type,
        referenced_entity_id=assistant_msg.referenced_entity_id,
        created_at=assistant_msg.created_at,
    )


@router.get(
    "/conversations",
    response_model=AssistantConversationListResponse,
    summary="List assistant conversation threads for a project",
)
async def list_conversations(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AssistantConversationListResponse:
    """Retrieve all conversations for the given project ordered by updated timestamp."""
    await _resolve_project(project_id, session)

    stmt = (
        select(AssistantConversation)
        .where(AssistantConversation.project_id == project_id)
        .options(selectinload(AssistantConversation.messages))
        .order_by(AssistantConversation.updated_at.desc())
    )
    res = await session.execute(stmt)
    conversations = res.scalars().all()

    items = []
    for conv in conversations:
        msgs = [
            AssistantMessageResponse(
                message_id=m.id,
                conversation_id=m.conversation_id,
                role=AssistantRole(m.role),
                content=m.content,
                action_id=m.action_id,
                action_status=m.action_status,  # type: ignore
                action_result=ActionResult.model_validate(m.structured_payload) if m.structured_payload else None,
                referenced_entity_type=m.referenced_entity_type,
                referenced_entity_id=m.referenced_entity_id,
                created_at=m.created_at,
            )
            for m in conv.messages
        ]
        items.append(
            AssistantConversationResponse(
                conversation_id=conv.id,
                project_id=conv.project_id,
                title=conv.title,
                messages=msgs,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
        )

    return AssistantConversationListResponse(
        items=items,
        total=len(items),
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=AssistantConversationResponse,
    summary="Get single assistant conversation thread with all messages",
)
async def get_conversation(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    conversation_id: Annotated[uuid.UUID, Path(description="Conversation UUID")],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AssistantConversationResponse:
    """Retrieve full conversation history for a specific thread."""
    await _resolve_project(project_id, session)

    stmt = (
        select(AssistantConversation)
        .where(
            AssistantConversation.id == conversation_id,
            AssistantConversation.project_id == project_id,
        )
        .options(selectinload(AssistantConversation.messages))
    )
    res = await session.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise NotFoundError("AssistantConversation", str(conversation_id))

    msgs = [
        AssistantMessageResponse(
            message_id=m.id,
            conversation_id=m.conversation_id,
            role=AssistantRole(m.role),
            content=m.content,
            action_id=m.action_id,
            action_status=m.action_status,  # type: ignore
            action_result=ActionResult.model_validate(m.structured_payload) if m.structured_payload else None,
            referenced_entity_type=m.referenced_entity_type,
            referenced_entity_id=m.referenced_entity_id,
            created_at=m.created_at,
        )
        for m in conv.messages
    ]

    return AssistantConversationResponse(
        conversation_id=conv.id,
        project_id=conv.project_id,
        title=conv.title,
        messages=msgs,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )


@router.post(
    "/actions/confirm",
    response_model=ActionResult,
    summary="Redeem single-use anti-replay confirmation token for pending mutating action",
)
async def confirm_action(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    request: ConfirmActionRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    action_service: Annotated[EngineeringActionService, Depends(get_engineering_action_service)],
) -> ActionResult:
    """Confirm and execute a pending mutating engineering action."""
    await _resolve_project(project_id, session)
    return await action_service.confirm_action(
        project_id=project_id,
        confirmation_token=request.confirmation_token,
    )


@router.post(
    "/actions/execute",
    response_model=ActionResult,
    summary="Directly dispatch an action from the authoritative 26-action catalog",
)
async def execute_action_direct(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    request: DirectExecuteActionRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    action_service: Annotated[EngineeringActionService, Depends(get_engineering_action_service)],
) -> ActionResult:
    """Directly trigger or gate an action without requiring a natural-language turn."""
    await _resolve_project(project_id, session)
    return await action_service.execute_action(
        project_id=project_id,
        action_id=request.action_id,
        parameters=request.parameters,
        target_id=request.target_id,
        conversation_id=request.conversation_id,
    )
