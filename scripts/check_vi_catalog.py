"""Check the Vietnamese catalogs and registry hook without a database or fixtures."""
# ruff: noqa: E402, T201

import collections
import json
import os
import re
import sys
from pathlib import Path

import polib
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
from odoo.tools import config

config["addons_path"] = "addons,custom_addons"
from odoo.modules.module import initialize_sys_path

initialize_sys_path()
from odoo.tools.translate import CodeTranslations, code_translations, get_translation

from odoo.addons.tp_i18n_vi.models.ir_http import IrHttp

root = ROOT
failures = []
entries = 0
pattern = re.compile(r"%(?:\([A-Za-z_][A-Za-z_0-9]*\))?[sdf]|\$\{[^}]+\}")
for p in (root / "custom_addons/tp_i18n_vi/i18n").rglob("*.po"):
    po = polib.pofile(p, check_for_duplicates=True)
    for e in po:
        entries += 1
        if e.fuzzy or not e.msgstr:
            failures.append((str(p), e.msgid, "empty/fuzzy"))
        if collections.Counter(pattern.findall(e.msgid)) != collections.Counter(
            pattern.findall(e.msgstr),
        ):
            failures.append((str(p), e.msgid, "placeholders"))
for name in [
    "custom_addons/tp_admin_delegation/views/hr_profile.xml",
    "custom_addons/tp_admin_delegation/views/admin_delegation_views.xml",
    "custom_addons/tp_hr_workspace/views/identity_org.xml",
]:
    etree.parse(str(root / name))
hook = object.__new__(IrHttp)
hook._register_hook()
first = dict(code_translations.python_translations)
web_first = dict(code_translations.web_translations)
hook._register_hook()
assert (
    first == code_translations.python_translations
    and web_first == code_translations.web_translations
)
for mod in ("base", "web"):
    assert (
        get_translation(mod, "vi_VN", "The operation cannot be completed: %s", ("X",))
        == "Không thể hoàn tất thao tác: X"
    )
    assert (
        get_translation(mod, "en_US", "The operation cannot be completed: %s", ("X",))
        == "The operation cannot be completed: X"
    )
assert (
    get_translation(
        "base",
        "vi_VN",
        "Missing required field %(field_display)s for model %(model_display)s",
        {"field_display": "Lý do", "model_display": "Hồ sơ"},
    )
    == "Thiếu trường bắt buộc Lý do của Hồ sơ"
)
for mod in {module for module, _lang in code_translations.web_translations}:
    original = {
        x["id"]: x["string"]
        for x in CodeTranslations().get_web_translations(mod, "vi_VN")["messages"]
    }
    served = {
        x["id"]: x["string"]
        for x in code_translations.get_web_translations(mod, "vi_VN")["messages"]
    }
    assert all(served[k] == v for k, v in original.items() if v != k and not v.isascii()), (
        mod,
        "native overwritten",
    )
assert {
    x["id"]: x["string"]
    for x in code_translations.get_web_translations("web", "vi_VN")["messages"]
}["Developer Tools"] == "Công cụ dành cho nhà phát triển"
assert {
    x["id"]: x["string"]
    for x in code_translations.get_web_translations("mail", "vi_VN")["messages"]
}["Meetings"] == "Cuộc họp"
print(
    json.dumps(
        {
            "entries": entries,
            "failures": failures,
            "hook": "PASS idempotent/native-preserved/en_US/placeholders",
        },
    ),
)
assert not failures
