"""
Runtime Environment for Type-Directed Computing

This module provides the core runtime infrastructure for executing actions with
proper resource management, capability enforcement, and effect tracking.
"""

import resource
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Callable
from contextlib import contextmanager
from enum import Enum



class ExecutionState(Enum):
    """Execution state of a runtime context."""
    IDLE = "idle"
    RUNNING = "running" 
    SUSPENDED = "suspended"
    FAILED = "failed"
    COMPLETED = "completed"


class RuntimeError(Exception):
    """Base exception for runtime errors."""
    pass


class ResourceExhaustedError(RuntimeError):
    """Raised when resource limits are exceeded."""
    pass


class CapabilityDeniedError(RuntimeError):
    """Raised when an action attempts to use a denied capability."""
    pass


class EffectViolationError(RuntimeError):
    """Raised when an action performs effects not declared in its type."""
    pass


@dataclass(frozen=True)
class ResourceLimits:
    """Resource usage limits for an execution context."""
    max_memory_mb: int = 100
    max_cpu_seconds: float = 30.0
    max_file_handles: int = 10
    max_network_connections: int = 5
    max_execution_time: float = 60.0


@dataclass
class ResourceUsage:
    """Current resource usage tracking."""
    memory_mb: float = 0.0
    cpu_seconds: float = 0.0 
    file_handles: int = 0
    network_connections: int = 0
    execution_time: float = 0.0
    start_time: float = field(default_factory=time.time)
    
    def update_execution_time(self):
        """Update the execution time."""
        self.execution_time = time.time() - self.start_time


@dataclass
class CapabilityGrant:
    """Represents a granted capability with specific permissions."""
    effect_type: str  # e.g., "IO", "Network", "FileSystem"
    permissions: Set[str]  # e.g., {"read", "write"}, {"connect", "bind"}
    resource_scope: Optional[str] = None  # e.g., "/tmp/*", "*.example.com"


class ExecutionContext:
    """
    Execution context that manages action execution with resource limits,
    capability enforcement, and effect tracking.
    """
    
    def __init__(
        self,
        context_id: str,
        limits: ResourceLimits = None,
        granted_capabilities: List[CapabilityGrant] = None,
        parent_context: Optional['ExecutionContext'] = None
    ):
        self.context_id = context_id
        self.limits = limits or ResourceLimits()
        self.granted_capabilities = granted_capabilities or []
        self.parent_context = parent_context
        
        self.state = ExecutionState.IDLE
        self.usage = ResourceUsage()
        self.declared_effects: Set[str] = set()
        self.observed_effects: Set[str] = set()
        
        self._lock = threading.RLock()
        self._cleanup_callbacks: List[Callable] = []
        
        # Create capability lookup for fast access
        self._capability_map: Dict[str, CapabilityGrant] = {
            cap.effect_type: cap for cap in self.granted_capabilities
        }
    
    @contextmanager
    def execution(self):
        """Context manager for action execution with resource monitoring."""
        with self._lock:
            if self.state != ExecutionState.IDLE:
                raise RuntimeError(f"Context {self.context_id} is not idle: {self.state}")
            
            self.state = ExecutionState.RUNNING
            self.usage = ResourceUsage()  # Reset usage tracking
            
        try:
            # Set resource limits
            self._apply_resource_limits()
            yield self
            
            # Check final resource usage
            self._check_resource_limits()
            self.state = ExecutionState.COMPLETED
            
        except Exception:
            self.state = ExecutionState.FAILED
            raise
            
        finally:
            # Clean up resources
            self._cleanup()
    
    def declare_effects(self, effect_types: Set[str]):
        """Declare what effects this execution will perform."""
        self.declared_effects = effect_types.copy()
        
        # Verify all declared effects are permitted
        for effect in effect_types:
            if effect not in self._capability_map:
                raise CapabilityDeniedError(
                    f"Effect '{effect}' not granted to context {self.context_id}"
                )
    
    def record_effect(self, effect_type: str, operation: str, details: Optional[Dict] = None):
        """Record that an effect has been performed."""
        # Check if effect was declared
        if effect_type not in self.declared_effects:
            raise EffectViolationError(
                f"Undeclared effect '{effect_type}' in context {self.context_id}"
            )
        
        # Check capability permissions
        if not self._check_capability_permission(effect_type, operation):
            raise CapabilityDeniedError(
                f"Permission denied for {effect_type}.{operation} in context {self.context_id}"
            )
        
        self.observed_effects.add(effect_type)
        
        # Update resource usage based on effect
        self._update_resource_usage(effect_type, operation, details or {})
    
    def check_capability(self, effect_type: str, operation: str) -> bool:
        """Check if a capability operation is permitted."""
        return (
            effect_type in self.declared_effects and 
            self._check_capability_permission(effect_type, operation)
        )
    
    def add_cleanup_callback(self, callback: Callable):
        """Add a cleanup callback to be called when context is destroyed."""
        self._cleanup_callbacks.append(callback)
    
    def _apply_resource_limits(self):
        """Apply system resource limits."""
        try:
            # Memory limit (soft limit)
            if self.limits.max_memory_mb > 0:
                memory_bytes = self.limits.max_memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            
            # CPU time limit
            if self.limits.max_cpu_seconds > 0:
                cpu_limit = int(self.limits.max_cpu_seconds)
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
                
        except (OSError, ValueError) as e:
            raise RuntimeError(f"Failed to apply resource limits: {e}")
    
    def _check_resource_limits(self):
        """Check if current resource usage exceeds limits."""
        self.usage.update_execution_time()
        
        if self.usage.execution_time > self.limits.max_execution_time:
            raise ResourceExhaustedError(
                f"Execution time limit exceeded: {self.usage.execution_time:.2f}s > {self.limits.max_execution_time}s"
            )
        
        if self.usage.memory_mb > self.limits.max_memory_mb:
            raise ResourceExhaustedError(
                f"Memory limit exceeded: {self.usage.memory_mb}MB > {self.limits.max_memory_mb}MB"
            )
        
        if self.usage.file_handles > self.limits.max_file_handles:
            raise ResourceExhaustedError(
                f"File handle limit exceeded: {self.usage.file_handles} > {self.limits.max_file_handles}"
            )
    
    def _check_capability_permission(self, effect_type: str, operation: str) -> bool:
        """Check if the operation is allowed for the given effect type."""
        capability = self._capability_map.get(effect_type)
        if not capability:
            return False
        
        return operation in capability.permissions
    
    def _update_resource_usage(self, effect_type: str, operation: str, details: Dict):
        """Update resource usage based on performed effect."""
        if effect_type == "IO":
            if operation in ["read", "write"]:
                self.usage.file_handles = max(self.usage.file_handles, details.get("handles", 0))
        
        elif effect_type == "Network":
            if operation in ["connect", "bind"]:
                self.usage.network_connections += 1
        
        # Always check limits after updating
        self._check_resource_limits()
    
    def _cleanup(self):
        """Clean up resources and call cleanup callbacks."""
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception:
                pass  # Ignore cleanup errors
        
        self._cleanup_callbacks.clear()


class Runtime:
    """
    Main runtime environment for type-directed computing.
    Manages execution contexts, enforces security, and provides observability.
    """
    
    def __init__(self):
        self.contexts: Dict[str, ExecutionContext] = {}
        self._context_counter = 0
        self._lock = threading.RLock()
        self._default_limits = ResourceLimits()
    
    def create_context(
        self,
        granted_capabilities: List[CapabilityGrant] = None,
        limits: ResourceLimits = None,
        parent_context_id: Optional[str] = None
    ) -> str:
        """Create a new execution context."""
        with self._lock:
            self._context_counter += 1
            context_id = f"ctx_{self._context_counter}"
            
            parent_context = None
            if parent_context_id:
                parent_context = self.contexts.get(parent_context_id)
                if not parent_context:
                    raise ValueError(f"Parent context not found: {parent_context_id}")
            
            context = ExecutionContext(
                context_id=context_id,
                limits=limits or self._default_limits,
                granted_capabilities=granted_capabilities or [],
                parent_context=parent_context
            )
            
            self.contexts[context_id] = context
            return context_id
    
    def get_context(self, context_id: str) -> ExecutionContext:
        """Get an execution context by ID."""
        context = self.contexts.get(context_id)
        if not context:
            raise ValueError(f"Context not found: {context_id}")
        return context
    
    def destroy_context(self, context_id: str):
        """Destroy an execution context and clean up resources."""
        with self._lock:
            context = self.contexts.pop(context_id, None)
            if context:
                context._cleanup()
    
    def list_contexts(self) -> Dict[str, ExecutionState]:
        """List all contexts and their current states."""
        return {cid: ctx.state for cid, ctx in self.contexts.items()}
    
    def get_context_usage(self, context_id: str) -> ResourceUsage:
        """Get resource usage for a context."""
        context = self.get_context(context_id)
        context.usage.update_execution_time()
        return context.usage
    
    def set_default_limits(self, limits: ResourceLimits):
        """Set default resource limits for new contexts."""
        self._default_limits = limits


# Global runtime instance
_runtime = Runtime()

def get_runtime() -> Runtime:
    """Get the global runtime instance."""
    return _runtime