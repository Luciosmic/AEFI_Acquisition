"""Export comment input (see export_comment_input_intention.md)."""

from PySide6.QtWidgets import QLineEdit

COMMENT_LABEL = "Commentaire:"
COMMENT_TOOLTIP = (
    "Écrit dans le fichier de paramètres de l'export (provenance.activity.operator_comment),\n"
    "jamais dans le nom des fichiers : celui-ci vient de l'objet mesuré et du lift-off."
)


class ExportCommentInput(QLineEdit):
    """Free text written in acquisition-parameters.json; empty = no comment."""

    def __init__(self, placeholder: str = "ex. scan de fond, sonde déplacée…", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setToolTip(COMMENT_TOOLTIP)

    def comment(self) -> str:
        return self.text().strip()
