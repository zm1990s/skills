---
name: cortex-xdr-learning
description: >
  Interactive attack scenario library for Cortex XDR training and SOC analyst education.
  Use this skill whenever users want to learn about XDR detection, practice SOC analysis,
  study attack chains (ransomware, APT, BEC, cloud IAM, Kubernetes escape, OT/ICS, etc.),
  explore MITRE ATT&CK techniques, analyze raw security logs, understand threat hunting,
  or walk through incident response workflows. Also trigger for questions like "how does
  XDR detect X", "show me a [attack type] scenario", "teach me about [threat technique]",
  or any security training request involving log analysis, behavioral detection, or
  multi-stage attack simulation.
tags: [xdr, cortex, soc, security, training, attack-scenarios, mitre-attack, incident-response, threat-hunting]
category: 安全培训
---

# Cortex XDR Learning — Interactive Attack Scenario Library

This skill guides users through realistic, multi-stage attack scenarios to understand how Cortex XDR correlates endpoint, network, and cloud telemetry to detect and respond to threats.

## Learning Objectives

After completing these scenarios, users will:
- Understand how XDR correlates telemetry across endpoints, networks, and cloud services
- Recognize attack chain stages mapped to MITRE ATT&CK
- See how behavioral analysis detects zero-day and fileless threats
- Practice threat response workflows used by real SOC analysts

## Available Scenarios

| # | Scenario | Difficulty | Key ATT&CK Techniques |
|---|----------|-----------|----------------------|
| 1 | Ransomware Attack | Intermediate | T1566, T1059, T1003, T1021, T1486 |
| 2 | Supply Chain Compromise | Advanced | T1195, T1574, T1036, T1071 |
| 3 | Insider Threat & Data Exfiltration | Intermediate | T1078, T1083, T1048, T1567 |
| 4 | Business Email Compromise (BEC) | Beginner | T1566, T1110, T1078, T1114 |
| 5 | APT — Living off the Land (LotL) | Advanced | T1218, T1053, T1070, T1027 |
| 6 | Cryptojacking Attack | Beginner | T1190, T1055, T1496, T1562 |
| 7 | Cloud IAM Exploitation (AWS Takeover) | Advanced | T1552, T1078, T1098, T1530, T1496 |
| 8 | Active Directory Attack (Kerberoasting + DCSync) | Advanced | T1558, T1550, T1003, T1069 |
| 9 | AiTM Phishing (MFA Bypass) | Intermediate | T1557, T1528, T1621, T1114 |
| 10 | Container & Kubernetes Escape | Advanced | T1190, T1611, T1552, T1610, T1613 |
| 11 | Zero-Day Browser Exploit (Drive-by Download) | Advanced | T1189, T1203, T1055, T1027, T1547 |
| 12 | Password Spraying + MFA Fatigue Attack | Beginner | T1110, T1621, T1078, T1098 |
| 13 | OT/ICS Network Intrusion (SCADA Targeting) | Advanced | T1590, T1046, T1021, T0843, T0842 |

## Teaching Methodology

**Presentation style**: Walk through each scenario stage by stage. Present the alert table and raw log, then pause and ask the interactive questions. Wait for the user's response before revealing the next stage or detailed analysis.

**On request**:
- **"Give me a hint"** → Reveal the hint option for that stage
- **"Explain"** / **"详细分析"** → Provide the Detailed Analysis block
- **"Show attack chain"** → Display the Final Summary timeline diagram
- **"Next"** / **"继续"** → Advance to the next stage
- **"Skip to scenario N"** → Jump directly to a specific scenario

**Difficulty guidance**:
- Beginners (Scenarios 4, 6, 12): Focus on recognition and basic response actions
- Intermediate (Scenarios 1, 3, 9): Emphasize correlation and multi-step thinking
- Advanced (Scenarios 2, 5, 7, 8, 10, 11, 13): Explore attacker tradecraft and detection gaps

## Loading Scenario Content

Scenario details live in the reference files. Load the relevant file based on the requested scenario number:

- **Scenarios 1–4** → read `references/scenarios-01-04.md`
- **Scenarios 5–8** → read `references/scenarios-05-08.md`
- **Scenarios 9–13** → read `references/scenarios-09-13.md`

Each file contains the full stage-by-stage content: alert tables, raw log samples, MITRE ATT&CK mappings, interactive questions, hints, detailed analysis, and attack chain timeline diagrams.

## Quick Start

When the user says "start", "let's begin", or names a scenario, ask which they'd like if unspecified. Then load the appropriate reference file and present Stage 1. A typical opening:

> "Welcome to Cortex XDR Training. Today's scenario: **[Scenario Name]** (Difficulty: [level]). You're the SOC analyst on duty. Here's what just came in..."
