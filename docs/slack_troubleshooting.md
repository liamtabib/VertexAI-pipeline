# Slack Integration Troubleshooting

## Common Issues & Solutions

### ❌ Issue: "Invalid token" error in logs
**Symptoms**: Logs show authentication error or invalid token
**Solutions**:
- [ ] Verify token starts with `xoxb-` (not `xoxp-`)
- [ ] Check token was copied completely (no truncation)
- [ ] Ensure no extra spaces or quotes in environment variable
- [ ] Regenerate token if needed from Slack app settings

### ❌ Issue: "Channel not found" error
**Symptoms**: Bot can't post to channel
**Solutions**:
- [ ] Verify channel name includes `#` (e.g., `#analytics-reports`)
- [ ] Check bot was invited to the channel
- [ ] Try using channel ID instead of name (format: `C1234567890`)
- [ ] Test with a public channel first

### ❌ Issue: No message appears in Slack
**Symptoms**: Job completes but no Slack message
**Solutions**:
- [ ] Check Cloud Run logs for Slack-related errors
- [ ] Verify bot has `chat:write` permission
- [ ] Test bot manually: send a DM to the bot
- [ ] Check if channel is archived or deleted

### ❌ Issue: "Rate limited" errors
**Symptoms**: Slack API rate limit exceeded
**Solutions**:
- [ ] Wait 1 minute and retry
- [ ] Reduce frequency of pipeline runs
- [ ] Check if other apps are using same bot token

## Verification Commands

### Check Cloud Run Configuration:
```bash
gcloud run jobs describe gemini-summarizer --region=us-central1 \
  --format="value(spec.template.template.spec.template.spec.containers[0].env[].name,spec.template.template.spec.template.spec.containers[0].env[].value)"
```

### Check Recent Logs:
```bash
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=gemini-summarizer" \
  --limit=20 --project=pipeline-466508 | grep -E "(slack|Slack|ERROR|Failed)"
```

### Test Bot Token Manually:
```bash
curl -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer xoxb-your-token"
```

## Recovery Steps

### Reset Configuration:
```bash
# Remove Slack variables (disables integration)
gcloud run jobs update gemini-summarizer \
  --region=us-central1 \
  --remove-env-vars="SLACK_BOT_TOKEN,SLACK_CHANNEL"

# Re-add with correct values
gcloud run jobs update gemini-summarizer \
  --region=us-central1 \
  --update-env-vars="SLACK_BOT_TOKEN=xoxb-correct-token,SLACK_CHANNEL=#correct-channel"
```