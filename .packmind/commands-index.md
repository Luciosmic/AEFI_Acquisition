# Packmind Commands Index

This file contains all available coding commands that can be used by AI agents (like Cursor, Claude Code, GitHub Copilot) to find and use proven patterns in coding tasks.

## Available Commands

- [Create application service](commands/create-application-service.md) : Scaffold a new DDD-style application service with constructor-injected ports, tests, and composition-root wiring to orchestrate hardware capabilities cleanly and keep infrastructure decoupled when adding new use-cases or extracting orchestration logic from presenters/adapters.
- [Create domain event](commands/create-domain-event.md) : Scaffold and publish a new domain event dataclass in the appropriate `src/domain/events/*_events.py` file to standardize cross-layer communication and ensure downstream consumers have all required state-change data when aggregates transition or new hardware lifecycle events are introduced.
- [Create port interface](commands/create-port-interface.md) : Scaffold a new ABC port interface (and mock adapter) to abstract hardware/infrastructure dependencies so services can be dependency-injected and tested without real devices when adding a new adapter, extracting a hard dependency, or defining a new output contract.
- [Create presenter](commands/create-presenter.md) : Scaffold a Qt presenter that implements an application service output port and exposes signals/slots to bridge the service and view so you can cleanly wire new UI panels while keeping business logic and UI event handling decoupled when adding features to the dashboard.
- [Document an Atomic Functionality (FA) from an intention](commands/document-an-atomic-functionality-fa-from-an-intention.md) : Guide pas-à-pas pour extraire une fonctionnalité atomique (mono/di/N-atomique) depuis une intention utilisateur, tracer ses sources, tisser le graphe, puis la projeter en Promise Model et en DDD (code_interface).
- [Pre pr quality check](commands/pre-pr-quality-check.md) : Run chained local checks (black, flake8, mypy, and pytest via `uv run`) in the correct order to catch formatting, lint, type, and test failures early and avoid blocked PR reviews before opening a pull request to `develop` or `main`.
- [Seed Graph of Intentions (folder scaffold)](commands/seed-graph-of-intentions-folder-scaffold.md) : Crée la graine du dépôt `graph_of_intentions/` (thoughts_interface, promise_model, code_interface) avec la structure minimale et des placeholders pour démarrer la cristallisation.


---

*This file was automatically generated from deployed command versions.*