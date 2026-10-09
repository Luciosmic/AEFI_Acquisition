"""
Unit of Work Port Interface

Responsibility:
- Delimiter une transaction sur UN agregat : tout ou rien.
- Collecter les Domain Events des agregats "vus" et les publier seulement apres commit.

Rationale:
- Sans frontiere transactionnelle, les evenements sont publies a la main pendant la mutation
  (_publish_events) : un echec apres publication laisse des observateurs avec un fait qui n'a jamais ete valide.
- Regle du domaine scan : un agregat par transaction ; les autres agregats sont mis a jour par
  reaction aux evenements, dans leur propre UoW.

Design:
- Contexte `with uow:` ; rollback implicite si exception ou si commit() jamais appele.
- register(aggregate) : appele par les repositories ; l'aggregat doit exposer `domain_events`
  (propriete qui retourne puis vide la liste).
- Repositories exposes en attributs : aefi_points, scans.
"""

from abc import ABC, abstractmethod
from typing import Any

from domain.aefi_point.repositories.i_aefi_point_repository import IAefiPointRepository
from domain.scan.repositories.i_scan_repository import IScanRepository


class IUnitOfWork(ABC):
    aefi_points: IAefiPointRepository
    scans: IScanRepository

    @abstractmethod
    def __enter__(self) -> "IUnitOfWork":
        """Ouvre une transaction."""

    @abstractmethod
    def __exit__(self, exc_type, exc, tb) -> None:
        """Ferme la transaction ; rollback si exception ou commit absent. Ne supprime pas l'exception."""

    @abstractmethod
    def commit(self) -> None:
        """Valide la transaction puis publie les evenements collectes (apres fermeture de la transaction)."""

    @abstractmethod
    def register(self, aggregate: Any) -> None:
        """Enregistre un agregat vu pour collecter ses Domain Events au commit."""
