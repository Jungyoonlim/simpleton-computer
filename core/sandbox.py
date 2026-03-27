"""
Sandboxing and isolation system for secure action execution.

This module provides process-level and container-level isolation for running
untrusted or resource-intensive actions safely.
"""

import os
import tempfile
import multiprocessing as mp
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
import threading
import time

from .runtime import ExecutionContext


class SandboxError(Exception):
    """Base exception for sandbox-related errors."""
    pass


class SandboxTimeoutError(SandboxError):
    """Raised when sandbox execution times out."""
    pass


class SandboxResourceError(SandboxError):
    """Raised when sandbox resource limits are exceeded."""
    pass


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""
    use_process_isolation: bool = True
    use_filesystem_isolation: bool = True
    use_network_isolation: bool = False
    allowed_modules: List[str] = field(default_factory=lambda: [
        "builtins", "typing", "dataclasses", "json", "re", "datetime", "math"
    ])
    blocked_modules: List[str] = field(default_factory=lambda: [
        "os", "subprocess", "sys", "importlib", "__builtin__"
    ])
    temp_dir_prefix: str = "simpleton_sandbox_"
    max_subprocess_count: int = 0  # No subprocesses allowed by default


@dataclass
class SandboxResult:
    """Result of sandbox execution."""
    success: bool
    return_value: Any = None
    error: Optional[str] = None
    stdout: str = ""
    stderr: str = ""
    execution_time: float = 0.0
    memory_peak_mb: float = 0.0
    exit_code: Optional[int] = None


class ProcessSandbox:
    """
    Process-based sandbox that isolates action execution in a separate process
    with resource limits and restricted capabilities.
    """
    
    def __init__(self, config: SandboxConfig = None):
        self.config = config or SandboxConfig()
        self._temp_dirs: List[Path] = []
    
    def execute(
        self,
        target_func: Callable,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        context: Optional[ExecutionContext] = None,
        timeout: float = 30.0
    ) -> SandboxResult:
        """Execute a function in a sandboxed process."""
        kwargs = kwargs or {}
        
        # Create isolated temporary directory
        temp_dir = None
        if self.config.use_filesystem_isolation:
            temp_dir = self._create_temp_workspace()
        
        try:
            # Set up the sandbox environment
            sandbox_env = self._prepare_sandbox_environment(temp_dir)
            
            # Execute in separate process
            if self.config.use_process_isolation:
                return self._execute_in_process(
                    target_func, args, kwargs, sandbox_env, timeout, context
                )
            else:
                # Direct execution (less secure but faster for trusted code)
                return self._execute_direct(target_func, args, kwargs, timeout)
                
        finally:
            # Clean up temporary directory
            if temp_dir:
                self._cleanup_temp_workspace(temp_dir)
    
    def _create_temp_workspace(self) -> Path:
        """Create an isolated temporary workspace."""
        temp_dir = Path(tempfile.mkdtemp(prefix=self.config.temp_dir_prefix))
        self._temp_dirs.append(temp_dir)
        
        # Set restrictive permissions
        temp_dir.chmod(0o700)
        
        return temp_dir
    
    def _cleanup_temp_workspace(self, temp_dir: Path):
        """Clean up temporary workspace."""
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            if temp_dir in self._temp_dirs:
                self._temp_dirs.remove(temp_dir)
        except Exception:
            pass  # Ignore cleanup errors
    
    def _prepare_sandbox_environment(self, temp_dir: Optional[Path]) -> Dict[str, Any]:
        """Prepare the sandbox execution environment."""
        env = {
            "temp_dir": str(temp_dir) if temp_dir else None,
            "allowed_modules": self.config.allowed_modules.copy(),
            "blocked_modules": self.config.blocked_modules.copy(),
            "max_subprocess_count": self.config.max_subprocess_count
        }
        return env
    
    def _execute_in_process(
        self,
        target_func: Callable,
        args: tuple,
        kwargs: Dict[str, Any],
        sandbox_env: Dict[str, Any],
        timeout: float,
        context: Optional[ExecutionContext]
    ) -> SandboxResult:
        """Execute function in a separate process with monitoring."""
        
        # Create communication pipes
        parent_conn, child_conn = mp.Pipe()
        
        # Start the sandbox process
        process = mp.Process(
            target=self._sandbox_worker,
            args=(child_conn, target_func, args, kwargs, sandbox_env, context)
        )
        
        start_time = time.time()
        process.start()
        
        try:
            # Wait for result with timeout
            if parent_conn.poll(timeout):
                result_data = parent_conn.recv()
                process.join(timeout=1.0)  # Give process time to clean up
                
                execution_time = time.time() - start_time
                
                if isinstance(result_data, dict) and "error" in result_data:
                    return SandboxResult(
                        success=False,
                        error=result_data["error"],
                        execution_time=execution_time
                    )
                else:
                    return SandboxResult(
                        success=True,
                        return_value=result_data,
                        execution_time=execution_time
                    )
            else:
                # Timeout occurred
                process.terminate()
                process.join(timeout=1.0)
                if process.is_alive():
                    process.kill()
                
                return SandboxResult(
                    success=False,
                    error=f"Execution timed out after {timeout}s",
                    execution_time=timeout
                )
                
        except Exception as e:
            process.terminate()
            process.join(timeout=1.0)
            if process.is_alive():
                process.kill()
            
            return SandboxResult(
                success=False,
                error=f"Sandbox execution failed: {str(e)}",
                execution_time=time.time() - start_time
            )
        
        finally:
            parent_conn.close()
    
    def _execute_direct(
        self,
        target_func: Callable,
        args: tuple,
        kwargs: Dict[str, Any],
        timeout: float
    ) -> SandboxResult:
        """Execute function directly in current process (less secure)."""
        start_time = time.time()
        
        try:
            # Set up a timeout using threading
            result_container = [None]
            error_container = [None]
            
            def target():
                try:
                    result_container[0] = target_func(*args, **kwargs)
                except Exception as e:
                    error_container[0] = str(e)
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout)
            
            execution_time = time.time() - start_time
            
            if thread.is_alive():
                return SandboxResult(
                    success=False,
                    error=f"Execution timed out after {timeout}s",
                    execution_time=execution_time
                )
            
            if error_container[0]:
                return SandboxResult(
                    success=False,
                    error=error_container[0],
                    execution_time=execution_time
                )
            
            return SandboxResult(
                success=True,
                return_value=result_container[0],
                execution_time=execution_time
            )
            
        except Exception as e:
            return SandboxResult(
                success=False,
                error=f"Direct execution failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    @staticmethod
    def _sandbox_worker(
        conn: mp.connection.Connection,
        target_func: Callable,
        args: tuple,
        kwargs: Dict[str, Any],
        sandbox_env: Dict[str, Any],
        context: Optional[ExecutionContext]
    ):
        """Worker function that runs in the sandboxed process."""
        try:
            # Apply sandbox restrictions
            ProcessSandbox._apply_sandbox_restrictions(sandbox_env)
            
            # Execute the target function
            result = target_func(*args, **kwargs)
            conn.send(result)
            
        except Exception as e:
            conn.send({"error": str(e)})
        
        finally:
            conn.close()
    
    @staticmethod
    def _apply_sandbox_restrictions(sandbox_env: Dict[str, Any]):
        """Apply sandbox restrictions in the worker process."""
        # Restrict module imports by modifying __builtins__
        original_import = __builtins__.__dict__.get('__import__', __import__)
        
        def restricted_import(name, *args, **kwargs):
            if name in sandbox_env["blocked_modules"]:
                raise ImportError(f"Module '{name}' is blocked in sandbox")
            
            if (sandbox_env["allowed_modules"] and 
                name not in sandbox_env["allowed_modules"] and
                not any(name.startswith(allowed + ".") for allowed in sandbox_env["allowed_modules"])):
                raise ImportError(f"Module '{name}' is not in allowed list")
            
            return original_import(name, *args, **kwargs)
        
        __builtins__.__dict__['__import__'] = restricted_import
        
        # Change working directory to temp dir if provided
        if sandbox_env.get("temp_dir"):
            os.chdir(sandbox_env["temp_dir"])
        
        # Disable subprocess creation if not allowed
        if sandbox_env.get("max_subprocess_count", 0) == 0:
            def blocked_function(*args, **kwargs):
                raise PermissionError("Subprocess creation is blocked in sandbox")
            
            # Block common subprocess modules (if they were allowed)
            try:
                import subprocess
                subprocess.run = blocked_function
                subprocess.call = blocked_function
                subprocess.Popen = blocked_function
            except ImportError:
                pass  # subprocess was already blocked
    
    def cleanup(self):
        """Clean up any remaining temporary directories."""
        for temp_dir in self._temp_dirs.copy():
            self._cleanup_temp_workspace(temp_dir)


class ContainerSandbox:
    """
    Container-based sandbox using Docker or similar technology.
    Provides stronger isolation than process sandbox but requires container runtime.
    """
    
    def __init__(self, config: SandboxConfig = None, container_image: str = "python:3.11-slim"):
        self.config = config or SandboxConfig()
        self.container_image = container_image
    
    def execute(
        self,
        target_func: Callable,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        context: Optional[ExecutionContext] = None,
        timeout: float = 30.0
    ) -> SandboxResult:
        """Execute function in a container sandbox."""
        # This is a placeholder for container-based execution
        # In a full implementation, this would:
        # 1. Serialize the function and arguments
        # 2. Create a container with appropriate limits
        # 3. Execute the function in the container
        # 4. Return the results
        
        raise NotImplementedError("Container sandbox requires container runtime integration")


def create_sandbox(
    sandbox_type: str = "process",
    config: SandboxConfig = None
) -> ProcessSandbox:
    """Factory function to create appropriate sandbox."""
    if sandbox_type == "process":
        return ProcessSandbox(config)
    elif sandbox_type == "container":
        return ContainerSandbox(config)
    else:
        raise ValueError(f"Unknown sandbox type: {sandbox_type}")


@contextmanager
def sandboxed_execution(
    sandbox_type: str = "process",
    config: SandboxConfig = None,
    timeout: float = 30.0
):
    """Context manager for sandboxed execution."""
    sandbox = create_sandbox(sandbox_type, config)
    try:
        yield lambda func, *args, **kwargs: sandbox.execute(
            func, args, kwargs, timeout=timeout
        )
    finally:
        sandbox.cleanup()