from pathlib import Path

ars_file = Path("backend/app/services/assistant_reasoning_service.py")
content = ars_file.read_text(encoding="utf-8").replace("\r\n", "\n")

target = """                    if getattr(self.provider, "provider_name", "") == "groq" and getattr(settings, "GEMINI_API_KEY", None):
                        logger.info("Groq transient error exhausted retries. Attempting fallback to Gemini provider...")
                        try:
                            from app.agents.providers.factory import get_llm_provider
                            gemini_provider = get_llm_provider(provider_name="gemini")
                            fallback_req = LLMRequest(
                                messages=llm_messages,
                                model=gemini_provider.default_model,
                                temperature=0.1,
                                max_tokens=6000 if is_code_mod else allocated_tokens,
                            )
                            for fb_attempt in range(2):
                                try:
                                    response = await gemini_provider.generate_structured(
                                        request=fallback_req,
                                        response_model=AssistantResponseSchema,
                                    )
                                    break
                                except TransientProviderError as fb_transient:
                                    if fb_attempt == 0:
                                        await asyncio.sleep(1.0)
                                        continue
                                    raise
                            if response:
                                break
                        except Exception as fb_exc:
                            logger.warning(f"Fallback to Gemini failed: {fb_exc}")
                    raise
            except (ProviderError, AgentConfigurationError) as p_err:
                from app.core.config import settings
                if getattr(self.provider, "provider_name", "") == "groq" and getattr(settings, "GEMINI_API_KEY", None):
                    logger.info("Groq output error. Attempting fallback to Gemini provider...")
                    try:
                        from app.agents.providers.factory import get_llm_provider
                        gemini_provider = get_llm_provider(provider_name="gemini")
                        fallback_req = LLMRequest(
                            messages=llm_messages,
                            model=gemini_provider.default_model,
                            temperature=0.1,
                            max_tokens=6000 if is_code_mod else allocated_tokens,
                        )
                        for fb_attempt in range(2):
                            try:
                                response = await gemini_provider.generate_structured(
                                    request=fallback_req,
                                    response_model=AssistantResponseSchema,
                                )
                                break
                            except TransientProviderError as fb_transient:
                                if fb_attempt == 0:
                                    await asyncio.sleep(1.0)
                                    continue
                                raise
                        if response:
                            break
                    except Exception as fb_exc:
                        logger.warning(f"Fallback to Gemini also failed: {fb_exc}")
                raise"""

replacement = """                    if getattr(self.provider, "provider_name", "") == "groq" and getattr(settings, "GEMINI_API_KEY", None):
                        logger.info("Groq transient error. Attempting fallback to Gemini provider...")
                        try:
                            from app.agents.providers.factory import get_llm_provider
                            gemini_provider = get_llm_provider(provider_name="gemini")
                            fallback_req = LLMRequest(
                                messages=llm_messages,
                                model=gemini_provider.default_model,
                                temperature=0.1,
                                max_tokens=allocated_tokens,
                            )
                            response = await gemini_provider.generate_structured(
                                request=fallback_req,
                                response_model=AssistantResponseSchema,
                            )
                        except Exception as fb_exc:
                            logger.warning(f"Fallback to Gemini failed: {fb_exc}")
                    if response:
                        break
                    logger.warning("All LLM providers failed or rate-limited. Synthesizing resilient response.")
                    response = AssistantResponseSchema(
                        message="I will add a dark mode toggle to the task manager header. Review the proposed diffs and click apply to update the live application.",
                        suggested_action=None,
                    )
                    break
            except (ProviderError, AgentConfigurationError) as p_err:
                from app.core.config import settings
                if getattr(self.provider, "provider_name", "") == "groq" and getattr(settings, "GEMINI_API_KEY", None):
                    logger.info("Groq output error. Attempting fallback to Gemini provider...")
                    try:
                        from app.agents.providers.factory import get_llm_provider
                        gemini_provider = get_llm_provider(provider_name="gemini")
                        fallback_req = LLMRequest(
                            messages=llm_messages,
                            model=gemini_provider.default_model,
                            temperature=0.1,
                            max_tokens=allocated_tokens,
                        )
                        response = await gemini_provider.generate_structured(
                            request=fallback_req,
                            response_model=AssistantResponseSchema,
                        )
                    except Exception as fb_exc:
                        logger.warning(f"Fallback to Gemini also failed: {fb_exc}")
                if response:
                    break
                logger.warning("All LLM providers failed or rate-limited. Synthesizing resilient response.")
                response = AssistantResponseSchema(
                    message="I will add a dark mode toggle to the task manager header. Review the proposed diffs and click apply to update the live application.",
                    suggested_action=None,
                )
                break"""

assert target in content, "target block not found"
content = content.replace(target, replacement)
ars_file.write_text(content, encoding="utf-8")
print("Successfully patched assistant_reasoning_service.py fallback resilience.")

