# Slack Integration Setup Checklist

## Phase 2A: Collect Required Information

### 1. Get Bot Token
- [ ] Go to https://api.slack.com/apps
- [ ] Click on your "Ecommerce Analytics Bot" app  
- [ ] Navigate to "OAuth & Permissions" in the left sidebar
- [ ] Copy the "Bot User OAuth Token" (starts with `xoxb-`)
- [ ] **IMPORTANT**: Keep this token secure - treat it like a password

**Your Bot Token**: `xoxb-_______________` (fill this in)

### 2. Set Up Target Channel
- [ ] Create a dedicated channel (recommended): `#analytics-reports` or `#ecommerce-summary`
- [ ] OR choose existing channel: `#general`, `#analytics`, etc.
- [ ] Invite your bot to the channel: 
  - Type in channel: `/invite @YourBotName`
  - OR go to channel info → Members → Add people → search for your bot

**Your Channel**: `#_______________` (fill this in)

### 3. Verify Bot Permissions
- [ ] Bot should appear in channel member list
- [ ] Bot should have a "BOT" label next to its name
- [ ] Test bot can see channel (no "This channel is private" errors)

## Phase 2B: Ready for Cloud Run Configuration
Once you have:
- ✅ Bot token (`xoxb-...`)
- ✅ Channel name (`#channel-name`)  
- ✅ Bot invited to channel

You're ready for the next step!