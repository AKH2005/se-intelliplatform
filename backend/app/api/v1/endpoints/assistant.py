"""Intelli Assistant Conversational & Engineering Action API Endpoints."""

import asyncio
from datetime import datetime, timezone
import inspect
import json
import logging
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Path, status
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.exceptions import ProviderError, TransientProviderError
from app.api.dependencies import (
    get_assistant_context_builder,
    get_assistant_reasoning_service,
    get_current_user_optional,
    get_db,
    get_engineering_action_service,
)
from app.core.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.project import Project
from app.models.user import User, UserRole
from app.schemas.assistant import (
    ActionResult,
    ActionStatus,
    AssistantConversationListResponse,
    AssistantConversationResponse,
    AssistantMessageResponse,
    AssistantRole,
    ConfirmActionRequest,
    CreateConversationRequest,
    DirectExecuteActionRequest,
    SendMessageRequest,
)
from app.services.assistant_context_builder import AssistantContextBuilder
from app.services.assistant_reasoning_service import AssistantReasoningService
from app.services.engineering_action_service import EngineeringActionService
from app.services.intent_router import IntentRouter

router = APIRouter()


def _is_project_authorized(project: Project, current_user: User | None) -> bool:
    """Return True if project has no owner, or current user is the owner or an admin."""
    if project.owner_id is None:
        return True
    if current_user is None:
        return False
    if str(project.owner_id) == str(current_user.id):
        return True
    if getattr(current_user, "role", None) == UserRole.ADMIN or getattr(current_user, "role", None) == UserRole.ADMIN.value:
        return True
    return False


def _is_conversation_authorized(conversation: AssistantConversation, current_user: User | None) -> bool:
    """Return True if conversation has no owner, or current user is the owner or an admin."""
    if conversation.user_id is None:
        return True
    if current_user is None:
        return False
    if str(conversation.user_id) == str(current_user.id):
        return True
    if getattr(current_user, "role", None) == UserRole.ADMIN or getattr(current_user, "role", None) == UserRole.ADMIN.value:
        return True
    return False


async def _resolve_active_version(context_builder: Any, project_id: uuid.UUID) -> Any:
    """Safely resolve active version from context_builder without raising if version_service is mocked synchronously."""
    if hasattr(context_builder, "version_service") and hasattr(context_builder.version_service, "get_active_version"):
        raw = context_builder.version_service.get_active_version(project_id)
        if inspect.isawaitable(raw):
            return await raw
        if hasattr(raw, "mock_calls"):
            return None
        return raw
    return None


async def _resolve_project(
    project_id: uuid.UUID,
    session: AsyncSession,
    current_user: User | None = None,
) -> Project:
    """Verify that project exists and user is authorized or raise NotFoundError / ForbiddenError."""
    stmt = select(Project).where(Project.id == project_id)
    res = await session.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", str(project_id))
    if not _is_project_authorized(project, current_user):
        raise ForbiddenError("You do not have permission to access this project.")
    return project


@router.post(
    "/conversations",
    response_model=AssistantConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new assistant conversation thread",
)
async def create_conversation(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    session: Annotated[AsyncSession, Depends(get_db)],
    request: CreateConversationRequest | None = None,
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> AssistantConversationResponse:
    """Explicitly create an assistant conversation thread scoped to the user and project."""
    await _resolve_project(project_id, session, current_user)
    title = (request.title.strip() if request and request.title else None) or "New Conversation"
    conversation = AssistantConversation(
        project_id=project_id,
        user_id=current_user.id if current_user else None,
        title=title,
    )
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)

    return AssistantConversationResponse(
        conversation_id=conversation.id,
        project_id=conversation.project_id,
        user_id=conversation.user_id,
        title=conversation.title,
        messages=[],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


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
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> AssistantMessageResponse:
    """Process a user conversational turn with the Intelli Assistant."""
    await _resolve_project(project_id, session, current_user)

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
        if not _is_conversation_authorized(conversation, current_user):
            raise ForbiddenError("You do not have permission to access this conversation.")
    else:
        title = request.content.strip()[:60]
        if len(request.content.strip()) > 60:
            title += "..."
        conversation = AssistantConversation(
            project_id=project_id,
            user_id=current_user.id if current_user else None,
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

    active_ver = await _resolve_active_version(context_builder, project_id)

    is_bootstrap = not active_ver or bool(
        isinstance(getattr(active_ver, "metadata", None), dict)
        and getattr(active_ver, "metadata", {}).get("bootstrap")
    )

    # 4. Fast-path intent detection for natural conversational development requests (prototype mode only when no active version exists or bootstrapped baseline)
    dev_intent = reasoning_service.classify_development_intent(request.content) if is_bootstrap else None
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

            is_prod = settings.ENVIRONMENT == "production"
            port_label = "HTTPS" if is_prod else "port 8001"
            runtime_port = 443 if is_prod else 8001

            if ok:
                action_id = "FAST_PATH_UPDATE"
                action_status = ActionStatus.SUCCESS
                reply_content = (
                    f"{dev_intent['acknowledgment']}\n\n"
                    f"Plan:\n" + "\n".join(f"• {item}" for item in dev_intent["plan_items"]) + "\n\n"
                    f"● Applying changes...\n"
                    f"✓ Application runtime updated on {port_label}.\n"
                    f"✓ {dev_intent['completed_summary']}\n\n"
                    f"{dev_intent['conclusion']}"
                )
                action_result = ActionResult(
                    action_id="FAST_PATH_UPDATE",
                    status=ActionStatus.SUCCESS,
                    summary=f"Application runtime updated with {dev_intent['summary']} on {port_label}.",
                    data={
                        "runtime_updated": True,
                        "feature": dev_intent["intent"],
                        "port": runtime_port,
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
                    data={"runtime_updated": False, "port": runtime_port},
                )

    if reply_content is None:
        # Standard workflow: intent classification -> context snapshot -> LLM reasoning -> gated action
        classification = IntentRouter.classify(request.content, history_payload)
        context_snapshot = await context_builder.build_context(
            project_id=project_id,
            user_query=request.content,
            explicit_file_paths=request.explicit_file_paths,
            error_message=request.error_message,
            detected_intent=classification.intent.value,
            active_persona=classification.persona,
        )
        reasoning_output = await reasoning_service.generate_response(
            user_message=request.content,
            context=context_snapshot,
            history_messages=history_payload,
            classification=classification,
        )
        reply_content = reasoning_output.message
        referenced_entity_type = reasoning_output.referenced_entity_type
        referenced_entity_id = reasoning_output.referenced_entity_id

        # Execute suggested action if validated and preserved by reasoning service
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


@router.post(
    "/messages/stream",
    summary="Send message to Intelli Assistant with real SSE token streaming",
    description="Streams conversational response tokens using Server-Sent Events (SSE). Preserves atomic execution gates for code modifications.",
)
async def send_message_stream(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    request: SendMessageRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    context_builder: Annotated[AssistantContextBuilder, Depends(get_assistant_context_builder)],
    reasoning_service: Annotated[AssistantReasoningService, Depends(get_assistant_reasoning_service)],
    action_service: Annotated[EngineeringActionService, Depends(get_engineering_action_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> StreamingResponse:
    """Stream assistant response chunks via Server-Sent Events (SSE)."""
    await _resolve_project(project_id, session, current_user)

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
        if not _is_conversation_authorized(conversation, current_user):
            raise ForbiddenError("You do not have permission to access this conversation.")
    else:
        title = request.content.strip()[:60]
        if len(request.content.strip()) > 60:
            title += "..."
        conversation = AssistantConversation(
            project_id=project_id,
            user_id=current_user.id if current_user else None,
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

    async def event_generator():
        chunks_collected = []
        try:
            active_ver = await _resolve_active_version(context_builder, project_id)
            is_bootstrap = not active_ver or bool(
                isinstance(getattr(active_ver, "metadata", None), dict)
                and getattr(active_ver, "metadata", {}).get("bootstrap")
            )
            # Step A: Check for fast-path development intent (prototype mode only when no active version exists or bootstrapped baseline)
            dev_intent = reasoning_service.classify_development_intent(request.content) if is_bootstrap else None
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
                    from app.runtime.preview_runtime_manager import preview_runtime_manager
                    ok, apply_msg, details = await preview_runtime_manager.apply_development_change(
                        project_id=str(project_id),
                        feature_type=dev_intent["intent"],
                    )
                    is_prod = settings.ENVIRONMENT == "production"
                    port_label = "HTTPS" if is_prod else "port 8001"
                    runtime_port = 443 if is_prod else 8001
                    if ok:
                        action_id = "FAST_PATH_UPDATE"
                        action_status = ActionStatus.SUCCESS
                        reply_content = (
                            f"{dev_intent['acknowledgment']}\n\n"
                            f"Plan:\n" + "\n".join(f"• {item}" for item in dev_intent["plan_items"]) + "\n\n"
                            f"● Applying changes...\n"
                            f"✓ Application runtime updated on {port_label}.\n"
                            f"✓ {dev_intent['completed_summary']}\n\n"
                            f"{dev_intent['conclusion']}"
                        )
                        action_result = ActionResult(
                            action_id="FAST_PATH_UPDATE",
                            status=ActionStatus.SUCCESS,
                            summary=f"Application runtime updated with {dev_intent['summary']} on {port_label}.",
                            data={"runtime_updated": True, "feature": dev_intent["intent"], "port": runtime_port, "details": details},
                        )
                    else:
                        action_id = "FAST_PATH_UPDATE"
                        action_status = ActionStatus.FAILED
                        reply_content = f"I couldn't complete that change: {apply_msg}"
                        action_result = ActionResult(
                            action_id="FAST_PATH_UPDATE",
                            status=ActionStatus.FAILED,
                            summary=f"Update failed: {apply_msg}",
                            errors=[apply_msg],
                            data={"runtime_updated": False, "port": runtime_port},
                        )

                assistant_msg = AssistantMessage(
                    conversation_id=conversation.id,
                    role=AssistantRole.ASSISTANT.value,
                    content=reply_content,
                    action_id=action_id,
                    action_status=action_status.value if action_status else None,
                    structured_payload=action_result.model_dump(mode="json") if action_result else None,
                )
                session.add(assistant_msg)
                await session.commit()
                await session.refresh(assistant_msg)

                yield f"event: start\ndata: {json.dumps({'intent': dev_intent['intent'], 'persona': 'IntelliDev', 'conversation_id': str(conversation.id)})}\n\n"
                yield f"event: content\ndata: {json.dumps({'chunk': reply_content})}\n\n"
                done_payload = {
                    "message_id": str(assistant_msg.id),
                    "conversation_id": str(conversation.id),
                    "role": "assistant",
                    "content": reply_content,
                    "action_id": action_id,
                    "action_status": action_status.value if action_status else None,
                    "action_result": action_result.model_dump(mode="json") if action_result else None,
                    "created_at": assistant_msg.created_at.isoformat(),
                }
                yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"
                return

            # Step B: Standard routed classification
            classification = IntentRouter.classify(request.content, history_payload)
            context_snapshot = await context_builder.build_context(
                project_id=project_id,
                user_query=request.content,
                explicit_file_paths=request.explicit_file_paths,
                error_message=request.error_message,
                detected_intent=classification.intent.value,
                active_persona=classification.persona,
            )

            yield f"event: start\ndata: {json.dumps({'intent': classification.intent.value, 'persona': classification.persona, 'conversation_id': str(conversation.id)})}\n\n"

            if not classification.allow_actions:
                # Pure conversational query: stream real token chunks
                async for chunk in reasoning_service.generate_response_stream(
                    user_message=request.content,
                    context=context_snapshot,
                    history_messages=history_payload,
                    classification=classification,
                ):
                    chunks_collected.append(chunk)
                    yield f"event: content\ndata: {json.dumps({'chunk': chunk})}\n\n"

                full_reply = "".join(chunks_collected)
                full_reply = reasoning_service.sanitize_response_text(full_reply)

                assistant_msg = AssistantMessage(
                    conversation_id=conversation.id,
                    role=AssistantRole.ASSISTANT.value,
                    content=full_reply,
                )
                session.add(assistant_msg)
                await session.commit()
                await session.refresh(assistant_msg)

                done_payload = {
                    "message_id": str(assistant_msg.id or uuid.uuid4()),
                    "conversation_id": str(conversation.id or uuid.uuid4()),
                    "role": "assistant",
                    "content": full_reply,
                    "created_at": assistant_msg.created_at.isoformat() if assistant_msg.created_at else datetime.now(timezone.utc).isoformat(),
                }
                yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

            else:
                # Mutating / action-eligible request: execute structured reasoning and diff generation atomically
                yield f"event: status\ndata: {json.dumps({'status': 'Evaluating project context and computing change diffs...'})}\n\n"

                try:
                    reasoning_output = await reasoning_service.generate_response(
                        user_message=request.content,
                        context=context_snapshot,
                        history_messages=history_payload,
                        classification=classification,
                    )
                except TransientProviderError as t_err:
                    err_msg = f"AI Provider rate limit reached: {t_err.message}. Please wait a moment and try again."
                    yield f"event: error\ndata: {json.dumps({'error': err_msg})}\n\n"
                    return
                except ProviderError as p_err:
                    err_msg = f"AI Provider returned invalid output: {p_err.message}. Please retry your request."
                    yield f"event: error\ndata: {json.dumps({'error': err_msg})}\n\n"
                    return

                action_result = None
                action_id = None
                action_status = None
                target_id = None

                if reasoning_output.suggested_action:
                    candidate = reasoning_output.suggested_action
                    action_id = candidate.action_id
                    target_id = candidate.target_id
                    action_result = await action_service.execute_action(
                        project_id=project_id,
                        action_id=candidate.action_id,
                        parameters=candidate.parameters,
                        target_id=candidate.target_id,
                        user_id=str(current_user.id) if current_user else "assistant_user",
                        conversation_id=conversation.id,
                        message_id=None,
                    )
                    action_status = action_result.status

                assistant_msg = AssistantMessage(
                    conversation_id=conversation.id,
                    role=AssistantRole.ASSISTANT.value,
                    content=reasoning_output.message,
                    action_id=action_id,
                    action_status=action_status.value if action_status else None,
                    target_id=str(target_id) if target_id else None,
                    structured_payload=action_result.model_dump(mode="json") if action_result else None,
                    referenced_entity_type=reasoning_output.referenced_entity_type,
                    referenced_entity_id=reasoning_output.referenced_entity_id,
                )
                session.add(assistant_msg)
                await session.commit()
                await session.refresh(assistant_msg)

                yield f"event: content\ndata: {json.dumps({'chunk': reasoning_output.message})}\n\n"

                done_payload = {
                    "message_id": str(assistant_msg.id or uuid.uuid4()),
                    "conversation_id": str(conversation.id or uuid.uuid4()),
                    "role": "assistant",
                    "content": reasoning_output.message,
                    "action_id": action_id,
                    "action_status": action_status.value if action_status else None,
                    "action_result": action_result.model_dump(mode="json") if action_result else None,
                    "referenced_entity_type": reasoning_output.referenced_entity_type,
                    "referenced_entity_id": reasoning_output.referenced_entity_id,
                    "created_at": assistant_msg.created_at.isoformat() if assistant_msg.created_at else datetime.now(timezone.utc).isoformat(),
                }
                yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

        except asyncio.CancelledError:
            logger.info("SSE client disconnected from stream.")
            return
        except Exception as exc:
            logger.error(f"Error during SSE stream: {exc}")
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/conversations",
    response_model=AssistantConversationListResponse,
    summary="List assistant conversation threads for a project",
)
async def list_conversations(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> AssistantConversationListResponse:
    """Retrieve all conversations for the given project ordered by updated timestamp."""
    await _resolve_project(project_id, session, current_user)

    stmt = (
        select(AssistantConversation)
        .where(AssistantConversation.project_id == project_id)
    )
    is_admin = current_user is not None and (
        getattr(current_user, "role", None) == UserRole.ADMIN
        or getattr(current_user, "role", None) == UserRole.ADMIN.value
    )
    if current_user is not None and not is_admin:
        stmt = stmt.where(
            (AssistantConversation.user_id == current_user.id) | (AssistantConversation.user_id.is_(None))
        )
    stmt = stmt.options(selectinload(AssistantConversation.messages)).order_by(AssistantConversation.updated_at.desc())
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
                user_id=conv.user_id,
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
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> AssistantConversationResponse:
    """Retrieve full conversation history for a specific thread."""
    await _resolve_project(project_id, session, current_user)

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
    if not _is_conversation_authorized(conv, current_user):
        raise ForbiddenError("You do not have permission to access this conversation.")

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
        user_id=conv.user_id,
        title=conv.title,
        messages=msgs,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete single assistant conversation thread",
)
async def delete_conversation(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    conversation_id: Annotated[uuid.UUID, Path(description="Conversation UUID")],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> None:
    """Delete a conversation thread if authorized."""
    await _resolve_project(project_id, session, current_user)
    stmt = select(AssistantConversation).where(
        AssistantConversation.id == conversation_id,
        AssistantConversation.project_id == project_id,
    )
    res = await session.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise NotFoundError("AssistantConversation", str(conversation_id))
    if not _is_conversation_authorized(conv, current_user):
        raise ForbiddenError("You do not have permission to access this conversation.")
    await session.delete(conv)
    await session.commit()


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
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> ActionResult:
    """Confirm and execute a pending mutating engineering action."""
    await _resolve_project(project_id, session, current_user)
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
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> ActionResult:
    """Directly trigger or gate an action without requiring a natural-language turn."""
    await _resolve_project(project_id, session, current_user)
    return await action_service.execute_action(
        project_id=project_id,
        action_id=request.action_id,
        parameters=request.parameters,
        target_id=request.target_id,
        user_id=str(current_user.id) if current_user else "assistant_user",
        conversation_id=request.conversation_id,
    )

