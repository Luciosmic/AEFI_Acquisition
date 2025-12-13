"""
Tests for InMemoryEventBus (Diagram-Friendly)
"""

from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.tests.diagram_friendly_test import DiagramFriendlyTest

class TestInMemoryEventBus(DiagramFriendlyTest):
    """Test InMemoryEventBus pub/sub functionality with diagram generation."""
    
    def setUp(self):
        super().setUp()
        self.log_interaction("Test", "CREATE", "InMemoryEventBus", "Initialize fresh bus")
        self.bus = InMemoryEventBus()
    
    def test_pub_sub_basic(self):
        """Test basic publish/subscribe functionality."""
        calls = []
        
        def handler(data):
            self.log_interaction("Handler", "RECEIVE", "Test", "Handler called", {"data": data})
            calls.append(data)
        
        self.log_interaction("Test", "SUBSCRIBE", "InMemoryEventBus", "Subscribe handler", {"event": "test_event"})
        self.bus.subscribe('test_event', handler)
        
        self.log_interaction("Test", "PUBLISH", "InMemoryEventBus", "Publish event", {"event": "test_event", "data": 42})
        self.bus.publish('test_event', 42)
        
        expected = [42]
        self.log_interaction("Test", "ASSERT", "InMemoryEventBus", "Verify calls", expect=expected, got=calls)
        self.assertEqual(calls, expected)
    
    def test_multiple_subscribers(self):
        """Test multiple handlers for same event type."""
        calls1 = []
        calls2 = []
        
        def handler1(data):
            self.log_interaction("Handler1", "RECEIVE", "Test", "Handler1 called", {"data": data})
            calls1.append(data)
        
        def handler2(data):
            self.log_interaction("Handler2", "RECEIVE", "Test", "Handler2 called", {"data": data})
            calls2.append(data)
        
        self.log_interaction("Test", "SUBSCRIBE", "InMemoryEventBus", "Subscribe Handler1", {"event": "test_event"})
        self.bus.subscribe('test_event', handler1)
        self.log_interaction("Test", "SUBSCRIBE", "InMemoryEventBus", "Subscribe Handler2", {"event": "test_event"})
        self.bus.subscribe('test_event', handler2)
        
        self.log_interaction("Test", "PUBLISH", "InMemoryEventBus", "Publish event", {"event": "test_event", "data": "hello"})
        self.bus.publish('test_event', 'hello')
        
        expected1 = ['hello']
        expected2 = ['hello']
        
        self.log_interaction("Test", "ASSERT", "InMemoryEventBus", "Verify calls1", expect=expected1, got=calls1)
        self.assertEqual(calls1, expected1)
        self.log_interaction("Test", "ASSERT", "InMemoryEventBus", "Verify calls2", expect=expected2, got=calls2)
        self.assertEqual(calls2, expected2)
    
    def test_different_event_types(self):
        """Test that different event types are isolated."""
        calls_a = []
        calls_b = []
        
        def handler_a(data):
            self.log_interaction("HandlerA", "RECEIVE", "Test", "HandlerA called", {"data": data})
            calls_a.append(data)
        
        def handler_b(data):
            self.log_interaction("HandlerB", "RECEIVE", "Test", "HandlerB called", {"data": data})
            calls_b.append(data)
        
        self.log_interaction("Test", "SUBSCRIBE", "InMemoryEventBus", "Subscribe HandlerA", {"event": "event_a"})
        self.bus.subscribe('event_a', handler_a)
        self.log_interaction("Test", "SUBSCRIBE", "InMemoryEventBus", "Subscribe HandlerB", {"event": "event_b"})
        self.bus.subscribe('event_b', handler_b)
        
        self.log_interaction("Test", "PUBLISH", "InMemoryEventBus", "Publish event_a", {"event": "event_a", "data": "A"})
        self.bus.publish('event_a', 'A')
        self.log_interaction("Test", "PUBLISH", "InMemoryEventBus", "Publish event_b", {"event": "event_b", "data": "B"})
        self.bus.publish('event_b', 'B')
        
        expected_a = ['A']
        expected_b = ['B']
        
        self.log_interaction("Test", "ASSERT", "InMemoryEventBus", "Verify calls_a", expect=expected_a, got=calls_a)
        self.assertEqual(calls_a, expected_a)
        self.log_interaction("Test", "ASSERT", "InMemoryEventBus", "Verify calls_b", expect=expected_b, got=calls_b)
        self.assertEqual(calls_b, expected_b)
    
    def test_handler_error_isolation(self):
        """Test that error in one handler doesn't affect others."""
        calls = []
        
        def failing_handler(data):
            self.log_interaction("FailingHandler", "ERROR", "Test", "Handler raising error", {"data": data})
            raise ValueError("Handler error")
        
        def working_handler(data):
            self.log_interaction("WorkingHandler", "RECEIVE", "Test", "Handler called", {"data": data})
            calls.append(data)
        
        self.log_interaction("Test", "SUBSCRIBE", "InMemoryEventBus", "Subscribe FailingHandler", {"event": "test_event"})
        self.bus.subscribe('test_event', failing_handler)
        self.log_interaction("Test", "SUBSCRIBE", "InMemoryEventBus", "Subscribe WorkingHandler", {"event": "test_event"})
        self.bus.subscribe('test_event', working_handler)
        
        self.log_interaction("Test", "PUBLISH", "InMemoryEventBus", "Publish event", {"event": "test_event", "data": "test"})
        self.bus.publish('test_event', 'test')
        
        expected = ['test']
        self.log_interaction("Test", "ASSERT", "InMemoryEventBus", "Verify calls", expect=expected, got=calls)
        self.assertEqual(calls, expected)
    
    def test_no_subscribers(self):
        """Test publishing to event with no subscribers."""
        self.log_interaction("Test", "PUBLISH", "InMemoryEventBus", "Publish to no subscribers", {"event": "nonexistent_event"})
        self.bus.publish('nonexistent_event', 'data')
        
        self.log_interaction("Test", "ASSERT", "InMemoryEventBus", "Verify no crash", expect="Success", got="Success")
    
    def test_unsubscribe(self):
        """Test unsubscribing a handler."""
        calls = []
        
        def handler(data):
            self.log_interaction("Handler", "RECEIVE", "Test", "Handler called", {"data": data})
            calls.append(data)
        
        self.log_interaction("Test", "SUBSCRIBE", "InMemoryEventBus", "Subscribe handler", {"event": "test_event"})
        self.bus.subscribe('test_event', handler)
        
        self.log_interaction("Test", "PUBLISH", "InMemoryEventBus", "Publish 1", {"event": "test_event", "data": 1})
        self.bus.publish('test_event', 1)
        
        self.log_interaction("Test", "UNSUBSCRIBE", "InMemoryEventBus", "Unsubscribe handler", {"event": "test_event"})
        self.bus.unsubscribe('test_event', handler)
        
        self.log_interaction("Test", "PUBLISH", "InMemoryEventBus", "Publish 2", {"event": "test_event", "data": 2})
        self.bus.publish('test_event', 2)
        
        expected = [1]
        self.log_interaction("Test", "ASSERT", "InMemoryEventBus", "Verify calls", expect=expected, got=calls)
        self.assertEqual(calls, expected)
    
    def test_clear_subscribers(self):
        """Test clearing all subscribers for an event type."""
        calls = []
        
        def handler(data):
            self.log_interaction("Handler", "RECEIVE", "Test", "Handler called", {"data": data})
            calls.append(data)
        
        self.log_interaction("Test", "SUBSCRIBE", "InMemoryEventBus", "Subscribe handler", {"event": "test_event"})
        self.bus.subscribe('test_event', handler)
        
        self.log_interaction("Test", "CLEAR", "InMemoryEventBus", "Clear subscribers", {"event": "test_event"})
        self.bus.clear_subscribers('test_event')
        
        self.log_interaction("Test", "PUBLISH", "InMemoryEventBus", "Publish event", {"event": "test_event", "data": "data"})
        self.bus.publish('test_event', 'data')
        
        expected = []
        self.log_interaction("Test", "ASSERT", "InMemoryEventBus", "Verify calls", expect=expected, got=calls)
        self.assertEqual(calls, expected)

    def test_digest_orchestration_flow(self):
        """Demonstration of orchestration flow."""
        # Setup is already done in setUp()
        
        calls = []
        
        def subscriber_a(data):
            self.log_interaction("SubscriberA", "RECEIVE", "InMemoryEventBus", "Received event", {"data": data})
            calls.append(("A", data))
        
        def subscriber_b(data):
            self.log_interaction("SubscriberB", "RECEIVE", "InMemoryEventBus", "Received event", {"data": data})
            calls.append(("B", data))
        
        self.log_interaction("Test", "SUBSCRIBE", "InMemoryEventBus", "Subscribe A", {"event": "scan.started"})
        self.bus.subscribe('scan.started', subscriber_a)
        
        self.log_interaction("Test", "SUBSCRIBE", "InMemoryEventBus", "Subscribe B", {"event": "scan.started"})
        self.bus.subscribe('scan.started', subscriber_b)
        
        payload = {"scan_id": "demo-123", "status": "started"}
        self.log_interaction("Test", "PUBLISH", "InMemoryEventBus", "Publish scan.started", {"payload": payload})
        self.bus.publish('scan.started', payload)
        
        expected_calls = [("A", payload), ("B", payload)]
        self.log_interaction("Test", "ASSERT", "InMemoryEventBus", "Verify orchestration", expect=expected_calls, got=calls)
        self.assertEqual(calls, expected_calls)
