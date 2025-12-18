"""
Interactive Port Layer

Provides user interaction interfaces following ISP (Interface Segregation Principle).
Integrates with EventBus and CommandBus patterns.

Architecture:
- IInteractivePort: Base interface (ISP)
- Controllers: Specific implementations (ScanController, MotionController, etc.)
- CompositeController: Aggregates all controllers
"""

