from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QWidget,
    QCheckBox,
    QDialogButtonBox,
    QPushButton,
)
from core.config_manager import ConfigManager  #[cite: 6]


class SponsorBlockDialog(QDialog):

  def __init__(self, config_mgr: ConfigManager, parent=None):
    super().__init__(parent)
    self.config_mgr = config_mgr  # ConfigManager ကို လက်ခံသိမ်းဆည်းခြင်း
    self.setWindowTitle("SponsorBlock Categories")
    self.resize(550, 520)

    # Main layout
    main_layout = QVBoxLayout(self)

    # Title and description
    title_label = QLabel("SponsorBlock Categories")
    title_font = title_label.font()
    title_font.setPointSize(14)
    title_font.setBold(True)
    title_label.setFont(title_font)

    desc_label = QLabel(
        "Select which types of video segments to automatically remove during"
        " download.\nSponsorBlock uses community-submitted data to identify"
        " these segments."
    )
    desc_label.setWordWrap(True)

    main_layout.addWidget(title_label)
    main_layout.addWidget(desc_label)

    # Scroll Area for categories
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_content = QWidget()
    scroll_layout = QVBoxLayout(scroll_content)

    # Categories list နှင့် Internal Key များကို သတ်မှတ်ခြင်း (Config တွင် သိမ်းရန်အတွက်)
    # (Title, Description, Config Key, Default Value) စသဖြင့်
    self.categories = [
        (
            "Sponsor",
            "Paid promotion, paid referrals and direct advertisements",
            "sponsorblock_sponsor",
            True,
        ),
        (
            "Unpaid/Self Promotion",
            "Unpaid promotion of creators' own content",
            "sponsorblock_selfpromo",
            True,
        ),
        (
            "Interaction Reminder",
            "Asking viewers to like, subscribe, or follow social media",
            "sponsorblock_interaction",
            True,
        ),
        (
            "Intro",
            "Video introduction that can be skipped",
            "sponsorblock_intro",
            False,
        ),
        (
            "Outro/End Cards",
            "Credits or when the video ends",
            "sponsorblock_outro",
            False,
        ),
        (
            "Preview/Recap",
            "Quick recap of previous videos or preview of what's coming up",
            "sponsorblock_preview",
            False,
        ),
        (
            "Non-Music Section",
            "For only music videos. Marks non-music sections",
            "sponsorblock_nonmusic",
            False,
        ),
        (
            "Filler Tangent",
            "Tangential scenes added only for filler or humor",
            "sponsorblock_filler",
            False,
        ),
    ]

    self.checkboxes = []
    for title, desc, config_key, default_checked in self.categories:
      item_widget = QWidget()
      item_layout = QVBoxLayout(item_widget)
      item_layout.setContentsMargins(0, 6, 0, 6)

      checkbox = QCheckBox(title)
      
      # Config က တန်ဖိုးဖတ်ပြီး Checkbox အနေအထား သတ်မှတ်
      is_checked = self.load_config_skip_sponsors_block_value(config_key, default_checked)
      checkbox.setChecked(is_checked)

      font = checkbox.font()
      font.setBold(True)
      checkbox.setFont(font)

      desc_lbl = QLabel(desc)
      desc_lbl.setStyleSheet("color: #777777; margin-left: 20px; font-weight = normal; font-size = normal;")
      desc_lbl.setWordWrap(True)

      item_layout.addWidget(checkbox)
      item_layout.addWidget(desc_lbl)

      scroll_layout.addWidget(item_widget)
      # Checkbox နဲ့ သူတို့ရဲ့ config_key တွေကို သိမ်းထား
      self.checkboxes.append((checkbox, config_key, default_checked))

    scroll_layout.addStretch()
    scroll_area.setWidget(scroll_content)
    main_layout.addWidget(scroll_area)

    # Action buttons layout (Select Defaults, Select All, Deselect All)
    action_layout = QHBoxLayout()
    self.btn_defaults = QPushButton("Select Defaults")
    self.btn_all = QPushButton("Select All")
    self.btn_deselect = QPushButton("Deselect All")
    
    # Button အရွယ်အစားကို အရမ်းမကြီးစေရန် Button Style ထည့်
    button_style = (
        "QPushButton { padding: 4px 10px; font-size: 10pt; min-height: 20px; }"
    )
    self.btn_defaults.setStyleSheet(button_style)
    self.btn_all.setStyleSheet(button_style)
    self.btn_deselect.setStyleSheet(button_style)

    action_layout.addWidget(self.btn_defaults)
    action_layout.addWidget(self.btn_all)
    action_layout.addWidget(self.btn_deselect)
    action_layout.addStretch()

    main_layout.addLayout(action_layout)

    # Bottom OK and Cancel Buttons
    dialog_buttons = QDialogButtonBox(
        QDialogButtonBox.Ok | QDialogButtonBox.Cancel
    )
    
    # OK နှိပ်ရင် config ထဲသို့ သိမ်းဆည်းရန် function ကို ချိတ်ဆက်
    dialog_buttons.accepted.connect(self.save_config_and_accept)
    dialog_buttons.rejected.connect(self.reject)

    # Custom styling for OK button (Red color as shown in video)
    ok_button = dialog_buttons.button(QDialogButtonBox.Ok)
    ok_button.setStyleSheet("""
        QPushButton {
            background-color: #0060FF;
            color: white;
            font-weight: normal;
            padding: 5px 15px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #00A1FD; /* Hover လုပ်ချိန် ပြောင်းလဲချင်သော အရောင် */
        }
        QPushButton:pressed {
            background-color: #2FB0F9; /* ခလုတ်နှိပ်လိုက်ချိန် (Pressed) အရောင် */
        }
    """)


    cancel_button = dialog_buttons.button(QDialogButtonBox.Cancel)
    cancel_button.setStyleSheet("padding: 5px 15px;")

    main_layout.addWidget(dialog_buttons)

    # Connect signals for selection buttons
    self.btn_defaults.clicked.connect(self.select_defaults)
    self.btn_all.clicked.connect(self.select_all)
    self.btn_deselect.clicked.connect(self.deselect_all)

  def load_config_skip_sponsors_block_value(self, config_key: str, default_val: bool) -> bool:
    """Config မှ SponsorBlock category တစ်ခုချင်းစီ၏ တန်ဖိုးကို ဖတ်ရန်"""
    if self.config_mgr:
      return self.config_mgr.get(config_key, default_val)
    return default_val

  def save_config_and_accept(self):
    """ OK နှိပ်လိုက်ချိန်တွင် Check လုပ်ထားသည်များကို Config ထဲသို့ သိမ်းဆည်းမည် """
    if self.config_mgr:
      updated_settings = {}
      for checkbox, config_key, _ in self.checkboxes:
        updated_settings[config_key] = checkbox.isChecked()
      
      # ConfigManager ၏ bulk update ကို အသုံးပြု၍ သိမ်းဆည်းခြင်း[cite: 6]
      self.config_mgr.update_multiple(updated_settings)

    self.accept()

  def get_checked_categories(self):
    """Checkbox တစ်ခုချင်းစီ၏ အမည်နှင့် Object ကို ပြန်ပေးရန်"""
    results = []
    for i, (title, desc, _, _) in enumerate(self.categories):
      checkbox = self.checkboxes[i][0]
      results.append((title, checkbox))
    return results

  def select_defaults(self):
    """Default Items များကိုသာ checked ရန်"""
    for checkbox, _, default_val in self.checkboxes:
      checkbox.setChecked(default_val)

  def select_all(self):
    """Item များအားလုံးကို checked ရန်"""
    for checkbox, _, _ in self.checkboxes:
      checkbox.setChecked(True)

  def deselect_all(self):
    """Items များအားလုံးကို Unchecked လုပ်ရန်"""
    for checkbox, _, _ in self.checkboxes:
      checkbox.setChecked(False)