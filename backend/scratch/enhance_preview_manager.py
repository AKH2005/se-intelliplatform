from pathlib import Path

target_file = Path("backend/app/runtime/preview_runtime_manager.py")
code = target_file.read_text(encoding="utf-8")

# 1. Update _kill_stale_port_8001 to ensure port is freed
old_kill = """                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        logger.info(f"Terminated stale process on port 8001 (PID {pid}).")
                    except Exception:
                        pass
            except Exception:
                pass"""

new_kill = """                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        logger.info(f"Terminated stale process on port 8001 (PID {pid}).")
                    except Exception:
                        pass
                import socket
                for _ in range(8):
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(0.2)
                        if s.connect_ex(("127.0.0.1", 8001)) != 0:
                            break
                    time.sleep(0.3)
            except Exception:
                pass"""

assert old_kill in code, "old_kill not found"
code = code.replace(old_kill, new_kill, 1)

# 2. Update poll_timeout in _ensure_running_unlocked
old_poll = """        # 4. Readiness health polling loop (STARTING -> HEALTH_CHECKING -> RUNNING)
        start_poll = time.monotonic()
        poll_timeout = 8.0
        last_err = ""

        while time.monotonic() - start_poll < poll_timeout:
            await asyncio.sleep(0.3)
            healthy, msg, details = await self.check_health(project_id=project_id, timeout=0.6)"""

new_poll = """        # 4. Readiness health polling loop (STARTING -> HEALTH_CHECKING -> RUNNING)
        start_poll = time.monotonic()
        poll_timeout = 25.0
        last_err = ""

        while time.monotonic() - start_poll < poll_timeout:
            await asyncio.sleep(0.4)
            healthy, msg, details = await self.check_health(project_id=project_id, timeout=1.2)"""

assert old_poll in code, "old_poll not found"
code = code.replace(old_poll, new_poll, 1)

# 3. Update restart_runtime to keep standalone server alive if already healthy
old_restart = """        async with self._lock:
            self.stop_runtime(project_id=project_id)
            await asyncio.sleep(0.3)
            return await self._ensure_running_unlocked(
                project_id, project_name, project_description, force_restart=True
            )"""

new_restart = """        async with self._lock:
            if self._is_docker_available():
                self.stop_runtime(project_id=project_id)
                await asyncio.sleep(0.5)
                return await self._ensure_running_unlocked(
                    project_id, project_name, project_description, force_restart=True
                )

            # For standalone preview runtime, probe if already healthy
            healthy, msg, details = await self.check_health(project_id=project_id, timeout=1.2)
            if healthy:
                await self.sync_context(project_id, project_name, project_description)
                return True, "Application preview active on port 8001.", details

            self.stop_runtime(project_id=project_id)
            await asyncio.sleep(0.5)
            return await self._ensure_running_unlocked(
                project_id, project_name, project_description, force_restart=True
            )"""

assert old_restart in code, "old_restart not found"
code = code.replace(old_restart, new_restart, 1)

target_file.write_text(code, encoding="utf-8")
print("SUCCESSFULLY ENHANCED preview_runtime_manager.py")

