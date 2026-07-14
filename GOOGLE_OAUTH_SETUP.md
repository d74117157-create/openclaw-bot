# Google OAuth Auto-Setup for OpenClaw Empire

## What This Does
Your bot now has a **built-in Google OAuth server** with **172 scopes** covering every Google API your empire needs. No command line. No manual token copying. Just click, authorize, done.

## Step 1: Add Your OAuth Credentials to Render

In your Render dashboard, add these environment variables:

```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://openclaw-bot.onrender.com/google/callback
```

> **Note:** If you change your Render URL, update `GOOGLE_REDIRECT_URI` accordingly.

## Step 2: Add the Redirect URI to Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services -> Credentials**
3. Find your OAuth 2.0 Client ID
4. Add this to **Authorized redirect URIs**:
   ```
   https://openclaw-bot.onrender.com/google/callback
   ```
5. Save. Wait 2-3 minutes for propagation.

## Step 3: Authorize (One Click)

Visit this URL in your browser:

```
https://openclaw-bot.onrender.com/google/auth
```

You will see the Google consent screen. Click **Allow All**. The bot will:
- Exchange the auth code for tokens automatically
- Save `access_token` + `refresh_token` to `/tmp/google_tokens.json`
- Update `GOOGLE_ACCESS_TOKEN` and `GOOGLE_REFRESH_TOKEN` in the running environment
- Auto-refresh tokens before they expire

## Step 4: Verify

Check your OAuth status:
```
https://openclaw-bot.onrender.com/google/status
```

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/google/auth` | GET | Start OAuth flow (redirects to Google) |
| `/google/callback` | GET | OAuth callback handler (auto-exchanges code) |
| `/google/status` | GET | Check OAuth configuration + token status |
| `/google/refresh` | POST | Manually trigger token refresh |
| `/google/scopes` | GET | List all 172 configured scopes |

## Scopes Included (172 total)

### YouTube (8 scopes)
- Full YouTube management, uploads, analytics, partner access
- `youtube`, `youtube.upload`, `youtube.readonly`, `youtube.force-ssl`
- `yt-analytics.readonly`, `yt-analytics-monetary.readonly`
- `youtubepartner`, `youtubepartner-channel-audit`

### Google Drive (11 scopes)
- Full drive access, file management, metadata, photos, scripts
- `drive`, `drive.file`, `drive.readonly`, `drive.metadata`
- `drive.activity`, `drive.labels`, `drive.photos.readonly`

### Gmail (10 scopes)
- Read, send, compose, labels, settings
- `gmail.readonly`, `gmail.modify`, `gmail.send`, `gmail.compose`
- `gmail.labels`, `gmail.metadata`, `gmail.settings.basic`

### Calendar (16 scopes)
- Full calendar management, events, freebusy, ACLs
- `calendar`, `calendar.events`, `calendar.events.owned`
- `calendar.freebusy`, `calendar.acls`

### Docs/Sheets/Slides (6 scopes)
- `documents`, `spreadsheets`, `presentations` (read/write)

### Analytics (9 scopes)
- `analytics`, `analytics.readonly`, `analytics.edit`
- `analytics.manage.users`, `marketingplatformadmin.analytics.read`

### Google Ads (15 scopes)
- `adwords`, `adsense`, `display-video`, `doubleclickbidmanager`
- `dfareporting`, `dfatrafficking`, `realtime-bidding`

### Cloud Platform (25+ scopes)
- `cloud-platform`, `compute`, `bigquery`, `cloud-vision`
- `devstorage.full_control`, `firebase`, `pubsub`

### Search Console (3 scopes)
- `webmasters`, `webmasters.readonly`, `indexing`

### Photos (6 scopes)
- `photoslibrary`, `photoslibrary.sharing`, `photoslibrary.appendonly`

### Tasks/Keep/Contacts (7 scopes)
- `tasks`, `keep`, `contacts`, `contacts.readonly`

### User Info (8 scopes)
- `userinfo.email`, `userinfo.profile`, `user.birthday.read`

### Forms/Blogger/Books (8 scopes)
- `forms`, `blogger`, `books`

### Meet/Chat/Classroom (11 scopes)
- `meetings.space`, `chat.spaces`, `chat.messages`, `classroom.courses`

### Play/Android (4 scopes)
- `androidpublisher`, `androidmanagement`, `playdeveloperreporting`

### Data Portability - YouTube (14 scopes)
- `dataportability.youtube.channel`, `.comments`, `.clips`, `.live_chat`
- `.music`, `.playable`, `.posts`, `.private_playlists`, `.public_playlists`
- `.shopping`, `.subscriptions`, `.unlisted_playlists`, `.unlisted_videos`

## Auto-Refresh

The bot checks token expiry every 5 minutes. If a token is about to expire (within 5 minutes), it automatically refreshes using the stored `refresh_token`. You never have to touch this again.

## Troubleshooting

**"Invalid redirect URI" error**
- Make sure `https://openclaw-bot.onrender.com/google/callback` is added to your Google OAuth client's authorized redirect URIs in Cloud Console.

**"Refresh token expired" error**
- Visit `/google/auth` again to re-authorize. The `prompt=consent` parameter ensures you always get a new refresh token.

**No refresh token returned**
- This happens if you have already authorized before. Add `prompt=consent` to force a new refresh token (already included in the code).

## Files Changed

- `google_oauth_server.py` - New OAuth server with 172 scopes
- `assets/fastapi_superswarm_api.py` - OAuth routes registered
- `.env.example` - Updated with new OAuth variables
