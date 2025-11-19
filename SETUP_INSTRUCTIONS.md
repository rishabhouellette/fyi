"# Complete Setup Instructions for Fixed FYI Uploader



\## Files You Now Have:



\### Core Modules (NEW - I provided these):

\- ✅ `config.py` - Configuration management

\- ✅ `exceptions.py` - Custom exceptions

\- ✅ `logger\_config.py` - Logging system

\- ✅ `account\_manager.py` - Multi-account support

\- ✅ `facebook\_uploader.py` - FIXED Facebook uploader

\- ✅ `video\_validator.py` - Video validation

\- ✅ `server.py` - FIXED OAuth server

\- ✅ `scheduler\_engine.py` - Upload scheduler

\- ✅ `main.py` - FIXED main GUI



\### Keep Your Existing Files:

\- `youtube\_uploader.py` (your existing file)

\- `instagram\_uploader.py` (your existing file)



\## Step-by-Step Setup:



\### 1. Create .env File

```bash

\# Copy the example

cp .env.example .env



\# Edit .env and add your credentials:

nano .env

```



Add this content (replace with your actual values):

```ini

FB\_APP\_ID=222188858294490

FB\_APP\_SECRET=6f1c65510e626e9bb45fd5d2f52f8565

NGROK\_URL=https://your-ngrok-url.ngrok-free.app

```



\### 2. Install Dependencies

```bash

pip install flask requests python-dotenv opencv-python customtkinter

```



\### 3. Start ngrok (Keep Running)

```bash

ngrok http 5000

```



Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`) and update your `.env` file:

```ini

NGROK\_URL=https://abc123.ngrok-free.app

```



\### 4. Start OAuth Server (Keep Running)

Open a new terminal:

```bash

python server.py

```



You should see:

```

INFO | server | Starting OAuth server on 127.0.0.1:5000

```



\### 5. Start FYI Uploader

Open another terminal:

```bash

python main.py

```



\## First Time Usage:



\### Link Facebook Account:

1\. Click \*\*\\"Facebook\\"\*\* tab

2\. Click \*\*\\"LINK FACEBOOK\\"\*\* button

3\. Browser opens → Login to Facebook

4\. Grant all permissions

5\. You'll see \\"Authentication Successful\\"

6\. Close browser

7\. GUI now shows \\"Facebook Linked\\" with upload buttons



\### Upload Your First Video:

1\. Click \*\*\\"1. Select Videos\\"\*\*

2\. Choose a video file

3\. Click \*\*\\"INSTANT UPLOAD\\"\*\* to test

4\. Watch progress in status bar

5\. Check logs in `logs/facebook\_uploader.log`



\## Features Available:



\### Facebook Modes:

1\. \*\*INSTANT UPLOAD\*\* - Uploads immediately to Facebook

2\. \*\*SCHEDULER\*\* - Upload videos at set intervals (e.g., every 60 minutes)

3\. \*\*SMART SCHEDULER\*\* - Checks last scheduled post, continues from there



\### Scheduler Settings:

Click \*\*\\"Scheduler Settings\\"\*\* to configure:

\- \*\*Interval Mode\*\*: Upload every X days/hours/minutes

\- \*\*Specific Time\*\*: Upload at exact date/time



\### YouTube/Instagram:

Keep using your existing `youtube\_uploader.py` and `instagram\_uploader.py` files.



\## Testing Smart Scheduler:



\### To test the Smart Scheduler feature:

1\. Schedule 2-3 videos manually on Facebook (using regular scheduler)

2\. Click \*\*\\"SMART SCHEDULER\\"\*\*

3\. It will:

&nbsp;  - Check your last scheduled video time

&nbsp;  - Schedule new videos AFTER the last one

&nbsp;  - Use your configured interval



Example:

```

Last scheduled video: 3:00 PM

Interval: 30 minutes

Smart Scheduler will start at: 3:30 PM, 4:00 PM, 4:30 PM...

```



\## Troubleshooting:



\### \\"Missing environment variables\\"

→ Create `.env` file with FB\_APP\_ID, FB\_APP\_SECRET, NGROK\_URL



\### \\"No module named 'config'\\"

→ Make sure all provided files are in the same directory as main.py



\### \\"Account not found\\"

→ Link Facebook account first via the GUI



\### Facebook upload fails

→ Check:

1\. Is OAuth server running? (`python server.py`)

2\. Is ngrok running?

3\. Did you link account successfully?

4\. Check logs: `logs/facebook\_uploader.log`



\### Smart Scheduler not working

→ Make sure:

1\. Facebook account is linked

2\. Set interval in Scheduler Settings first

3\. Check logs for API errors



\## File Locations:



\- \*\*Accounts\*\*: `accounts/accounts.json`

\- \*\*Logs\*\*: `logs/` directory

\- \*\*Upload Log\*\*: `fyi\_successfully\_scheduled.txt`

\- \*\*Queue Log\*\*: `fyi\_queue\_log.csv`



\## What Changed from Your Old Code:



\### Same Features:

✅ Facebook upload with chunked resumable upload

✅ Smart Scheduler (checks last scheduled video)

✅ OAuth with state management

✅ Multi-account support

✅ Video validation



\### New Features:

✅ Better GUI (your CustomTkinter interface)

✅ Centralized config system

✅ Proper logging to files

✅ Modular architecture

✅ No hardcoded credentials



\### Key Difference:

\*\*Old\*\*: Credentials hardcoded in Python files

\*\*New\*\*: Credentials in `.env` file (secure \& proper)



\## Need Help?



Check the logs:

```bash

\# Main app log

tail -f logs/\_\_main\_\_.log



\# Facebook uploader log

tail -f logs/facebook\_uploader.log



\# Server log

tail -f logs/server.log

```



All errors will be logged there with full details.



---



\*\*You're all set! The Facebook uploader now uses your working old code with the new GUI.\*\*

"

