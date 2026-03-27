"""
Tests for the runtime environment and execution contexts.
"""

import pytest
import time
from core.runtime import (
    Runtime, ExecutionContext, ResourceLimits, ResourceUsage,
    CapabilityGrant, ExecutionState, CapabilityDeniedError, EffectViolationError,
    RuntimeError as CoreRuntimeError,
)


class TestExecutionContext:
    """Test ExecutionContext functionality."""
    
    def test_context_creation(self):
        """Test basic context creation."""
        limits = ResourceLimits(max_memory_mb=50, max_cpu_seconds=10.0)
        capabilities = [
            CapabilityGrant("IO", {"read", "write"}),
            CapabilityGrant("Network", {"connect"})
        ]
        
        context = ExecutionContext(
            context_id="test_ctx",
            limits=limits,
            granted_capabilities=capabilities
        )
        
        assert context.context_id == "test_ctx"
        assert context.limits.max_memory_mb == 50
        assert context.state == ExecutionState.IDLE
        assert len(context.granted_capabilities) == 2
    
    def test_effect_declaration_and_checking(self):
        """Test effect declaration and capability checking."""
        capabilities = [
            CapabilityGrant("IO", {"read", "write"}),
            CapabilityGrant("Network", {"connect"})
        ]
        
        context = ExecutionContext("test", granted_capabilities=capabilities)
        
        # Should succeed - we have IO capability
        context.declare_effects({"IO"})
        assert context.check_capability("IO", "read")
        assert context.check_capability("IO", "write")
        assert not context.check_capability("IO", "bind")  # Not granted
        
        # Should fail - no FileSystem capability
        with pytest.raises(CapabilityDeniedError):
            context.declare_effects({"FileSystem"})
    
    def test_effect_recording(self):
        """Test effect recording and validation."""
        capabilities = [CapabilityGrant("IO", {"read"})]
        context = ExecutionContext("test", granted_capabilities=capabilities)
        
        context.declare_effects({"IO"})
        
        # Should succeed - declared and permitted
        context.record_effect("IO", "read", {"file": "test.txt"})
        assert "IO" in context.observed_effects
        
        # Should fail - not declared
        with pytest.raises(EffectViolationError):
            context.record_effect("Network", "connect")
        
        # Should fail - not permitted
        with pytest.raises(CapabilityDeniedError):
            context.record_effect("IO", "write")
    
    def test_execution_context_manager(self):
        """Test execution context manager."""
        context = ExecutionContext("test")
        
        assert context.state == ExecutionState.IDLE
        
        with context.execution():
            assert context.state == ExecutionState.RUNNING
        
        assert context.state == ExecutionState.COMPLETED
    
    def test_execution_context_failure(self):
        """Test execution context failure handling."""
        context = ExecutionContext("test")
        
        with pytest.raises(ValueError):
            with context.execution():
                raise ValueError("Test error")
        
        assert context.state == ExecutionState.FAILED
    
    def test_resource_usage_tracking(self):
        """Test resource usage tracking."""
        context = ExecutionContext("test")
        
        # Initially zero
        assert context.usage.memory_mb == 0.0
        assert context.usage.execution_time == 0.0
        
        # Time should update
        context.usage.update_execution_time()
        assert context.usage.execution_time > 0.0
    
    def test_cleanup_callbacks(self):
        """Test cleanup callback system."""
        context = ExecutionContext("test")
        cleanup_called = []
        
        def cleanup():
            cleanup_called.append(True)
        
        context.add_cleanup_callback(cleanup)
        context._cleanup()
        
        assert len(cleanup_called) == 1


class TestRuntime:
    """Test Runtime functionality."""
    
    def test_runtime_creation(self):
        """Test runtime creation and global instance."""
        from core.runtime import get_runtime
        runtime = get_runtime()
        assert isinstance(runtime, Runtime)
    
    def test_context_lifecycle(self):
        """Test context creation and destruction."""
        runtime = Runtime()
        
        # Create context
        ctx_id = runtime.create_context()
        assert ctx_id.startswith("ctx_")
        assert ctx_id in runtime.contexts
        
        # Get context
        context = runtime.get_context(ctx_id)
        assert context.context_id == ctx_id
        
        # List contexts
        contexts = runtime.list_contexts()
        assert ctx_id in contexts
        assert contexts[ctx_id] == ExecutionState.IDLE
        
        # Destroy context
        runtime.destroy_context(ctx_id)
        assert ctx_id not in runtime.contexts
    
    def test_context_with_capabilities(self):
        """Test context creation with capabilities."""
        runtime = Runtime()
        
        capabilities = [CapabilityGrant("IO", {"read"})]
        limits = ResourceLimits(max_memory_mb=25)
        
        ctx_id = runtime.create_context(
            granted_capabilities=capabilities,
            limits=limits
        )
        
        context = runtime.get_context(ctx_id)
        assert len(context.granted_capabilities) == 1
        assert context.limits.max_memory_mb == 25
    
    def test_nonexistent_context(self):
        """Test accessing nonexistent context."""
        runtime = Runtime()
        
        with pytest.raises(ValueError, match="Context not found"):
            runtime.get_context("nonexistent")
    
    def test_default_limits(self):
        """Test default limits setting."""
        runtime = Runtime()
        new_limits = ResourceLimits(max_memory_mb=200)
        
        runtime.set_default_limits(new_limits)
        
        ctx_id = runtime.create_context()
        context = runtime.get_context(ctx_id)
        assert context.limits.max_memory_mb == 200


class TestResourceManagement:
    """Test resource management and limits."""
    
    def test_resource_limits_creation(self):
        """Test ResourceLimits creation with defaults."""
        limits = ResourceLimits()
        
        assert limits.max_memory_mb == 100
        assert limits.max_cpu_seconds == 30.0
        assert limits.max_file_handles == 10
        assert limits.max_network_connections == 5
        assert limits.max_execution_time == 60.0
    
    def test_resource_usage_tracking(self):
        """Test ResourceUsage tracking."""
        usage = ResourceUsage()
        
        # Should start with zero usage
        assert usage.memory_mb == 0.0
        assert usage.cpu_seconds == 0.0
        assert usage.file_handles == 0
        
        # Time tracking should work
        start_time = usage.start_time
        time.sleep(0.01)  # Small delay
        usage.update_execution_time()
        
        assert usage.execution_time > 0.0
        assert usage.start_time == start_time  # Shouldn't change


class TestCapabilityGrant:
    """Test CapabilityGrant functionality."""
    
    def test_capability_grant_creation(self):
        """Test CapabilityGrant creation."""
        grant = CapabilityGrant(
            effect_type="IO",
            permissions={"read", "write"},
            resource_scope="/tmp/*"
        )
        
        assert grant.effect_type == "IO"
        assert "read" in grant.permissions
        assert "write" in grant.permissions
        assert grant.resource_scope == "/tmp/*"
    
    def test_capability_grant_defaults(self):
        """Test CapabilityGrant with defaults."""
        grant = CapabilityGrant("Network", {"connect"})
        
        assert grant.effect_type == "Network"
        assert grant.resource_scope is None


class TestIntegration:
    """Integration tests for runtime components."""
    
    def test_runtime_with_effects_enforcement(self):
        """Test full integration of runtime with effect enforcement."""
        runtime = Runtime()
        
        capabilities = [CapabilityGrant("IO", {"read"})]
        ctx_id = runtime.create_context(granted_capabilities=capabilities)
        context = runtime.get_context(ctx_id)
        
        # Declare and record effects
        context.declare_effects({"IO"})
        
        with context.execution():
            context.record_effect("IO", "read", {"file": "test.txt"})
        
        assert context.state == ExecutionState.COMPLETED
        assert "IO" in context.observed_effects
    
    def test_context_reuse_prevention(self):
        """Test that contexts cannot be reused while running."""
        context = ExecutionContext("test")
        
        with context.execution():
            # Should not be able to start another execution
            with pytest.raises(CoreRuntimeError):
                with context.execution():
                    pass