param([Parameter(Mandatory=$true)][string]$Label)
# HR-EMPLOYEE-CODE-003: tp_organization 20.0.2.3.0 + tp_hr_attendance 20.0.3.5.5 on the PC server.
# Run on the PC after copying the committed release tarball and its manifest into .local\hr-employee-code003.
# Refuses before any change on source drift or on installed modules whose source differs from the DB. Stops Odoo,
# snapshots identities/links/attendance, backs up DB dump (+ restore list), filestore, module source and config;
# extracts the release, removes deleted files, verifies every checksum, stamps released files with the deploy time;
# upgrades both modules in a one-off container (the migration converts TP1nnnn -> TPnnn or aborts on any conflict);
# snapshots again before Odoo restarts and refuses differences outside the expected keys. Always restarts Odoo.
# Never prints credentials, password hashes or employee rows; the applied mapping stays in the private backup folder.
$ErrorActionPreference = 'Stop'
if ($Label -notmatch '^code003(-[a-z0-9]+)?$') { throw 'Invalid release label' }
$root = 'C:\Projects\TANPHAT-ONE'
$base = Join-Path $root '.local\hr-employee-code003'
$manifest = Get-Content -LiteralPath "$base\$Label-manifest.json" -Raw | ConvertFrom-Json
$addons = @('custom_addons/tp_organization/', 'custom_addons/tp_hr_attendance/')
function FileHash([string]$relative) {
    if ($relative.Contains('..') -or -not ($addons | Where-Object { $relative.StartsWith($_) })) { throw "Out of scope: $relative" }
    $target = Join-Path $root $relative
    if (-not (Test-Path -LiteralPath $target)) { return 'MISSING' }
    $content = [IO.File]::ReadAllText($target).Replace("`r`n", "`n")
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($content)))).Replace('-','').ToLower() }
    finally { $sha.Dispose() }
}
$psql = @('exec','tp-postgres','psql','-X','-v','ON_ERROR_STOP=1','-U','tp_odoo','-d','tp_tanphat_dev','-At')
# One "key=value" line per check. Aggregates only (counts and md5 of id-ordered lists): no names or hashes leave the DB.
$snapshotSql = @'
SELECT 'module:'||name||'='||coalesce(latest_version,'')||':'||state FROM ir_module_module WHERE name IN ('tp_organization','tp_hr_attendance') ORDER BY name;
SELECT 'employees='||count(*)||':'||coalesce(md5(string_agg(id::text, ',' ORDER BY id)), '-') FROM hr_employee;
SELECT 'identity='||coalesce(md5(string_agg(id||':'||coalesce(name,'')||':'||coalesce(tp_source_code,'')||':'||active||':'||company_id||':'||coalesce(sequence,0), ',' ORDER BY id)), '-') FROM hr_employee;
SELECT 'codes='||coalesce(md5(string_agg(id||':'||coalesce(tp_employee_code,''), ',' ORDER BY id)), '-') FROM hr_employee;
SELECT 'code_forms='||count(*) FILTER (WHERE tp_employee_code ~ '^TP[0-9]{3}$')||':'||count(*) FILTER (WHERE tp_employee_code ~ '^TP1[0-9]{4}$')||':'||count(*) FILTER (WHERE tp_employee_code IS NULL OR (tp_employee_code !~ '^TP[0-9]{3}$' AND tp_employee_code !~ '^TP1[0-9]{4}$')) FROM hr_employee;
SELECT 'code_duplicates='||count(*) FROM (SELECT company_id, tp_employee_code FROM hr_employee WHERE tp_employee_code IS NOT NULL GROUP BY 1, 2 HAVING count(*) > 1) d;
SELECT 'roster='||coalesce(md5(string_agg(e.id||':'||coalesce(e.user_id,0)||':'||coalesce(e.parent_id,0)||':'||coalesce(v.department_id,0)||':'||coalesce(v.job_id,0), ',' ORDER BY e.id)), '-') FROM hr_employee e LEFT JOIN hr_version v ON v.id=e.current_version_id;
SELECT 'versions='||count(*)||':'||coalesce(md5(string_agg(id||':'||employee_id||':'||coalesce(department_id,0)||':'||coalesce(job_id,0)||':'||active, ',' ORDER BY id)), '-') FROM hr_version;
SELECT 'users='||count(*)||':'||coalesce(md5(string_agg(id||':'||login||':'||coalesce(password,'')||':'||active||':'||coalesce(company_id,0), ',' ORDER BY id)), '-') FROM res_users;
SELECT 'groups='||count(*)||':'||coalesce(md5(string_agg(uid||':'||gid, ',' ORDER BY uid, gid)), '-') FROM res_groups_users_rel;
SELECT 'audit='||count(*)||':'||count(*) FILTER (WHERE action='code_correction') FROM tp_hr_employee_audit;
SELECT 'audit_max='||coalesce(max(id),0) FROM tp_hr_employee_audit;
SELECT 'audit_history='||coalesce(md5(string_agg(id||':'||action||':'||coalesce(employee_code,'')||':'||coalesce(new_code,''), ',' ORDER BY id)), '-') FROM tp_hr_employee_audit;
SELECT 'sequence='||padding||':'||prefix||':'||implementation FROM ir_sequence WHERE code='tp.hr.employee.code';
SELECT format('SELECT %L||last_value||'':''||is_called FROM %I', 'sequence_value=', 'ir_sequence_'||lpad(id::text, 3, '0')) FROM ir_sequence WHERE code='tp.hr.employee.code' \gexec
SELECT 'days='||count(*)||':'||coalesce(md5(string_agg(id||':'||employee_id||':'||work_date||':'||coalesce(in_time,'')||':'||coalesce(out_time,'')||':'||coalesce(recorded_hours,0)||':'||coalesce(units,0)||':'||units_state||':'||data_state||':'||coalesce(version,0), ',' ORDER BY id)), '-') FROM tp_hr_attendance_day;
SELECT 'day_codes='||coalesce(md5(string_agg(id||':'||coalesce(employee_code,''), ',' ORDER BY id)), '-') FROM tp_hr_attendance_day;
SELECT 'day_code_stale='||count(*) FROM tp_hr_attendance_day d JOIN hr_employee e ON e.id=d.employee_id WHERE d.employee_code IS DISTINCT FROM e.tp_employee_code;
SELECT 'sessions='||count(*)||':'||coalesce(md5(string_agg(id||':'||employee_id||':'||check_in||':'||check_out||':'||active, ',' ORDER BY id)), '-') FROM tp_hr_attendance_session;
SELECT 'corrections='||count(*)||':'||coalesce(md5(string_agg(id||':'||employee_id||':'||state, ',' ORDER BY id)), '-') FROM tp_hr_attendance_correction;
SELECT 'correction_codes='||coalesce(md5(string_agg(id||':'||coalesce(employee_code,''), ',' ORDER BY id)), '-') FROM tp_hr_attendance_correction;
SELECT 'correction_code_stale='||count(*) FROM tp_hr_attendance_correction c JOIN hr_employee e ON e.id=c.employee_id WHERE c.employee_code IS DISTINCT FROM e.tp_employee_code;
SELECT 'periods='||count(*)||':'||coalesce(md5(string_agg(id||':'||state||':'||date_from||':'||date_to, ',' ORDER BY id)), '-') FROM tp_hr_attendance_period;
SELECT 'enti_mapping='||count(*)||':'||coalesce(md5(string_agg(id||':'||key_nv||':'||coalesce(ma_nv,'')||':'||coalesce(employee_id,0)||':'||state, ',' ORDER BY id)), '-') FROM tp_hr_attendance_enti_mapping;
SELECT 'enti_days='||count(*) FROM tp_hr_attendance_enti_day;
SELECT 'source_codes='||count(*)||':'||coalesce(md5(string_agg(t::text, ',' ORDER BY t::text)), '-') FROM tp_hr_attendance_source_code t;
SELECT 'cron='||c.active||':'||c.priority||':'||c.interval_number||' '||c.interval_type FROM ir_cron c JOIN ir_model_data d ON d.res_id=c.id AND d.model='ir.cron' AND d.module='tp_hr_attendance' AND d.name='ir_cron_enti_attendance_sync';
SELECT 'base_url='||md5(value) FROM ir_config_parameter WHERE key='web.base.url';
SELECT 'employee_messages='||count(*) FROM mail_message WHERE model='hr.employee';
SELECT 'mail_queue='||count(*) FROM mail_mail;
SELECT 'notifications='||count(*) FROM mail_notification;
SELECT format(CASE WHEN EXISTS (SELECT 1 FROM pg_attribute x WHERE x.attrelid=c.conrelid AND x.attname='id' AND NOT x.attisdropped)
        THEN 'SELECT %L||count(%I)||'':''||coalesce(md5(string_agg(id||''>''||%I, '','' ORDER BY id)), ''-'') FROM %s'
        ELSE 'SELECT %L||count(%I)||'':''||coalesce(md5(string_agg(%I::text, '','' ORDER BY %I::text)), ''-'') FROM %s' END,
    'ref:'||c.conrelid::regclass::text||'.'||a.attname||'=', a.attname, a.attname,
    CASE WHEN EXISTS (SELECT 1 FROM pg_attribute x WHERE x.attrelid=c.conrelid AND x.attname='id' AND NOT x.attisdropped) THEN c.conrelid::regclass::text ELSE a.attname END,
    c.conrelid::regclass::text)
FROM pg_constraint c JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=c.conkey[1]
WHERE c.contype='f' AND c.confrelid='hr_employee'::regclass AND c.conrelid::regclass::text NOT LIKE '%wizard%'
ORDER BY c.conrelid::regclass::text, a.attname \gexec
'@
$sqlFile = "$base\$Label-snapshot.sql"
[IO.File]::WriteAllText($sqlFile, $snapshotSql.Replace("`r`n", "`n"), [Text.UTF8Encoding]::new($false))
function Snapshot([string]$name) {
    docker cp $sqlFile tp-postgres:/tmp/code003-snapshot.sql
    if ($LASTEXITCODE -ne 0) { throw 'Snapshot copy failed' }
    $lines = @(& docker @psql -f /tmp/code003-snapshot.sql)
    if ($LASTEXITCODE -ne 0) { throw "Snapshot $name failed" }
    $lines | Set-Content -LiteralPath "$base\$Label-$name.txt" -Encoding UTF8
    $map = [ordered]@{}
    foreach ($line in $lines) { $at = $line.IndexOf('='); if ($at -gt 0) { $map[$line.Substring(0, $at)] = $line.Substring($at + 1) } }
    return $map
}
$container = (docker inspect tp-odoo | ConvertFrom-Json)[0]
if (-not $container.State.Running -or $container.Config.WorkingDir -ne '/workspace') { throw 'Unexpected Odoo runtime' }
# Baseline: every touched path must still hold the previous commit's content (MISSING for new files).
foreach ($file in $manifest.baseline.PSObject.Properties) {
    if ((FileHash $file.Name) -ne $file.Value) { throw "Source drift before deploy: $($file.Name)" }
}
# -u cascades to every installed module depending on these two: each must already run the source on disk.
$installed = @{}
foreach ($row in @(& docker @psql -F '|' -c "SELECT name, latest_version FROM ir_module_module WHERE state='installed'")) {
    $parts = $row.Split('|'); $installed[$parts[0]] = $parts[1]
}
if ($LASTEXITCODE -ne 0) { throw 'Module list failed' }
foreach ($dir in Get-ChildItem -LiteralPath "$root\custom_addons" -Directory) {
    if (-not $installed.ContainsKey($dir.Name) -or $dir.Name -in @('tp_organization', 'tp_hr_attendance')) { continue }
    $text = Get-Content -LiteralPath "$($dir.FullName)\__manifest__.py" -Raw
    if ($text -notmatch "[`"']version[`"']\s*:\s*[`"']([^`"']+)[`"']") { throw "No version: $($dir.Name)" }
    $version = $Matches[1]
    if ($installed[$dir.Name] -ne $version -and -not $installed[$dir.Name].EndsWith(".$version")) {
        throw "Installed module differs from its source: $($dir.Name) $($installed[$dir.Name]) vs $version"
    }
}
$stamp = Get-Date -Format 'yyyyMMddTHHmmss'
$backup = "C:\TANPHAT-backups\hr-employee-code003\$Label-$stamp"
New-Item -ItemType Directory -Path $backup | Out-Null
docker stop tp-odoo | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Stop failed' }
$upgradeExit = -1
$stampedAt = $null
$after = $null
try {
    $before = Snapshot 'before'
    docker exec tp-postgres pg_dump -U tp_odoo -F c -f /tmp/hr-employee-code003-pre.dump tp_tanphat_dev
    if ($LASTEXITCODE -ne 0) { throw 'pg_dump failed' }
    docker exec tp-postgres pg_restore -l /tmp/hr-employee-code003-pre.dump > "$backup\restore-list.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Backup verification failed' }
    docker cp tp-postgres:/tmp/hr-employee-code003-pre.dump "$backup\tp_tanphat_dev.dump"
    if ($LASTEXITCODE -ne 0) { throw 'Backup copy failed' }
    docker exec tp-postgres rm -f /tmp/hr-employee-code003-pre.dump
    tar -czf "$backup\filestore.tar.gz" -C "$root\docker_data\filestore" tp_tanphat_dev
    if ($LASTEXITCODE -ne 0) { throw 'Filestore backup failed' }
    tar -czf "$backup\source.tar.gz" -C $root custom_addons/tp_organization custom_addons/tp_hr_attendance
    if ($LASTEXITCODE -ne 0) { throw 'Source backup failed' }
    Copy-Item -LiteralPath "$root\docker.odoo.conf", "$base\$Label-manifest.json", "$base\$Label-before.txt" -Destination $backup
    tar -xzf "$base\$Label-release.tar.gz" -C $root
    if ($LASTEXITCODE -ne 0) { throw 'Extract failed' }
    foreach ($relative in $manifest.removed) {
        if ((FileHash $relative) -ne 'MISSING') { Remove-Item -LiteralPath (Join-Path $root $relative) -Force }
    }
    foreach ($file in $manifest.release.PSObject.Properties) {
        if ((FileHash $file.Name) -ne $file.Value) { throw "Release checksum mismatch: $($file.Name)" }
    }
    # Odoo versions each CSS/JS bundle by file URL + modification time: stamp released files with the deploy time.
    $stampedAt = Get-Date
    foreach ($file in $manifest.release.PSObject.Properties) {
        (Get-Item -LiteralPath (Join-Path $root $file.Name)).LastWriteTime = $stampedAt
    }
    $argsDocker = @('run','--rm','--name','tp-code003-upgrade','--network','tanphat-one_default',
        '-v',($root+':/workspace'),'-v',($root+'\docker_data\filestore:/var/lib/odoo/filestore'),'-w','/workspace',
        $container.Config.Image,'python3','odoo-bin','-c','/workspace/docker.odoo.conf','-d','tp_tanphat_dev',
        '-u','tp_organization,tp_hr_attendance','--no-http','--stop-after-init','--max-cron-threads=0',
        "--logfile=/workspace/.local/hr-employee-code003/$Label-upgrade.log")
    $ErrorActionPreference = 'Continue'
    & docker @argsDocker *> "$base\$Label-console.log"
    $upgradeExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($upgradeExit -ne 0) { throw "Upgrade failed: $upgradeExit; backup: $backup" }
    # Snapshot before Odoo (and the ENTI cron) runs again, so only the upgrade's own changes are compared.
    $after = Snapshot 'after'
    # Existing audit history must be unchanged: compare only the rows that existed before (the upgrade appends rows).
    $history = @(& docker @psql -c "SELECT coalesce(md5(string_agg(id||':'||action||':'||coalesce(employee_code,'')||':'||coalesce(new_code,''), ',' ORDER BY id)), '-') FROM tp_hr_employee_audit WHERE id <= $([int]$before['audit_max'])")
    if ($LASTEXITCODE -ne 0) { throw 'Audit history check failed' }
    $after['audit_history'] = $history[0]
    Copy-Item -LiteralPath "$base\$Label-after.txt", "$base\$Label-upgrade.log" -Destination $backup
    # Private evidence: the applied mapping (record id, old, new) from the migration log, kept with the backup only.
    Select-String -LiteralPath "$base\$Label-upgrade.log" -Pattern 'employee id \d+: TP\d+ -> TP\d+' |
        ForEach-Object { $_.Line -replace '^.*(employee id \d+: TP\d+ -> TP\d+).*$', '$1' } |
        Set-Content -LiteralPath "$backup\mapping-applied.txt" -Encoding UTF8
} finally {
    docker start tp-odoo | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Restart failed' }
    Get-ChildItem -LiteralPath $backup -File | Where-Object { $_.Name -ne 'SHA256SUMS.json' } | ForEach-Object { [pscustomobject]@{file=$_.Name; bytes=$_.Length; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash} } | ConvertTo-Json | Set-Content -LiteralPath "$backup\SHA256SUMS.json" -Encoding UTF8
}
# Keys the conversion may change; everything else (identities, accounts, rights, links, hours, periods, ENTI) must match.
$expected = @('module:tp_organization', 'module:tp_hr_attendance', 'codes', 'code_forms', 'audit', 'audit_max', 'sequence', 'sequence_value',
    'day_codes', 'correction_codes', 'day_code_stale', 'correction_code_stale', 'employee_messages')
$unexpected = @(@($before.Keys) + @($after.Keys) | Sort-Object -Unique | Where-Object { $_ -notin $expected -and $before[$_] -ne $after[$_] })
$forms = $after['code_forms'].Split(':')
$errors = @(Select-String -CaseSensitive -LiteralPath "$base\$Label-upgrade.log" -Pattern ' (ERROR|CRITICAL) ').Count
$result = [pscustomobject]@{commit=$manifest.commit; backup=$backup; files=@($manifest.release.PSObject.Properties).Count;
    removed=@($manifest.removed).Count; upgrade_exit=$upgradeExit; log_errors=$errors; stamped_at=$stampedAt.ToString('s');
    modules=@($after['module:tp_organization'], $after['module:tp_hr_attendance']); converted=@(Get-Content -LiteralPath "$backup\mapping-applied.txt").Count;
    code_forms_before=$before['code_forms']; code_forms_after=$after['code_forms']; duplicates=$after['code_duplicates'];
    sequence_value=$after['sequence_value']; day_code_stale=@($before['day_code_stale'], $after['day_code_stale']);
    correction_code_stale=@($before['correction_code_stale'], $after['correction_code_stale']);
    mail_queue=@($before['mail_queue'], $after['mail_queue']); notifications=@($before['notifications'], $after['notifications']);
    checked_keys=@($after.Keys).Count; unexpected_diffs=$unexpected}
$result | ConvertTo-Json | Set-Content -LiteralPath "$base\$Label-result.json" -Encoding UTF8
Copy-Item -LiteralPath "$base\$Label-result.json" -Destination $backup
Get-Content -LiteralPath "$base\$Label-result.json"
if ($errors -gt 0) { throw 'Upgrade logged errors: inspect before accepting' }
if ($unexpected.Count -gt 0) { throw "Unexpected differences: $($unexpected -join ', ')" }
if ($forms[1] -ne '0' -or $forms[2] -ne '0' -or $after['code_duplicates'] -ne '0') { throw 'Codes outside TP001-TP999 remain' }
if ($after['day_code_stale'] -ne '0' -or $after['correction_code_stale'] -ne '0') { throw 'Attendance code copies were not refreshed' }
