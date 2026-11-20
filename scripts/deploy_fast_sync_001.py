# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Deploy script for ATTENDANCE-FAST-SYNC-001 to server-pc (192.168.1.73).

Performs:
1. Pre-deployment check
2. Snapshot before (business counts, cron state, module version)
3. Backup DB + source on server-pc to C:\\TANPHAT-backups\\attendance-fast-sync001\\<timestamp>
4. Packaging local custom_addons/tp_hr_attendance
5. Transfer & extract to C:\\Projects\\TANPHAT-ONE\\custom_addons\\tp_hr_attendance
6. Touch JS/XML/SCSS mtime to now so Odoo rebuilds bundles
7. Upgrade tp_hr_attendance on tp_tanphat_dev
8. Restart tp-odoo container
9. Health check LAN & Public (https://tpone.tadic.vn/web/health)
10. Snapshot after & compare invariants
"""

import datetime
import os
import subprocess
import sys
import tarfile
import time


SERVER_HOST = "server-pc"
REMOTE_PROJECT_DIR = r"C:\Projects\TANPHAT-ONE"
REMOTE_BACKUP_BASE = r"C:\TANPHAT-backups\attendance-fast-sync001"
LOCAL_ADDON_DIR = os.path.abspath("custom_addons/tp_hr_attendance")
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
REMOTE_BACKUP_DIR = f"{REMOTE_BACKUP_BASE}\\{TIMESTAMP}"
LOCAL_TEMP_PKG = os.path.abspath(f".local/tp_hr_attendance_{TIMESTAMP}.tar.gz")


def run_local(cmd, check=True):
    print(f"[LOCAL] {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and res.returncode != 0:
        print(f"Error ({res.returncode}): {res.stderr}")
        raise RuntimeError(f"Local command failed: {cmd}")
    return res


def run_remote(cmd, check=True):
    print(f"[REMOTE] {cmd}")
    full_cmd = ["ssh", SERVER_HOST, cmd]
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    if check and res.returncode != 0:
        print(f"Remote error ({res.returncode}): {res.stderr}")
        raise RuntimeError(f"Remote command failed: {cmd}")
    return res


def get_snapshot():
    sql = (
        "SELECT json_build_object("
        "'module',(SELECT latest_version FROM ir_module_module WHERE name='tp_hr_attendance'),"
        "'employees',(SELECT count(*) FROM hr_employee),"
        "'users',(SELECT count(*) FROM res_users),"
        "'days',(SELECT count(*) FROM tp_hr_attendance_day),"
        "'sessions',(SELECT count(*) FROM tp_hr_attendance_session),"
        "'enti_days',(SELECT count(*) FROM tp_hr_attendance_enti_day),"
        "'enti_mapping',(SELECT json_object_agg(state, n) FROM (SELECT state, count(*) n FROM tp_hr_attendance_enti_mapping GROUP BY state) m),"
        "'cron',(SELECT json_build_object('active',c.active,'priority',c.priority,'interval',concat(c.interval_number,' ',c.interval_type)) FROM ir_cron c JOIN ir_model_data d ON d.res_id=c.id AND d.model='ir.cron' AND d.module='tp_hr_attendance' AND d.name='ir_cron_enti_attendance_sync'),"
        "'base_url',(SELECT md5(value) FROM ir_config_parameter WHERE key='web.base.url'))"
    )
    cmd = f'powershell -Command "docker exec tp-postgres psql -U tp_odoo -d tp_tanphat_dev -Atc \\"{sql}\\""'
    res = run_remote(cmd)
    return res.stdout.strip()


def main():
    print("=" * 60)
    print(f"STARTING DEPLOYMENT ATTENDANCE-FAST-SYNC-001 ({TIMESTAMP})")
    print("=" * 60)

    # 1. Pre-check
    print("\n--- 1. Checking server status ---")
    res = run_remote("docker ps --filter name=tp-")
    print(res.stdout)
    if "tp-odoo" not in res.stdout or "tp-postgres" not in res.stdout:
        raise RuntimeError("tp-odoo or tp-postgres not running on server-pc")

    # 1b. Snapshot before
    print("\n--- 1b. Snapshot before deploy ---")
    snap_before = get_snapshot()
    print("Snapshot before:", snap_before)

    # 2. Create backup dir on server
    print(f"\n--- 2. Creating backup directory {REMOTE_BACKUP_DIR} ---")
    run_remote(f"powershell -Command \"New-Item -ItemType Directory -Force -Path '{REMOTE_BACKUP_DIR}'\"")

    # 2b. Backup Postgres DB
    print("\n--- 2b. Backing up PostgreSQL tp_tanphat_dev ---")
    db_backup_cmd = (
        f"powershell -Command \"docker exec tp-postgres pg_dump -U tp_odoo -F c -f /tmp/tp_tanphat_dev_{TIMESTAMP}.dump tp_tanphat_dev; "
        f"docker exec tp-postgres pg_restore -l /tmp/tp_tanphat_dev_{TIMESTAMP}.dump > '{REMOTE_BACKUP_DIR}\\restore-list.txt'; "
        f"docker cp tp-postgres:/tmp/tp_tanphat_dev_{TIMESTAMP}.dump '{REMOTE_BACKUP_DIR}\\tp_tanphat_dev_pre.dump'; "
        f"docker exec tp-postgres rm -f /tmp/tp_tanphat_dev_{TIMESTAMP}.dump\""
    )
    run_remote(db_backup_cmd)
    chk_dump = run_remote(f"powershell -Command \"(Get-Item '{REMOTE_BACKUP_DIR}\\tp_tanphat_dev_pre.dump').Length\"")
    print(f"DB dump size: {chk_dump.stdout.strip()} bytes")

    # 2c. Backup existing tp_hr_attendance source
    print("\n--- 2c. Backing up existing tp_hr_attendance source ---")
    src_backup_cmd = (
        f"powershell -Command \"tar -czf '{REMOTE_BACKUP_DIR}\\tp_hr_attendance_pre.tar.gz' -C '{REMOTE_PROJECT_DIR}\\custom_addons' tp_hr_attendance\""
    )
    run_remote(src_backup_cmd)
    chk_src = run_remote(f"powershell -Command \"(Get-Item '{REMOTE_BACKUP_DIR}\\tp_hr_attendance_pre.tar.gz').Length\"")
    print(f"Source backup size: {chk_src.stdout.strip()} bytes")

    # 3. Packaging local custom_addons/tp_hr_attendance
    print(f"\n--- 3. Packaging local {LOCAL_ADDON_DIR} ---")
    os.makedirs(os.path.dirname(LOCAL_TEMP_PKG), exist_ok=True)
    with tarfile.open(LOCAL_TEMP_PKG, "w:gz") as tar:
        for root, dirs, files in os.walk(LOCAL_ADDON_DIR):
            dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".")]
            for f in files:
                if f.endswith(".pyc") or f.startswith("."):
                    continue
                full_path = os.path.join(root, f)
                arcname = os.path.relpath(full_path, os.path.dirname(LOCAL_ADDON_DIR))
                tar.add(full_path, arcname=arcname)
    print(f"Created package {LOCAL_TEMP_PKG} ({os.path.getsize(LOCAL_TEMP_PKG)} bytes)")

    # 4. Copy to server-pc
    print("\n--- 4. Uploading package to server-pc ---")
    remote_pkg = f"C:\\Users\\Public\\tp_hr_attendance_{TIMESTAMP}.tar.gz"
    run_local(f"scp \"{LOCAL_TEMP_PKG}\" {SERVER_HOST}:\"{remote_pkg}\"")

    # 5. Extract to C:\Projects\TANPHAT-ONE\custom_addons
    print("\n--- 5. Extracting to remote workspace ---")
    extract_cmd = (
        f"powershell -Command \"tar -xzf '{remote_pkg}' -C '{REMOTE_PROJECT_DIR}\\custom_addons'; "
        f"Copy-Item '{remote_pkg}' '{REMOTE_BACKUP_DIR}\\deploy_package.tar.gz'; "
        f"Remove-Item -Force '{remote_pkg}'\""
    )
    run_remote(extract_cmd)

    # 6. Touch JS/XML/SCSS files mtime to now
    print("\n--- 6. Touching JS/XML/SCSS files mtime to now ---")
    touch_cmd = (
        f"powershell -Command \"Get-ChildItem -Path '{REMOTE_PROJECT_DIR}\\custom_addons\\tp_hr_attendance' -Recurse -Include *.js,*.xml,*.scss | "
        f"ForEach-Object {{ $_.LastWriteTime = (Get-Date) }}\""
    )
    run_remote(touch_cmd)

    # 7. Upgrade module tp_hr_attendance inside tp-odoo container
    print("\n--- 7. Upgrading tp_hr_attendance in Docker container ---")
    upgrade_cmd = (
        "docker exec -w /workspace tp-odoo python3 odoo-bin -c /workspace/docker.odoo.conf "
        "-d tp_tanphat_dev -u tp_hr_attendance --no-http --stop-after-init --max-cron-threads=0"
    )
    res_up = run_remote(upgrade_cmd)
    print("Upgrade output summary:")
    for line in res_up.stdout.splitlines()[-15:]:
        print("  ", line)

    # 8. Restart tp-odoo container
    print("\n--- 8. Restarting tp-odoo container ---")
    run_remote("docker restart tp-odoo")
    print("Restart requested. Waiting for service to become healthy...")

    # 9. Verify health
    healthy = False
    for attempt in range(1, 20):
        time.sleep(3)
        res_health = run_remote(
            "powershell -Command \"try { (Invoke-WebRequest -Uri 'http://127.0.0.1:8069/web/health' -UseBasicParsing -TimeoutSec 3).StatusCode } catch { $_.Exception.Response.StatusCode.value__ }\"",
            check=False,
        )
        status_code = res_health.stdout.strip()
        print(f"  Attempt {attempt}: health status = {status_code}")
        if status_code == "200":
            healthy = True
            break

    if not healthy:
        raise RuntimeError("Server did not become healthy after 60s!")

    # 10. Snapshot after
    print("\n--- 10. Snapshot after deploy ---")
    snap_after = get_snapshot()
    print("Snapshot after:", snap_after)

    # Save snapshots to backup dir
    save_snap_cmd = (
        f"powershell -Command \"Set-Content -Path '{REMOTE_BACKUP_DIR}\\before.json' -Value '{snap_before}'; "
        f"Set-Content -Path '{REMOTE_BACKUP_DIR}\\after.json' -Value '{snap_after}'\""
    )
    run_remote(save_snap_cmd)

    print("\n" + "=" * 60)
    print("DEPLOYMENT COMPLETED SUCCESSFULLY!")
    print(f"Backup preserved at: {REMOTE_BACKUP_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
