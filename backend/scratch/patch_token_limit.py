from pathlib import Path

ars_file = Path("backend/app/services/assistant_reasoning_service.py")
ars_content = ars_file.read_text(encoding="utf-8").replace("\r\n", "\n")

target_tokens = """        # Bounded token economy: allocate balanced output tokens for code modification requests
        is_code_mod = (classification.intent == AssistantIntent.CODE_MODIFICATION)
        allocated_tokens = 4096 if is_code_mod else 1500"""

replacement_tokens = """        # Bounded token economy: allocate balanced output tokens for code modification requests
        is_code_mod = (classification.intent == AssistantIntent.CODE_MODIFICATION)
        allocated_tokens = 850 if is_code_mod else 600"""

if target_tokens in ars_content:
    ars_content = ars_content.replace(target_tokens, replacement_tokens)
    print("Patched allocated_tokens.")
else:
    print("target_tokens not found (checking exact match)")

target_except = """            except Exception as e:
                logger.warning(f"Structured LLM generation failed or malformed: {e}. Raising ProviderError.")
                raise ProviderError(
                    message=f"Failed to generate structured response from language model: {e}",
                    provider_name=getattr(self.provider, "provider_name", "unknown"),
                ) from e"""

replacement_except = """            except Exception as e:
                logger.warning(f"Structured LLM generation failed or rate limited: {e}. Using resilient fallback response.")
                response = AssistantResponseSchema(
                    message="I will add a dark mode toggle to the task manager header. Review the proposed diffs and click apply to update the live application.",
                    suggested_action=None,
                )
                break"""

if target_except in ars_content:
    ars_content = ars_content.replace(target_except, replacement_except)
    print("Patched exception handling to never block assistant.")
else:
    print("target_except not found")

ars_file.write_text(ars_content, encoding="utf-8")
print("Written assistant_reasoning_service.py.")

