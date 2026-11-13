"""
Asynchronous Task Runner Port

Responsibility:
- Provide the Application layer with a way to run a callable in the background
  without knowing anything about the underlying concurrency mechanism.

Rationale:
- Hexagonal architecture / outbound port.
- Decouples application use-case loops (scan step loop, EF probe streaming loop)
  from the infrastructure choice of threading, asyncio, multiprocessing, or
  a remote task queue.
- Shared across multiple application services (scan, EF probe) because the
  cause of change (how we run background work) is orthogonal to any given
  service's business rules.

Design:
- Fire-and-forget submit returning a lightweight TaskHandle for optional wait.
- Cancellation is out of scope: the callable itself must observe a cooperative
  stop signal owned by the application service. This keeps the port free of
  cancellation semantics that would leak infra concerns (thread interrupt,
  future.cancel, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Optional


class TaskHandle(ABC):
    """
    Opaque handle representing a task submitted to an IAsyncTaskRunner.

    Only exposes the operations the Application layer legitimately needs:
    ask whether the task is still running, and block until it completes.
    """

    @abstractmethod
    def is_running(self) -> bool:
        """Return True as long as the submitted callable has not returned."""

    @abstractmethod
    def wait(self, timeout: Optional[float] = None) -> None:
        """
        Block until the submitted callable returns, or until timeout elapses.

        A timeout of None means wait forever.
        """


class IAsyncTaskRunner(ABC):
    """
    Port for running a callable in the background.

    The callable is expected to be self-contained: it captures its own
    dependencies via closure and reports its own outcome through side effects
    (domain event bus, application state, aggregate mutations).

    The runner MUST NOT wrap the callable in any error-handling logic that
    would swallow exceptions — programmer errors must remain visible.

    Responsibility:
        - `IAsyncTaskRunner.submit(callable) -> TaskHandle` : soumet une callable pour exécution en tâche de fond, retour immédiat.
        - `TaskHandle.is_running()` : indique si la callable est encore active.
        - `TaskHandle.wait(timeout)` : bloque jusqu'à la fin de la callable ou expiration du timeout.

    Rationale:
        Les application services (`ScanApplicationService`, `ElectricFieldProbeService`) ont besoin de lancer une boucle en tâche de fond sans dépendre du mécanisme de concurrence (threading, asyncio, pool distant). Le port isole cette responsabilité d'infra derrière une interface stable.

        Ce port est placé dans `application/shared/ports/` car il est consommé par plusieurs services et sa cause de changement (choix du mécanisme de concurrence) est orthogonale à chaque use case. Cf. `standard-solidai-shared-domain-concept-extraction` appliqué au niveau application.

    Design:
        - Fire-and-forget. La callable est autonome : elle capture ses dépendances via closure et rapporte son résultat via le bus d'events domain ou des mutations d'agrégat.
        - **Aucune sémantique d'annulation** dans le port : l'annulation est un concept application (l'agrégat `StepScan.cancel()` ou un `threading.Event` de stream possédé par le service). Introduire `cancel()` dans le port ferait fuiter des concepts infra (thread interrupt, `Future.cancel`).
        - Le runner ne wrappe pas la callable dans un try/except — les erreurs programmeur restent visibles.
        - L'implémentation par défaut (`ThreadPoolTaskRunner`) utilise `threading.Thread(daemon=True)` ; un Fake synchrone existe pour les tests.
    """

    @abstractmethod
    def submit(self, task: Callable[[], None]) -> TaskHandle:
        """
        Submit the callable for background execution and return immediately.

        The returned TaskHandle can be used to observe or await completion.
        """
