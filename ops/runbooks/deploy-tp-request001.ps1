param([Parameter(Mandatory=$true)][string]$Label)
# TP-REQUEST-001 (CHG-20261121-001): install tp_request (20.0.1.0.0) and upgrade tp_branding (20.0.2.2.0) on PC server.
# Stops tp-odoo, snapshots pre-deploy aggregates, backs up full DB dump (+ pg_restore -l verify), filestore, touched
# source and docker.odoo.conf; extracts committed release tarball, checks every SHA256, stamps LastWriteTime; runs
# one-off Odoo container with -i tp_request -u tp_branding --no-http --stop-after-init; snapshots post-deploy aggregates
# confirming zero unexpected drift on existing HR/Equipment/Attendance/User/Group data; restarts tp-odoo (never touches tp-tunnel).
$ErrorActionPreference = 'Stop'
if ($Label -notmatch '^req001(-[a-z0-9]+)?$') { throw 'Invalid release label' }
$root = 'C:\Projects\TANPHAT-ONE'
$base = Join-Path $root '.local\tp-request001'
$manifest = Get-Content -LiteralPath "$base\$Label-manifest.json" -Raw | ConvertFrom-Json
$scope = @('custom_addons/tp_request/', 'custom_addons/tp_branding/')

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
$snapshotSql = @'
SELECT 'module:'||name||'='||coalesce(latest_version,'')||':'||state FROM ir_module_module WHERE name IN ('tp_request','tp_branding','tp_admin_delegation','tp_equipment','tp_hr_attendance') ORDER BY name;
SELECT 'employees='||count(*)||':'||coalesce(md5(string_agg(id||':'||coalesce(name,'')||':'||coalesce(user_id,0)||':'||coalesce(work_contact_id,0)||':'||active||':'||company_id, ',' ORDER BY id)), '-') FROM hr_employee;
SELECT 'users='||count(*)||':'||coalesce(md5(string_agg(id||':'||login||':'||coalesce(password,'')||':'||active||':'||coalesce(company_id,0), ',' ORDER BY id)), '-') FROM res_users;
SELECT 'groups='||count(*)||':'||coalesce(md5(string_agg(uid||':'||gid, ',' ORDER BY uid, gid)), '-') FROM res_groups_users_rel;
SELECT 'equipment='||count(*)||':'||coalesce(md5(string_agg(id||':'||coalesce(tp_code,'')||':'||coalesce(tp_employee_id,0)||':'||coalesce(tp_custody,'')||':'||coalesce(tp_lifecycle,'')||':'||coalesce(tp_technical_state,''), ',' ORDER BY id)), '-') FROM maintenance_equipment;
SELECT 'equipment_proposals='||count(*)||':'||coalesce(md5(string_agg(id||':'||coalesce(name,'')||':'||coalesce(review_state,''), ',' ORDER BY id)), '-') FROM tp_equipment_proposal;
SELECT 'attendance_corrections='||count(*)||':'||coalesce(md5(string_agg(id||':'||coalesce(name,'')||':'||coalesce(state,''), ',' ORDER BY id)), '-') FROM tp_hr_attendance_correction;
SELECT 'base_url='||md5(value) FROM ir_config_parameter WHERE key='web.base.url';
'@

$sqlFile = "$base\$Label-snapshot.sql"
function Snapshot([string]$name) {
    [IO.File]::WriteAllText($sqlFile, $snapshotSql.Replace("`r`n", "`n"), [Text.UTF8Encoding]::new($false))
    docker cp $sqlFile tp-postgres:/tmp/req001-snapshot.sql
    if ($LASTEXITCODE -ne 0) { throw 'Snapshot copy failed' }
    $lines = @(& docker @psql -f /tmp/req001-snapshot.sql)
    if ($LASTEXITCODE -ne 0) { throw "Snapshot $name failed" }
    $lines | Set-Content -LiteralPath "$base\$Label-$name.txt" -Encoding UTF8
    $map = [ordered]@{}
    foreach ($line in $lines) { $at = $line.IndexOf('='); if ($at -gt 0) { $map[$line.Substring(0, $at)] = $line.Substring($at + 1) } }
    return $map
}

$container = (docker inspect tp-odoo | ConvertFrom-Json)[0]
if (-not $container.State.Running -or $container.Config.WorkingDir -ne '/workspace') { throw 'Unexpected Odoo runtime' }

$stamp = Get-Date -Format 'yyyyMMddTHHmmss'
$backup = "C:\TANPHAT-backups\tp-request001\$Label-$stamp"
New-Item -ItemType Directory -Path $backup | Out-Null

docker stop tp-odoo | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Stop tp-odoo failed' }

$upgradeExit = -1
$after = $null
try {
    $before = Snapshot 'before'
    docker exec tp-postgres pg_dump -U tp_odoo -F c -f /tmp/tp-req001-pre.dump tp_tanphat_dev
    if ($LASTEXITCODE -ne 0) { throw 'pg_dump failed' }
    docker exec tp-postgres pg_restore -l /tmp/tp-req001-pre.dump > "$backup\restore-list.txt"
    if ($LASTEXITCODE -ne 0) { throw 'pg_restore -l verification failed' }
    docker cp tp-postgres:/tmp/tp-req001-pre.dump "$backup\tp_tanphat_dev.dump"
    if ($LASTEXITCODE -ne 0) { throw 'Backup copy failed' }
    docker exec tp-postgres rm -f /tmp/tp-req001-pre.dump

    tar -czf "$backup\filestore.tar.gz" -C "$root\docker_data\filestore" tp_tanphat_dev
    if ($LASTEXITCODE -ne 0) { throw 'Filestore backup failed' }

    tar -czf "$backup\source.tar.gz" -C $root custom_addons/tp_branding
    if ($LASTEXITCODE -ne 0) { throw 'Source backup failed' }
    Copy-Item -LiteralPath "$root\docker.odoo.conf", "$base\$Label-manifest.json", "$base\$Label-before.txt" -Destination $backup

    tar -xzf "$base\$Label-release.tar.gz" -C $root
    if ($LASTEXITCODE -ne 0) { throw 'Release extract failed' }

    $verifiedCount = 0
    foreach ($file in $manifest.release.PSObject.Properties) {
        if ((FileHash $file.Name) -ne $file.Value) { throw "Release checksum mismatch: $($file.Name)" }
        $verifiedCount++
    }

    $stampedAt = Get-Date
    foreach ($file in $manifest.release.PSObject.Properties) {
        (Get-Item -LiteralPath (Join-Path $root $file.Name)).LastWriteTime = $stampedAt
    }

    $argsDocker = @('run','--rm','--name','tp-req001-upgrade','--network','tanphat-one_default',
        '-v',($root+':/workspace'),'-v',($root+'\docker_data\filestore:/var/lib/odoo/filestore'),'-w','/workspace',
        $container.Config.Image,'python3','odoo-bin','-c','/workspace/docker.odoo.conf','-d','tp_tanphat_dev',
        '-i','tp_request','-u','tp_branding','--no-http','--stop-after-init','--max-cron-threads=0',
        "--logfile=/workspace/.local/tp-request001/$Label-upgrade.log")
    $ErrorActionPreference = 'Continue'
    & docker @argsDocker *> "$base\$Label-console.log"
    $upgradeExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'

    $after = Snapshot 'after'
    Copy-Item -LiteralPath "$base\$Label-after.txt", "$base\$Label-upgrade.log" -Destination $backup -ErrorAction SilentlyContinue

    $reqTypesCount = & docker @psql -c "SELECT count(*) FROM tp_request_type;"
    $reqCount = & docker @psql -c "SELECT count(*) FROM tp_request;"
    $errLines = @(Select-String -LiteralPath "$base\$Label-upgrade.log" -Pattern ' ERROR | CRITICAL ' -ErrorAction SilentlyContinue)

    $invariantKeys = @('employees','users','groups','equipment','equipment_proposals','attendance_corrections','base_url')
    $drifts = @()
    foreach ($k in $invariantKeys) {
        if ($before[$k] -ne $after[$k]) { $drifts += "$k : $($before[$k]) -> $($after[$k])" }
    }

    Write-Output "BACKUP=$backup"
    Write-Output "FILES_VERIFIED=$verifiedCount"
    Write-Output "UPGRADE_EXIT=$upgradeExit"
    Write-Output "UPGRADE_ERRORS=$($errLines.Count)"
    Write-Output "TP_REQUEST_MODULE=$($after['module:tp_request'])"
    Write-Output "TP_BRANDING_MODULE=$($after['module:tp_branding'])"
    Write-Output "TP_REQUEST_TYPES=$reqTypesCount"
    Write-Output "TP_REQUEST_RECORDS=$reqCount"
    Write-Output "DRIFT_COUNT=$($drifts.Count)"
    foreach ($d in $drifts) { Write-Output "DRIFT=$d" }

    if ($upgradeExit -ne 0) { throw "Upgrade failed with exit code $upgradeExit" }
    if ($errLines.Count -gt 0) { throw "Upgrade log contains $($errLines.Count) ERROR/CRITICAL entries" }
    if ($drifts.Count -gt 0) { throw "Unexpected data drift detected: $($drifts -join '; ')" }
}
finally {
    docker start tp-odoo | Out-Null
}
