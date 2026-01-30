"""About dialog for TNC Map Helper application"""

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from application import __version__

if TYPE_CHECKING:
    from application.database.database_operations import Database


class AboutDialog(QDialog):
    """Dialog showing application information and links"""

    def __init__(self, database: "Database", parent=None):
        super().__init__(parent)
        self.database = database
        self.setWindowTitle("About T&C Map Helper")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title and version
        title_label = QLabel(f"T&C Map Helper v {__version__}")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Get database version from database
        db_version = self.database.get_db_version()
        db_version_label = QLabel(f"Database Content Version: {db_version}")
        db_version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(db_version_label)
        
        layout.addSpacing(10)
        
        # Links section
        links_label = QLabel("Links:")
        links_font = links_label.font()
        links_font.setBold(True)
        links_label.setFont(links_font)
        layout.addWidget(links_label)
        
        # Documentation link
        general_info_btn = QPushButton("Documentation")
        general_info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        general_info_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://atlassian.spscommerce.com/wiki/spaces/~vkovalchuk@spscommerce.com/pages/729384074/General+Information")
            )
        )
        layout.addWidget(general_info_btn)
        
        # Bugs and Ideas link
        bugs_ideas_btn = QPushButton("Bugs and Ideas for Improvements")
        bugs_ideas_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bugs_ideas_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://atlassian.spscommerce.com/wiki/spaces/~vkovalchuk@spscommerce.com/pages/729384076/Bugs+and+Ideas+for+Improvements")
            )
        )
        layout.addWidget(bugs_ideas_btn)
        
        # Slack channel link
        slack_btn = QPushButton("Slack Channel")
        slack_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        slack_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://spscommerce.enterprise.slack.com/archives/C0A9VCU3WBG")
            )
        )
        layout.addWidget(slack_btn)
        
        layout.addSpacing(10)
        
        # Contact section
        contact_label = QLabel("Contact author:")
        contact_font = contact_label.font()
        contact_font.setBold(True)
        contact_label.setFont(contact_font)
        layout.addWidget(contact_label)
        
        email_btn = QPushButton("vkovalchuk@spscommerce.com")
        email_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        email_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("mailto:vkovalchuk@spscommerce.com"))
        )
        layout.addWidget(email_btn)
        
        layout.addStretch()
        
        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
