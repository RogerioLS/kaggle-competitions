# 🔒 Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability & Confidentiality Protections

This repository operates as a **Federated Portfolio Hub** for competitive Machine Learning and Large Language Model agents.

We prioritize security, especially concerning:
1. **API Keys and Credentials**: Kaggle API keys (`~/.kaggle/kaggle.json`, `KAGGLE_KEY`), Hugging Face tokens, and cloud credentials must NEVER be committed to this hub or any submodule.
2. **Competition Confidentiality**: Proprietary weights, model strategies, and submission pipelines must remain isolated within private competition submodules.

If you discover a security vulnerability or credential leak within **kaggle-competitions** or any registered submodule, please do NOT file a public issue. Report it directly via email to:

- **Security Contact**: `rogerio.ls@gmail.com`

Please include:
1. Description of the vulnerability or exposed credential.
2. Affected repository or submodule path.
3. Steps to reproduce and assess impact.

You will receive an acknowledgment within 24–48 hours, and immediate containment measures will be executed.
