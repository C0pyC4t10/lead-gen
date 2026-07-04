# Running the Lead Gen Server Locally

## What this does
- Runs the **original `server.py`** on your laptop (with Playwright for Facebook/Instagram extraction)
- Saves leads to the **same Supabase database** that the deployed webapp uses
- The deployed site at **https://scraven.vercel.app** will show all leads you save locally

## Setup (one time)

```bash
cd /home/skarbolt/kb/lead-gen
./run_local.sh
```

This will:
1. Create a Python virtual environment
2. Install all dependencies
3. Install Playwright Chromium browser (~150MB, one-time)
4. Connect to Supabase
5. Start the server on `http://localhost:8800`

## Use

**To extract leads:**
```bash
# In another terminal, with the server running:
python3 smart_hunt.py --category beauty --count 50
python3 apify_facebook.py "facebook.com/somepage"
```

**To view saved leads:**
- Open **https://scraven.vercel.app/leads.html** in your browser
- Login with `jahid.skarbol@gmail.com` + your old password
- Or use the auto-login token (see below)

**Auto-login (skip the login form):**

Open browser console (F12 → Console) and paste:
```js
localStorage.setItem("skarbol_token", "1b3b98cffd0fb88612f170882a818c8c1dd893d7672ec7447a95258fcd0cc0ce");
localStorage.setItem("skarbol_user", JSON.stringify({name:"Jahid",email:"jahid.skarbol@gmail.com",role:"super_admin"}));
location.reload();
```

## Important

- **Keep `run_local.sh` running** while you extract leads
- The server **must be running** for Playwright extraction to work
- The webapp at `scraven.vercel.app` works **independently** — you don't need the local server to view leads, only to extract new ones

## Troubleshooting

**"Network is unreachable" when connecting to Supabase:**
- Your ISP may block direct Supabase connections
- Try a different network (mobile hotspot, VPN)
- Or use a free PostgreSQL tunnel service

**Playwright fails:**
- Run `python3 -m playwright install chromium` again
- May need to install system deps: `sudo apt install -y libnss3 libatk1.0-0 libatk-bridge2.0-0`

**Port 8800 already in use:**
- Edit `server.py` last line: change `port = int(os.environ.get('PORT', 8800))` to another port
- Or run `PORT=8888 python3 server.py`
