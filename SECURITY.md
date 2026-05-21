# Security Policy

## Scope and important disclaimers

**stock-mcp is a small open-source hobby project.** Please read these points before reporting:

- This server uses [yfinance](https://github.com/ranaroussi/yfinance), an **unofficial, reverse-engineered Yahoo Finance scraper**. It is not affiliated with or endorsed by Yahoo or Verizon Media.
- **Do not use this project for production trading systems, algorithmic trading, financial advice, or any decision where data accuracy is critical.** Data may be inaccurate, delayed, adjusted retroactively, or suddenly unavailable with no warning.
- The server handles **no personally identifiable information (PII)**. It does not accept user credentials, does not store data, and does not make outbound requests except to Yahoo Finance via yfinance.
- There is no authentication layer. The MCP server is designed to be run locally by the user who owns the machine.

## Supported versions

Only the latest release on the `main` branch receives security attention.

## Reporting a vulnerability

**Non-sensitive issues** (e.g., a dependency with a known CVE, an information-disclosure edge case): open a [GitHub Issue](https://github.com/<owner>/stock-mcp/issues) with the label `security`.

**Sensitive issues** (e.g., something that could harm users if disclosed publicly before a fix is available): use GitHub's [private vulnerability reporting](https://github.com/<owner>/stock-mcp/security/advisories) feature.

Please include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested remediation if you have one

Given the project's small scope, response time may be a few days rather than hours. There is no bug bounty program.
