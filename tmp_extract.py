from pathlib import Path
import re

root = Path('src/osdagbridge/desktop/ui/dialogs')
text = (root / 'additional_inputs.py').read_text(encoding='utf-8')

helper_match = re.search(r"def get_combobox_style\(\):[\s\S]*?def create_action_button_bar", text)
if not helper_match:
    raise SystemExit("helper block not found")
helper_text = text[helper_match.start():helper_match.end()]
helper_text = helper_text.rsplit("\n", 1)[0]

import_block_match = re.search(r"^import sys[\s\S]+?from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar\n", text, re.MULTILINE)
if not import_block_match:
    raise SystemExit("import block not found")
imports = import_block_match.group(0)

classes = [
    ("TypicalSectionDetailsTab", Path("tabs/typical_section_details.py")),
    ("OptimizableField", Path("tabs/optimizable_field.py")),
    ("SectionPropertiesTab", Path("tabs/section_properties_tab.py")),
    ("GirderDetailsTab", Path("tabs/sub_tabs/section_properties/girder_details_tab.py")),
    ("StiffenerDetailsTab", Path("tabs/sub_tabs/section_properties/stiffener_details_tab.py")),
    ("CrossBracingDetailsTab", Path("tabs/sub_tabs/section_properties/cross_bracing_details_tab.py")),
    ("EndDiaphragmDetailsTab", Path("tabs/sub_tabs/section_properties/end_diaphragm_details_tab.py")),
    ("CustomVehicleDialog", Path("tabs/custom_vehicle_dialog.py")),
    ("LoadingTab", Path("tabs/loading_tab.py")),
]

def extract_class(name: str) -> str:
    pattern = re.compile(rf"class {name}\\b[\\s\\S]*?(?=\\nclass |\\Z)")
    m = pattern.search(text)
    if not m:
        raise SystemExit(f"class {name} not found")
    return m.group(0).rstrip() + "\n"

for class_name, relative_path in classes:
    class_body = extract_class(class_name)
    file_path = root / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    header = '"""Auto-generated tab module extracted from additional_inputs."""\n' + imports + "\n" + helper_text + "\n\n"
    file_path.write_text(header + class_body + "\n", encoding="utf-8")
    print("wrote", file_path)
