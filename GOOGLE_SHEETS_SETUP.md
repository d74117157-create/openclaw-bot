
# GOOGLE SHEETS INTEGRATION SETUP
# Your swarm memory syncs to Google Sheets automatically

## Step 1: Create the Google Sheet
1. Go to https://sheets.new
2. Name it: "OpenClaw Swarm Memory"
3. Create 4 tabs/sheets:
   - Sheet 1: "portfolio"
   - Sheet 2: "trades"  
   - Sheet 3: "decisions"
   - Sheet 4: "events"

## Step 2: Add headers to each sheet

### portfolio sheet (row 1):
timestamp | asset | balance | price | value_usd | source

### trades sheet (row 1):
timestamp | exchange | symbol | side | qty | price | notional | pnl | status | agent

### decisions sheet (row 1):
timestamp | agent_name | action | context | result | confidence

### events sheet (row 1):
timestamp | event_type | platform | details

## Step 3: Get your Sheet ID
The Sheet ID is in the URL:
https://docs.google.com/spreadsheets/d/THIS_IS_YOUR_SHEET_ID/edit

## Step 4: Share with service account (or make public for now)
Click Share → Anyone with link → Viewer (for reading)
For writing: Share → Add email of your Google service account

## Step 5: Add to Render Environment Variables
GOOGLE_SHEETS_ID=your_sheet_id_here
GOOGLE_API_KEY=AIzaSyDzJZDn2Vbx-po11V6MSfcf5vtCg3KlcUY (already set)

## Step 6: Test
Run /portfolio in Discord after next deploy.
Every trade, balance check, and bot event will auto-log to Sheets.
