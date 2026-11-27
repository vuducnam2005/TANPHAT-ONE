{
    "name": "TANPHAT ONE — Tài khoản ngân hàng cá nhân",
    "summary": "Danh mục ngân hàng chuẩn NAPAS/VietQR và tự khai báo tài khoản nhận lương trong Thông tin cá nhân",
    "version": "20.0.1.1.1",
    "license": "LGPL-3",
    "author": "Tan Phat JSC",
    "depends": ["tp_hr_workspace", "tp_admin_delegation"],
    "data": [
        "security/ir.access.csv",
        "data/tp_bank_data.xml",
        "views/tp_bank_views.xml",
        "views/res_partner_bank_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "tp_hr_bank/static/src/bank_picker.js",
            "tp_hr_bank/static/src/bank_picker.xml",
            "tp_hr_bank/static/src/bank_field.js",
            "tp_hr_bank/static/src/bank_field.xml",
            "tp_hr_bank/static/src/my_profile_bank.js",
            "tp_hr_bank/static/src/my_profile_bank.xml",
            "tp_hr_bank/static/src/bank.scss",
        ],
    },
    "installable": True,
    "application": False,
}
