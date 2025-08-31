# GitHub Workflow Slack Notifications 🔔

This document describes the Slack notification system integrated into RadioBridge's GitHub workflows.

## 📨 What Gets Notified

### CI/CD Pipeline (`ci.yml`)
- **When**: After all CI jobs complete (test, integration-test, build, security, performance, docs)
- **Triggers**:
  - Push to `main` branch
  - Pull requests to `main` or `develop`
- **Content**:
  - Overall CI status (success/failure)
  - Individual job results
  - Branch, author, and commit information
  - Direct link to workflow run

### Release Pipeline (`release.yml`)
- **Success Notifications**: After successful release publication
  - Version information
  - Installation instructions
  - Links to GitHub Release and PyPI package
- **Failure Notifications**: When any release job fails
  - Failed job status
  - Action required message
  - Link to workflow logs

## 🎨 Notification Format

Notifications use rich Slack attachments with:
- **Color coding**: Green for success, red for failure
- **Structured fields**: Organized information display
- **Clickable links**: Direct navigation to GitHub
- **Timestamps**: When the event occurred
- **Ham radio touch**: "73" sign-offs and amateur radio terminology

## 🔧 Configuration

### Required Secret
The workflows use `SLACK_WEBHOOK_URL` secret which should contain your Slack incoming webhook URL.

### Slack Action
Uses `8398a7/action-slack@v3` for reliable Slack integration with custom payload support.

### Notification Conditions
- **CI**: Only notifies on main branch pushes and pull requests
- **Release**: Notifies on all release attempts (success or failure)
- **Skip cancelled**: No notifications for cancelled workflows

## 📱 Example Notifications

### Successful CI
```
✅ RadioBridge CI Pipeline
Repository: ko6gxm/RadioBridge
Branch: main
Author: Craig Simon
Overall Status: success
Job Results:
• Tests: success
• Integration: success
• Build: success
• Security: success
• Performance: success
• Docs: success
```

### Successful Release
```
🎉 RadioBridge Release 0.3.0 Published!
Version: 0.3.0
Installation: pip install radiobridge==0.3.0
Links:
• GitHub Release
• PyPI Package
```

### Failed Release
```
❌ RadioBridge Release 0.3.0 Failed!
Job Status:
• Validation: success
• Build & Test: success
• Create Release: failure
• Publish PyPI: skipped
Action Required: Check workflow logs and fix issues before retrying.
```

## 🚀 Benefits

1. **Immediate Awareness**: Know instantly when CI/CD completes
2. **Detailed Context**: Rich information without checking GitHub
3. **Mobile Friendly**: Slack notifications work great on mobile
4. **Team Visibility**: Share CI/CD status with collaborators
5. **Ham Radio Spirit**: Professional notifications with amateur radio flair

## 🔧 Customization

To modify notifications:

1. **Change channels**: Update the webhook URL to point to different Slack channels
2. **Modify content**: Edit the `custom_payload` sections in the workflow files
3. **Add conditions**: Modify `if` conditions to change when notifications trigger
4. **Add more platforms**: Use additional actions for Discord, Teams, etc.

## 🐛 Troubleshooting

**No notifications received?**
- Verify `SLACK_WEBHOOK_URL` secret is set correctly
- Check that webhook URL is active in Slack
- Ensure conditions are met (correct branch, event type)

**Notifications too verbose?**
- Modify the `if` conditions to be more restrictive
- Remove individual job status from the payload
- Consider success-only notifications for CI

**Want notifications in multiple channels?**
- Create separate webhook URLs for different channels
- Add multiple notification steps with different webhook URLs

---

*The notification system ensures you stay informed about your RadioBridge development workflow while maintaining the amateur radio community spirit. 73!*
