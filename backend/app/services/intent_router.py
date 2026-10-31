"""Authoritative Intent Routing and Disambiguation for IntelliAssist.

Distinguishes:
- ORDINARY_CONVERSATION: Greetings, conversational chat, platform capabilities overview.
- PLATFORM_HELP (IntelliGuide): Questions regarding SE IntelliPlatform architecture,
  immutable DevelopmentVersions, sandbox execution, browser testing, environments, and workflows.
- CODE_EXPLANATION (IntelliDev): Grounded explanations of components, state, hooks,
  API routing, database models, and file architecture based on active version source files.
- DEBUGGING (IntelliDev): Investigating runtime errors, live preview discrepancies,
  broken event handlers, or diagnostic stack traces.
- CODE_REVIEW (IntelliDev): Assessing code quality, security considerations, and best practices.
- FEATURE_PLANNING (IntelliDev): Multi-file feature specifications, user stories, and architecture plans.
- TEST_EXECUTION: Explicit user requests to execute sandbox tests, browser journeys, or test generation.
- VERIFICATION_TROUBLESHOOTING: Explicit requests to diagnose verification failures, linting, or Ruff issues.

Prevents background errors or failed verification states in context from hijacking unrelated user queries.
"""

import enum
import re
from typing import Any
from pydantic import BaseModel, Field


class AssistantIntent(str, enum.Enum):
    """Categorical intent routing for IntelliAssist conversations."""
    ORDINARY_CONVERSATION = "ORDINARY_CONVERSATION"
    PLATFORM_HELP = "PLATFORM_HELP"
    CODE_EXPLANATION = "CODE_EXPLANATION"
    DEBUGGING = "DEBUGGING"
    CODE_REVIEW = "CODE_REVIEW"
    FEATURE_PLANNING = "FEATURE_PLANNING"
    TEST_EXECUTION = "TEST_EXECUTION"
    VERIFICATION_TROUBLESHOOTING = "VERIFICATION_TROUBLESHOOTING"
    CODE_MODIFICATION = "CODE_MODIFICATION"


class IntentClassificationResult(BaseModel):
    """Structured routing outcome with persona, action gating, and diagnostic focus."""
    intent: AssistantIntent
    persona: str = Field(..., description="'IntelliGuide' for platform help, 'IntelliDev' for project engineering")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning: str
    allow_actions: bool = Field(
        default=False,
        description="Whether candidate engineering actions can be suggested or executed for this turn",
    )
    is_fast_path_candidate: bool = Field(
        default=False,
        description="True only for short, explicit imperative modification commands",
    )
    diagnostic_focus: str | None = Field(
        default=None,
        description="Specific diagnostic focus if debugging (e.g. 'preview_runtime', 'stack_trace', 'static_analysis')",
    )


class IntentRouter:
    """Classifies user messages and history into distinct conversational intents."""

    @staticmethod
    def classify(
        user_message: str,
        history_messages: list[dict[str, str]] | None = None,
    ) -> IntentClassificationResult:
        """Deterministically determine primary intent and routing parameters."""
        raw_msg = (user_message or "").strip()
        msg = raw_msg.lower()

        # 1. Follow-up detection for short, context-dependent queries
        short_followup_patterns = [
            r"^(whats? the matter|what's the matter|why\??|why is that\??|how come\??|whats? wrong|what's wrong\??)",
            r"^(explain (further|more)|tell me more|elaborate|continue|what else\??)",
            r"^(why did that happen|what happened\??|how does that work\??)$",
        ]
        is_short_followup = any(re.search(pat, msg) for pat in short_followup_patterns) or len(msg.split()) <= 4 and ("why" in msg or "matter" in msg or "wrong" in msg or "how" in msg)

        if is_short_followup and history_messages:
            # Look at previous turns to inherit intent
            recent_user_turns = [m.get("content", "") for m in history_messages if m.get("role") == "user"]
            recent_asst_turns = [m.get("content", "") for m in history_messages if m.get("role") == "assistant"]
            last_user = recent_user_turns[-1].lower() if recent_user_turns else ""
            last_asst = recent_asst_turns[-1].lower() if recent_asst_turns else ""

            if any(term in last_user for term in ["preview", "not seen", "not working", "error", "bug", "fails"]) or any(term in last_asst for term in ["preview", "runtime", "diagnosis"]):
                return IntentClassificationResult(
                    intent=AssistantIntent.DEBUGGING,
                    persona="IntelliDev",
                    confidence=0.92,
                    reasoning="Follow-up inquiry to previous debugging / preview conversation context.",
                    allow_actions=False,
                    diagnostic_focus="preview_runtime" if "preview" in (last_user + last_asst) else "general_bug",
                )
            if any(term in last_user for term in ["explain", "how does", "what is", "walk through", ".tsx", ".py"]):
                return IntentClassificationResult(
                    intent=AssistantIntent.CODE_EXPLANATION,
                    persona="IntelliDev",
                    confidence=0.90,
                    reasoning="Follow-up clarification to previous code explanation context.",
                    allow_actions=False,
                )
            if any(term in last_user for term in ["platform", "workflow", "version", "staging", "environment"]):
                return IntentClassificationResult(
                    intent=AssistantIntent.PLATFORM_HELP,
                    persona="IntelliGuide",
                    confidence=0.90,
                    reasoning="Follow-up clarification to platform help context.",
                    allow_actions=False,
                )

        # 2. Ordinary Conversation (Greetings, capability inquiries, acknowledgments)
        greeting_words = {"hi", "hello", "hey", "greetings", "good morning", "good evening", "good afternoon"}
        if msg in greeting_words or re.match(r"^(hi|hello|hey)\b[!., ]*$", msg):
            return IntentClassificationResult(
                intent=AssistantIntent.ORDINARY_CONVERSATION,
                persona="IntelliGuide",
                confidence=1.0,
                reasoning="Standard conversational greeting.",
                allow_actions=False,
            )
        if any(msg == q for q in ["who are you", "who are you?", "what can you do", "what can you do?", "what is your role", "what is your role?"]):
            return IntentClassificationResult(
                intent=AssistantIntent.ORDINARY_CONVERSATION,
                persona="IntelliGuide",
                confidence=1.0,
                reasoning="Inquiry regarding assistant identity and capabilities.",
                allow_actions=False,
            )
        if msg in {"thank you", "thanks", "thanks!", "great thanks", "awesome", "got it"}:
            return IntentClassificationResult(
                intent=AssistantIntent.ORDINARY_CONVERSATION,
                persona="IntelliGuide",
                confidence=1.0,
                reasoning="Conversational acknowledgment or gratitude.",
                allow_actions=False,
            )

        # 3. Explicit Verification Troubleshooting
        if any(term in msg for term in [
            "run static analysis", "execute static analysis", "why did verification fail",
            "fix static analysis", "static analysis errors", "static analysis report",
            "ruff lint", "linting errors", "verify version", "check verification",
        ]):
            return IntentClassificationResult(
                intent=AssistantIntent.VERIFICATION_TROUBLESHOOTING,
                persona="IntelliDev",
                confidence=0.95,
                reasoning="Explicit user request regarding static analysis or version verification troubleshooting.",
                allow_actions=True,
                diagnostic_focus="static_analysis",
            )

        # 4. Explicit Test Execution
        if any(term in msg for term in [
            "run unit tests", "run test suite", "run browser tests", "run sandbox",
            "execute tests", "generate ai tests", "generate tests", "run regression tests",
            "run smoke tests", "smoke tests", "run smoke", "run test", "run tests",
        ]):
            return IntentClassificationResult(
                intent=AssistantIntent.TEST_EXECUTION,
                persona="IntelliDev",
                confidence=0.95,
                reasoning="Explicit user request to execute or generate tests.",
                allow_actions=True,
                diagnostic_focus="testing",
            )

        # 5. Code Review
        if any(term in msg for term in [
            "code review", "review the code", "review this file", "review my code",
            "check for vulnerabilities", "security audit", "best practices in",
            "clean code review", "audit security",
        ]):
            return IntentClassificationResult(
                intent=AssistantIntent.CODE_REVIEW,
                persona="IntelliDev",
                confidence=0.95,
                reasoning="Request for architectural, security, or code quality review.",
                allow_actions=False,
            )

        # 6. Debugging (Errors, Tracebacks, Live Preview Issues, Broken Handlers)
        preview_triggers = [
            "changes are not seen in live preview",
            "changes not seen in live preview",
            "changes are not showing",
            "not visible in live preview",
            "not updating in live preview",
            "preview is not showing",
            "preview is blank",
            "preview shows old",
            "preview is not updating",
            "live preview error",
            "live preview is broken",
        ]
        if any(t in msg for t in preview_triggers) or ("preview" in msg and ("not seen" in msg or "not showing" in msg or "not update" in msg or "broken" in msg)):
            return IntentClassificationResult(
                intent=AssistantIntent.DEBUGGING,
                persona="IntelliDev",
                confidence=0.98,
                reasoning="User reporting that changes or code are not reflected in Live Preview.",
                allow_actions=False,
                diagnostic_focus="preview_runtime",
            )

        # 6. Fast-Path Imperative Modifications (Single short imperative command)
        is_short_command = len(raw_msg) <= 80 and len(raw_msg.splitlines()) <= 2
        fast_path_imperatives = [
            "add a login page", "add login page", "add authentication", "add login",
            "make the homepage more modern", "make homepage more modern",
            "add a search bar", "add search bar", "add dark mode",
            "delete authentication", "remove authentication",
            "the login button isn't working", "login button isn't working",
            "the login button is not working", "the button doesn't work",
            "the button isn't working", "button doesn't work",
            "button isn't working", "button not working", "fix the button",
            "fix the login button", "fix button",
        ]
        if is_short_command and any(cmd in msg for cmd in fast_path_imperatives):
            return IntentClassificationResult(
                intent=AssistantIntent.CODE_MODIFICATION,
                persona="IntelliDev",
                confidence=0.96,
                reasoning="Concise imperative modification or button repair command targeting project code.",
                allow_actions=True,
                is_fast_path_candidate=True,
            )

        # 7. Generic Debugging (Errors, Tracebacks, Live Preview Issues, Broken Handlers)
        error_indicators = [
            "traceback (most recent call last):",
            "typeerror:", "valueerror:", "syntaxerror:", "referenceerror:",
            "500 internal server error", "unhandled exception", "failed with exit code",
            "error:", "bug in", "fix the error", "diagnose the error",
            "handler isn't firing",
        ]
        if any(indicator in msg for indicator in error_indicators):
            return IntentClassificationResult(
                intent=AssistantIntent.DEBUGGING,
                persona="IntelliDev",
                confidence=0.95,
                reasoning="Bug, runtime exception, or broken event handler reported.",
                allow_actions=False,
                diagnostic_focus="stack_trace" if "traceback" in msg or "error:" in msg else "event_handler",
            )

        file_tokens = re.findall(r"[\w./-]+\.(?:tsx|ts|jsx|js|py|json|html|css|md)", user_message, re.IGNORECASE)

        # 7. Code Modification (Natural-language request to edit, update, modify, or add code to project files)
        code_mod_verbs = [
            "modify", "update", "change", "refactor", "edit",
            "implement", "replace", "add to", "insert into", "add", "create",
            "build", "insert", "integrate", "include", "put", "make", "write",
            "style", "customize", "fix", "enhance", "apply", "improve", "delete", "remove",
        ]
        code_keywords = [
            "endpoint", "component", "button", "route", "handler", "logic", "function",
            "form", "card", "header", "footer", "navbar", "nav", "title", "theme", "color",
            "search", "filter", "input", "page", "view", "ui", "modal", "dialog", "style",
            "css", "state", "tag", "badge", "table", "list", "item", "api", "backend",
            "frontend", "auth", "login", "task", "tasks", "todo", "code", "file", "screen",
            "dark", "dark mode", "csv", "export", "mobile", "layout", "responsive", "toggle",
        ]
        words = msg.split()
        has_mod_verb = any(verb in words or (verb + " ") in msg for verb in code_mod_verbs)
        has_code_kw = file_tokens or any(kw in msg for kw in code_keywords)
        is_informational = any(cue in msg for cue in ["explain", "walk through", "how does", "what does", "review", "describe", "show where", "tell me about"])
        starts_imperative = any(msg.startswith(prefix) for prefix in ["add ", "create ", "implement ", "update ", "change ", "modify ", "edit ", "make ", "style "])

        if (has_mod_verb and has_code_kw and not is_informational) or (starts_imperative and not is_informational):
            return IntentClassificationResult(
                intent=AssistantIntent.CODE_MODIFICATION,
                persona="IntelliDev",
                confidence=0.98,
                reasoning="Natural-language user request to modify or implement project source code.",
                allow_actions=True,
            )

        # 8. Code Explanation (Components, source files, state management, API routes)
        code_explanation_cues = [
            "explain how", "explain the", "how does", "walk through",
            "how is state managed", "state management in", "describe task creation",
            "how it communicates with", "what does", "show where",
            "explain component", "explain function", "where is the api defined",
        ]
        if any(cue in msg for cue in code_explanation_cues) or (file_tokens and any(q in msg for q in ["what", "how", "explain", "describe", "where"])):
            return IntentClassificationResult(
                intent=AssistantIntent.CODE_EXPLANATION,
                persona="IntelliDev",
                confidence=0.95,
                reasoning="Detailed source code or architectural explanation query.",
                allow_actions=False,
            )

        # 8. Feature Planning & Specifications (User stories, acceptance criteria, multi-line tasks)
        is_structured_task = (
            "**task name:**" in msg
            or "acceptance criteria:" in msg
            or "acceptance criteria" in msg
            or (len(raw_msg.splitlines()) >= 4 and ("description:" in msg or "enhance" in msg or "add" in msg))
        )
        if is_structured_task:
            return IntentClassificationResult(
                intent=AssistantIntent.FEATURE_PLANNING,
                persona="IntelliDev",
                confidence=0.98,
                reasoning="Structured task specification with acceptance criteria.",
                allow_actions=False,
                is_fast_path_candidate=False,
            )


        # 10. Platform Guidance (IntelliGuide)
        platform_keywords = [
            "se intelliplatform", "developmentversion", "sandbox",
            "workflow", "workflows", "promotion", "environments",
            "live preview architecture", "how does the platform", "what are stages",
        ]
        if any(kw in msg for kw in platform_keywords):
            return IntentClassificationResult(
                intent=AssistantIntent.PLATFORM_HELP,
                persona="IntelliGuide",
                confidence=0.90,
                reasoning="Platform concept or capability guidance inquiry.",
                allow_actions=False,
            )

        # Default fallback: Treat as Project-Aware Development inquiry (IntelliDev)
        return IntentClassificationResult(
            intent=AssistantIntent.CODE_EXPLANATION if file_tokens else AssistantIntent.ORDINARY_CONVERSATION,
            persona="IntelliDev" if file_tokens else "IntelliGuide",
            confidence=0.75,
            reasoning="Default conversational resolution based on presence of code entities.",
            allow_actions=False,
        )
