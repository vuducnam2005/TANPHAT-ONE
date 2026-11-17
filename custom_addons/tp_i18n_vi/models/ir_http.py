"""Fill missing server messages without changing upstream translation files."""

from collections import defaultdict
from pathlib import Path

from odoo import models
from odoo.tools import frozendict
from odoo.tools.misc import file_open, file_path
from odoo.tools.translate import code_translations, translation_file_reader


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def _register_hook(self):
        super()._register_hook()
        # Python errors use the originating module's catalog, unlike client _t.
        # Preserve native Vietnamese; fill missing or still-English entries.
        additions = defaultdict(dict)
        with file_open("tp_i18n_vi/i18n/server_vi.po", "rb") as stream:
            for row in translation_file_reader(stream, fileformat="po"):
                if row.get("type") == "code" and row.get("value"):
                    additions[row["module"]][row["src"]] = row["value"]
        for lang in ("vi", "vi_VN"):
            for module, terms in additions.items():
                native = code_translations.get_python_translations(module, lang)
                code_translations.python_translations[module, lang] = frozendict(
                    terms | dict(native),
                )
            for catalog in sorted(
                Path(file_path("tp_i18n_vi/i18n/supplements")).glob("*.po"),
            ):
                module = catalog.stem
                python_terms = dict(code_translations.get_python_translations(module, lang))
                native = {
                    row["id"]: row["string"]
                    for row in code_translations.get_web_translations(module, lang)[
                        "messages"
                    ]
                }
                with catalog.open("rb") as stream:
                    for row in translation_file_reader(stream, fileformat="po"):
                        if row.get('type') != 'code' or not row.get('value'):
                            continue
                        targets = []
                        if 'odoo-python' in row['comments']:
                            targets.append(python_terms)
                        if 'odoo-javascript' in row['comments']:
                            targets.append(native)
                        for target in targets:
                            current = target.get(row['src'], row['src'])
                            if current == row['src'] or current.isascii():
                                target[row['src']] = row['value']
                code_translations.python_translations[module, lang] = frozendict(python_terms)
                code_translations.web_translations[module, lang] = frozendict(
                    {
                        "messages": tuple(
                            frozendict({"id": source, "string": value})
                            for source, value in native.items()
                        ),
                    },
                )
