# Security Policy 🛡️

**RadioBridge takes security seriously.** As a tool trusted by amateur radio operators worldwide for programming mission-critical communications equipment, we are committed to maintaining the highest security standards.

*73 and thank you for helping keep RadioBridge secure!*
*Craig - KO6GXM*

---

## 📢 Reporting a Vulnerability

### 🚨 Quick Reporting

**Found a security issue?** We want to hear from you!

1. **📧 Email**: Send details to **craig@ko6gxm.com** with subject line starting with `[SECURITY]`
2. **🔒 GitHub**: Use our [Security Advisories](https://github.com/ko6gxm/radiobridge/security/advisories) (preferred for coordinated disclosure)
3. **🔐 Encrypted**: For sensitive disclosures, request GPG key in initial contact

### 📋 What to Include

**Please provide as much detail as possible:**

```
Subject: [SECURITY] Brief description of vulnerability

1. **Vulnerability Type**: (e.g., CSV injection, path traversal, etc.)
2. **Affected Component**: (e.g., CLI, formatter, downloader)
3. **Affected Versions**: (e.g., v0.3.0, main branch)
4. **Reproduction Steps**: Clear step-by-step instructions
5. **Proof of Concept**: Code, commands, or screenshots
6. **Impact Assessment**: Potential security implications
7. **Your Environment**: OS, Python version, installation method
```

### ⚡ Emergency Contact

**Critical security issues requiring immediate attention:**

- 📧 **Email**: craig@ko6gxm.com with subject: `[URGENT SECURITY]`
- 🔴 **GitHub**: Mark advisory as "Critical" severity
- ⏱️ **Response**: Within 12 hours for critical issues

---

## 🗓️ Supported Versions

### Current Support Matrix

| Version | Python Support | Security Support | Status |
|---------|---------------|------------------|--------|
| **0.3.x** (current) | 3.9 - 3.13 | ✅ Full Support | Active Development |
| **0.2.x** | 3.9 - 3.13 | ⚠️ Limited Support | Bug Fixes Only |
| **0.1.x** | 3.9+ | ❌ No Support | End of Life |
| **main branch** | 3.9 - 3.13 | ✅ Full Support | Development |

### End-of-Life Policy

- **Current Release**: Full security support and rapid response
- **Previous Major**: Critical security fixes for 6 months
- **Older Releases**: No security support (please upgrade)

---

## 🎯 Security Scope

### ✅ In Scope (We Want to Hear About These!)

**Application Security:**
- Code injection vulnerabilities (CSV, command injection)
- Path traversal and file system access issues
- Unsafe deserialization or data parsing
- Authentication/authorization bypasses
- Cross-site scripting in generated output
- Denial of service vulnerabilities

**Dependencies & Supply Chain:**
- Vulnerable dependencies (we use Safety + Bandit in CI)
- Package tampering or substitution attacks
- Malicious code in third-party libraries

**Data Security:**
- Unsafe handling of user data or credentials
- Information disclosure vulnerabilities
- Unsafe temporary file creation

### ❌ Out of Scope (Not Security Issues)

**External Services:**
- RepeaterBook.com availability or data quality
- Network connectivity or DNS resolution issues
- Rate limiting or API restrictions

**Usage & Configuration:**
- Amateur radio licensing or regulatory compliance
- Incorrect radio programming by end users
- Hardware compatibility issues
- Performance or feature requests

**Expected Behavior:**
- CLI help output or error messages
- Documentation bugs or typos
- Feature requests or enhancement ideas

---

## ⏰ Response Expectations

### Our Commitment to You

| Severity | Initial Response | Triage Complete | Fix Available |
|----------|-----------------|-----------------|---------------|
| **Critical** | 12 hours | 24 hours | 3 days |
| **High** | 24 hours | 3 days | 7 days |
| **Medium** | 3 days | 7 days | 30 days |
| **Low** | 7 days | 14 days | Next release |

### What Happens Next?

1. **Acknowledgment**: We confirm receipt of your report
2. **Triage**: We assess severity and impact
3. **Investigation**: We reproduce and analyze the issue
4. **Fix Development**: We create and test a solution
5. **Coordinated Disclosure**: We work with you on public disclosure
6. **Recognition**: We thank you publicly (if desired)

---

## 🤝 Responsible Disclosure

### Our Promise

- **No Legal Action**: We won't pursue legal action against security researchers acting in good faith
- **Credit Given**: We'll publicly acknowledge your contribution (unless you prefer anonymity)
- **Communication**: We'll keep you informed throughout the process
- **Fair Timeline**: We'll work together on appropriate disclosure timing

### What We Ask

- **Good Faith**: Act with honest intent to improve security
- **Privacy**: Don't access, modify, or delete user data
- **Scope**: Stay within the defined scope above
- **Patience**: Allow reasonable time for fixes before public disclosure
- **No Spam**: Don't flood our systems or perform denial of service attacks

### Disclosure Timeline

```
Day 0:    Vulnerability reported
Day 1-3:  Initial response and triage
Day 4-30: Investigation and fix development
Day 31-90: Testing and coordinated disclosure planning
Day 90+:  Public disclosure (sooner if fix is ready)
```

---

## 🏆 Security Hall of Fame

**We recognize security researchers who help improve RadioBridge:**

### Contributors

*📻 Hall of Fame coming soon! Be our first security researcher.*

### Recognition Options

- **GitHub**: Public acknowledgment in SECURITY.md and release notes
- **Blog**: Feature on [ko6gxm.com](https://ko6gxm.com)
- **QSL Card**: Official KO6GXM QSL card as thanks (upon request)
- **Anonymity**: We respect your preference to remain anonymous

*Want to join the Hall of Fame? Help us find and fix security issues!*

---

## 🔧 GitHub Security Advisories

### Using GitHub's Security Features

1. **Report**: Visit our [Security Advisories](https://github.com/ko6gxm/radiobridge/security/advisories)
2. **Click**: "Report a vulnerability" button
3. **Describe**: Fill out the vulnerability details form
4. **Submit**: Your report goes directly to maintainers

### Benefits of GitHub Advisories

- **Private Discussion**: Work with maintainers before public disclosure
- **CVE Assignment**: Automatic CVE numbering for significant issues
- **Credit System**: Built-in contributor recognition
- **Coordinated Release**: Synchronized public disclosure with fixes

---

## 🔒 Security Measures

### Current Security Practices

**Development Security:**
- 🤖 **Automated Scanning**: Safety and Bandit in CI/CD pipeline
- 🧪 **Security Tests**: Dedicated security test cases
- 📝 **Code Review**: All changes reviewed before merge
- 🔄 **Dependency Updates**: Regular dependency security updates

**Runtime Security:**
- 🛡️ **Input Validation**: Strict validation of CSV and command inputs
- 📁 **Safe File Handling**: Secure temporary file creation and cleanup
- 🌐 **Network Safety**: Rate limiting and request validation
- 🔐 **No Privilege Escalation**: Runs with user permissions only

### Security Testing

```bash
# Run security scans locally
pipenv run python -m safety check
pipenv run python -m bandit -r src/

# Include security tests
pipenv run pytest -m security
```

---

## ⚖️ License and Disclaimers

### Security vs. MIT License

RadioBridge is provided under the **MIT License**, which includes important disclaimers:

> **THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND**

**This means:**
- ✅ We'll fix security issues as fast as possible
- ✅ We appreciate security reports and take them seriously
- ❌ We can't guarantee the software is free from all vulnerabilities
- ❌ Users are responsible for verifying security in their environment

### Amateur Radio Responsibility

**Remember:** As licensed amateur radio operators, we are responsible for:
- ✅ Ensuring our transmissions are legal and appropriate
- ✅ Verifying repeater information before transmitting
- ✅ Following proper amateur radio operating procedures
- ✅ Maintaining the security of our radio equipment

---

## 📞 Contact Information

### Security Team

**Primary Contact:**
- 👨‍💻 **Craig Simon - KO6GXM**
- 📧 **Email**: craig@ko6gxm.com
- 🌐 **Website**: [ko6gxm.com](https://ko6gxm.com)
- 📻 **QRZ**: [KO6GXM](https://qrz.com/db/KO6GXM)

### Response Languages
- 🇺🇸 **English** (preferred)
- 🇪🇸 **Spanish** (basic)

### Time Zone
- 🕐 **Pacific Time (US)** - Expect faster responses during business hours

---

## 📚 Additional Resources

### Security Best Practices

**For Users:**
- Keep RadioBridge updated to the latest version
- Verify CSV data sources and content
- Use RadioBridge in trusted environments
- Report suspicious behavior immediately

**For Developers:**
- Review our [Contributing Guide](CONTRIBUTING.md)
- Follow secure coding practices
- Test security implications of changes
- Keep dependencies updated

### Learning More

- 📖 **Documentation**: [README.md](README.md)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/ko6gxm/radiobridge/discussions)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/ko6gxm/radiobridge/issues)
- 🔐 **Security**: This document and our [Advisories](https://github.com/ko6gxm/radiobridge/security/advisories)

---

<div align="center">

**🛡️ Security Through Community 🛡️**

*Your security reports make RadioBridge safer for the entire amateur radio community.*

[![Report Vulnerability](https://img.shields.io/badge/Report-Security%20Issue-red.svg?style=for-the-badge)](https://github.com/ko6gxm/radiobridge/security/advisories)
[![Email Security](https://img.shields.io/badge/Email-craig%40ko6gxm.com-blue.svg?style=for-the-badge)](mailto:craig@ko6gxm.com?subject=[SECURITY])

*73 and secure coding!*
*KO6GXM*

</div>
