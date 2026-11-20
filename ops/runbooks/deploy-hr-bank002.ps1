param([Parameter(Mandatory=$true)][string]$Label)
# BANK-002 + HR-SELF-EDIT-001: upgrade tp_hr_bank to 20.0.1.1.0 on the PC server (bank accounts usable on save,
# no HR verification; the migration marks earlier self-declared accounts usable) and ship the in-place own-profile
# editing (tp_admin_delegation/models/hr_profile.py, Python only; tp_hr_workspace employee_profile.js, static).
# Run on the PC after copying the committed release tarball and its manifest into .local\hr-bank002.
# Refuses before any change on source drift (released paths and the files they build on) or when tp_hr_bank is not
# installed at 20.0.1.0.0. Stops Odoo, snapshots, backs up DB dump (+ restore list), filestore, touched source and
# config; extracts the release, verifies every checksum, stamps released files with the deploy time; upgrades only
# tp_hr_bank in a one-off container; snapshots again before Odoo restarts and refuses differences outside the
# expected keys (bank account fields other than allow_out_payment must not change). Always restarts Odoo.
# Prints aggregates only: no account numbers, names, logins or password hashes leave the DB.
$ErrorActionPreference = 'Stop'
if ($Label -notmatch '^bank002(-[a-z0-9]+)?$') { throw 'Invalid release label' }
$root = 'C:\Projects\TANPHAT-ONE'
$base = Join-Path $root '.local\hr-bank002'
$manifest = Get-Content -LiteralPath "$base\$Label-manifest.json" -Raw | ConvertFrom-Json
$scope = @('custom_addons/tp_hr_bank/', 'custom_addons/tp_admin_delegation/', 'custom_addons/tp_hr_workspace/')
function FileHash([string]$relative) {
    if ($relative.Contains('..') -or -not ($scope | Where-Object { $relative.StartsWith($_) })) { throw "Out of scope: $relative" }
    $target = Join-Path $root $relative
    if (-not (Test-Path -LiteralPath $target)) { return 'MISSING' }
    $content = [IO.File]::ReadAllText($target).Replace("`r`n", "`n")
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($content)))).Replace('-','').ToLower() }
    finally { $sha.Dispose() }
}
$psql = @('exec','tp-postgres','psql','-X','-v','ON_ERROR_STOP=1','-U','tp_odoo','-d','tp_tanphat_dev','-At')
# One "key=value" line per check: counts and md5 of id-ordered lists only.
$snapshotSql = @'
SELECT 'module:'||name||'='||coalesce(latest_version,'')||':'||state FROM ir_module_module WHERE name IN ('tp_hr_bank','tp_hr_workspace','tp_admin_delegation') ORDER BY name;
SELECT 'modules_installed='||count(*)||':'||md5(string_agg(name||':'||coalesce(latest_version,''), ',' ORDER BY name)) FROM ir_module_module WHERE state='installed' AND name<>'tp_hr_bank';
SELECT 'employees='||count(*)||':'||coalesce(md5(string_agg(id||':'||coalesce(name,'')||':'||coalesce(user_id,0)||':'||coalesce(work_contact_id,0)||':'||active||':'||company_id, ',' ORDER BY id)), '-') FROM hr_employee;
SELECT 'employee_salary='||coalesce(md5(string_agg(id||':'||coalesce(salary_distribution::text,''), ',' ORDER BY id)), '-') FROM hr_employee;
SELECT 'bank_accounts='||count(*)||':'||coalesce(md5(string_agg(id||':'||partner_id||':'||coalesce(sanitized_account_number,'')||':'||coalesce(bank_name,'')||':'||coalesce(bank_bic,'')||':'||coalesce(holder_name,'')||':'||active||':'||coalesce(allow_out_payment,false)||':'||coalesce(company_id,0), ',' ORDER BY id)), '-') FROM res_partner_bank;
SELECT 'bank_accounts_except_trust='||count(*)||':'||coalesce(md5(string_agg(id||':'||partner_id||':'||coalesce(sanitized_account_number,'')||':'||coalesce(bank_name,'')||':'||coalesce(bank_bic,'')||':'||coalesce(holder_name,'')||':'||active||':'||coalesce(tp_bank_id,0)||':'||coalesce(company_id,0), ',' ORDER BY id)), '-') FROM res_partner_bank;
SELECT 'bank_trust='||count(*) FILTER (WHERE active)||':'||count(*) FILTER (WHERE active AND allow_out_payment)||':'||count(*) FILTER (WHERE active AND NOT coalesce(allow_out_payment,false) AND tp_bank_id IS NOT NULL) FROM res_partner_bank;
SELECT 'employee_bank_links='||count(*)||':'||coalesce(md5(string_agg(employee_id||'>'||bank_account_id, ',' ORDER BY employee_id, bank_account_id)), '-') FROM employee_bank_account_rel;
SELECT 'users='||count(*)||':'||coalesce(md5(string_agg(id||':'||login||':'||coalesce(password,'')||':'||active||':'||coalesce(company_id,0)||':'||partner_id, ',' ORDER BY id)), '-') FROM res_users;
SELECT 'groups='||count(*)||':'||coalesce(md5(string_agg(uid||':'||gid, ',' ORDER BY uid, gid)), '-') FROM res_groups_users_rel;
SELECT 'partners='||count(*)||':'||coalesce(md5(string_agg(id||':'||coalesce(name,'')||':'||active||':'||coalesce(company_id,0), ',' ORDER BY id)), '-') FROM res_partner;
SELECT 'access_all='||count(*)||':'||coalesce(md5(string_agg(a.id||':'||coalesce(a.domain,'')||':'||a.active||':'||coalesce(a.group_id,0)||':'||a.operation, ',' ORDER BY a.id)), '-') FROM ir_access a;
SELECT 'tp_bank='||count(*)||':'||count(*) FILTER (WHERE active)||':'||count(DISTINCT bin) FROM tp_bank;
SELECT 'employee_messages='||count(*) FROM mail_message WHERE model='hr.employee';
SELECT 'mail_queue='||count(*) FROM mail_mail;
SELECT 'notifications='||count(*) FROM mail_notification;
SELECT 'base_url='||md5(value) FROM ir_config_parameter WHERE key='web.base.url';
'@
$sqlFile = "$base\$Label-snapshot.sql"
function Snapshot([string]$name) {
    [IO.File]::WriteAllText($sqlFile, $snapshotSql.Replace("`r`n", "`n"), [Text.UTF8Encoding]::new($false))
    docker cp $sqlFile tp-postgres:/tmp/bank002-snapshot.sql
    if ($LASTEXITCODE -ne 0) { throw 'Snapshot copy failed' }
    $lines = @(& docker @psql -f /tmp/bank002-snapshot.sql)
    if ($LASTEXITCODE -ne 0) { throw "Snapshot $name failed" }
    $lines | Set-Content -LiteralPath "$base\$Label-$name.txt" -Encoding UTF8
    $map = [ordered]@{}
    foreach ($line in $lines) { $at = $line.IndexOf('='); if ($at -gt 0) { $map[$line.Substring(0, $at)] = $line.Substring($at + 1) } }
    return $map
}
$container = (docker inspect tp-odoo | ConvertFrom-Json)[0]
if (-not $container.State.Running -or $container.Config.WorkingDir -ne '/workspace') { throw 'Unexpected Odoo runtime' }
# Baseline: released paths hold the parent commit's content (MISSING for new files); dependencies match the release.
foreach ($file in $manifest.baseline.PSObject.Properties) {
    if ((FileHash $file.Name) -ne $file.Value) { throw "Source drift before deploy: $($file.Name)" }
}
foreach ($file in $manifest.dependencies.PSObject.Properties) {
    if ((FileHash $file.Name) -ne $file.Value) { throw "Dependency differs from the tested source: $($file.Name)" }
}
$modules = @{}
foreach ($row in @(& docker @psql -F '|' -c "SELECT name, state, coalesce(latest_version,'') FROM ir_module_module WHERE name IN ('tp_hr_bank','tp_hr_workspace','tp_admin_delegation')")) {
    $parts = $row.Split('|'); $modules[$parts[0]] = "$($parts[1]):$($parts[2])"
}
if ($LASTEXITCODE -ne 0) { throw 'Module state check failed' }
if ($modules['tp_hr_bank'] -ne 'installed:20.0.1.0.0') { throw "Unexpected tp_hr_bank state: $($modules['tp_hr_bank'])" }
foreach ($dep in @('tp_hr_workspace', 'tp_admin_delegation')) {
    if (-not "$($modules[$dep])".StartsWith('installed:')) { throw "Dependency not installed: $dep" }
}
$stamp = Get-Date -Format 'yyyyMMddTHHmmss'
$backup = "C:\TANPHAT-backups\hr-bank002\$Label-$stamp"
New-Item -ItemType Directory -Path $backup | Out-Null
docker stop tp-odoo | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Stop failed' }
$upgradeExit = -1
$stampedAt = $null
$after = $null
try {
    $before = Snapshot 'before'
    docker exec tp-postgres pg_dump -U tp_odoo -F c -f /tmp/hr-bank002-pre.dump tp_tanphat_dev
    if ($LASTEXITCODE -ne 0) { throw 'pg_dump failed' }
    docker exec tp-postgres pg_restore -l /tmp/hr-bank002-pre.dump > "$backup\restore-list.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Backup verification failed' }
    docker cp tp-postgres:/tmp/hr-bank002-pre.dump "$backup\tp_tanphat_dev.dump"
    if ($LASTEXITCODE -ne 0) { throw 'Backup copy failed' }
    docker exec tp-postgres rm -f /tmp/hr-bank002-pre.dump
    tar -czf "$backup\filestore.tar.gz" -C "$root\docker_data\filestore" tp_tanphat_dev
    if ($LASTEXITCODE -ne 0) { throw 'Filestore backup failed' }
    # Overwritten source (paths that exist before the release; new files are absent from the baseline).
    $existing = @($manifest.baseline.PSObject.Properties | Where-Object { $_.Value -ne 'MISSING' } | ForEach-Object { $_.Name })
    tar -czf "$backup\source.tar.gz" -C $root @existing
    if ($LASTEXITCODE -ne 0) { throw 'Source backup failed' }
    Copy-Item -LiteralPath "$root\docker.odoo.conf", "$base\$Label-manifest.json", "$base\$Label-before.txt" -Destination $backup
    tar -xzf "$base\$Label-release.tar.gz" -C $root
    if ($LASTEXITCODE -ne 0) { throw 'Extract failed' }
    foreach ($file in $manifest.release.PSObject.Properties) {
        if ((FileHash $file.Name) -ne $file.Value) { throw "Release checksum mismatch: $($file.Name)" }
    }
    # Odoo versions each CSS/JS bundle by file URL + modification time: stamp released files with the deploy time.
    $stampedAt = Get-Date
    foreach ($file in $manifest.release.PSObject.Properties) {
        (Get-Item -LiteralPath (Join-Path $root $file.Name)).LastWriteTime = $stampedAt
    }
    $argsDocker = @('run','--rm','--name','tp-bank002-upgrade','--network','tanphat-one_default',
        '-v',($root+':/workspace'),'-v',($root+'\docker_data\filestore:/var/lib/odoo/filestore'),'-w','/workspace',
        $container.Config.Image,'python3','odoo-bin','-c','/workspace/docker.odoo.conf','-d','tp_tanphat_dev',
        '-u','tp_hr_bank','--no-http','--stop-after-init','--max-cron-threads=0',
        "--logfile=/workspace/.local/hr-bank002/$Label-upgrade.log")
    $ErrorActionPreference = 'Continue'
    & docker @argsDocker *> "$base\$Label-console.log"
    $upgradeExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($upgradeExit -ne 0) { throw "Upgrade failed: $upgradeExit; backup: $backup" }
    $after = Snapshot 'after'
    Copy-Item -LiteralPath "$base\$Label-after.txt", "$base\$Label-upgrade.log" -Destination $backup
} finally {
    docker start tp-odoo | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Restart failed' }
    Get-ChildItem -LiteralPath $backup -File | Where-Object { $_.Name -ne 'SHA256SUMS.json' } | ForEach-Object { [pscustomobject]@{file=$_.Name; bytes=$_.Length; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash} } | ConvertTo-Json | Set-Content -LiteralPath "$backup\SHA256SUMS.json" -Encoding UTF8
}
# Only the module version and the trust flag of self-declared accounts may change.
$expected = @('module:tp_hr_bank', 'bank_accounts', 'bank_trust')
$unexpected = @(@($before.Keys) + @($after.Keys) | Sort-Object -Unique | Where-Object { $_ -notin $expected -and $before[$_] -ne $after[$_] })
$errors = @(Select-String -CaseSensitive -LiteralPath "$base\$Label-upgrade.log" -Pattern ' (ERROR|CRITICAL) ').Count
$migrated = @(Select-String -LiteralPath "$base\$Label-upgrade.log" -Pattern 'BANK-002: (\d+) self-declared' | ForEach-Object { $_.Matches[0].Groups[1].Value })
$result = [pscustomobject]@{commit=$manifest.commit; backup=$backup; files=@($manifest.release.PSObject.Properties).Count;
    upgrade_exit=$upgradeExit; log_errors=$errors; stamped_at=$stampedAt.ToString('s');
    module=$after['module:tp_hr_bank']; migrated=$migrated;
    bank_trust_active_trusted_waiting=@($before['bank_trust'], $after['bank_trust']);
    mail_queue=@($before['mail_queue'], $after['mail_queue']); notifications=@($before['notifications'], $after['notifications']);
    checked_keys=@($after.Keys).Count; unexpected_diffs=$unexpected}
$result | ConvertTo-Json | Set-Content -LiteralPath "$base\$Label-result.json" -Encoding UTF8
Copy-Item -LiteralPath "$base\$Label-result.json" -Destination $backup
Get-Content -LiteralPath "$base\$Label-result.json"
if ($errors -gt 0) { throw 'Upgrade logged errors: inspect before accepting' }
if ($unexpected.Count -gt 0) { throw "Unexpected differences: $($unexpected -join ', ')" }
if ($after['module:tp_hr_bank'] -ne '20.0.1.1.0:installed') { throw "tp_hr_bank not upgraded: $($after['module:tp_hr_bank'])" }
if (-not $after['bank_trust'].EndsWith(':0')) { throw "Self-declared accounts still waiting: $($after['bank_trust'])" }
