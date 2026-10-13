"""
View model of the "bench not calibrated" banner.

Responsibility:
- Carry, as plain text, what the banner of the motion and scan panels shows,
  so the widgets import no application or domain type.

Rationale:
- The operator who finds motion disabled must read why, which quantity is
  missing and where to enter it, instead of searching the logs.

Design:
- Frozen dataclass, built by MotionPresenter / ScanPresenter from the
  application DTOs.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MotionConversionBannerViewModel:
    visible: bool = False
    headline: str = ""
    detail: str = ""

    @property
    def text(self) -> str:
        return f"{self.headline}\n{self.detail}" if self.detail else self.headline

    @staticmethod
    def calibrated() -> "MotionConversionBannerViewModel":
        return MotionConversionBannerViewModel()

    @staticmethod
    def not_calibrated(
        motor_name: str | None, missing_quantity: str | None, where_to_enter: str | None
    ) -> "MotionConversionBannerViewModel":
        what = missing_quantity or "conversion mm/impulsion"
        who = f" du moteur « {motor_name} »" if motor_name else ""
        detail = f"À saisir : {where_to_enter}." if where_to_enter else ""
        return MotionConversionBannerViewModel(
            visible=True,
            headline=f"Banc non calibré : {what}{who} manquant(e) — mouvement et scan désactivés.",
            detail=detail,
        )
