# My Tools — Unified Web App (Signup/Login + Image Resizer + RemoveBG)

Tamara 2 tools (Image Resizer - Compressor, RemoveBG Pro) - tame je
zip files mokli hati e j tools ni original design/UI ne ek j login
system sathe jodi didhu che. Database MySQL che.

## This update fixes
1. **Resizer + RemoveBG tools** — have tame je zip mokli hati e j
   tools no original look (drag & drop, dark mode, live preview,
   before/after comparison, background color presets) vaparyo che,
   fakt login/history sathe jodi didhu che. Badhu same processing
   (EXIF handling, safety limits, u2net AI model) pela thi j hatu.
2. **"127.0.0.1 refused to connect" email link bug** — Aa tyare
   thay jyare tame email tamara **phone** par kholo, pan link
   `127.0.0.1` (matlab "aa j computer") point karto hoy. Have:
   - Server `0.0.0.0` par run thay che (network par pan available)
   - `python app.py` run karso tyare terminal ma tamara PC nu
     network address batashe (e.g. `http://192.168.1.5:5000`)
   - `.env` ma `APP_BASE_URL` set kari shakay
   - Verification / reset link have **hammesha screen par pan**
     batashe (email na male to backup)
3. **Signup email verification link na aavvani problem** — link
   have hammesha screen par pan dekhaay che (email delay/spam thai
   shake tevi situation mate), etle verify karvama kadi atkas nahi.
4. **`.env` variable naming** — tamaru `.env` `DB_HOST`/`DB_USER`
   vapare che, app have banne naming (`MYSQL_HOST` ane `DB_HOST`)
   support kare che.
5. Login pachi `/login`/`/signup` khulto nathi (dashboard par j jay
   che), logout karya pachi j pacho khule che.
6. Aakhu project laptop + mobile responsive, MySQL database sathe.

## 1. MySQL Setup

Tamara computer par MySQL server (standalone MySQL ya **XAMPP** no
MySQL) chalu hovo joiye.

App potej database (`mytools_db`) ane tables banavi lese jyare
tame pehli vaar `python app.py` run karso.

## 2. Install

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

> Note: `rembg` / `onnxruntime` install thava ma thoduk time lagshe.
> Pehli vaar RemoveBG tool vaparso tyare AI model (~176 MB) download
> thashe (internet joise, ek j vaar).

## 3. Configuration (.env file)

`.env.example` ne `.env` ma copy karo, pachi values check/sachi karo:

- `MYSQL_HOST` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE`
- Email (Gmail App Password): https://myaccount.google.com/apppasswords
- `APP_BASE_URL` — **jo tame email phone par kholo cho**, to aa
  tamara PC nu network address set karo (terminal ma batashe jyare
  app run karso), jem ke `APP_BASE_URL=http://192.168.1.5:5000`

**SMTP set nahi karo to pan app kaam karshe** — link screen par j
batashe. SMTP set karyu hoy to pan link hammesha screen par backup
tarike dekhaay che.

## 4. Run

```bash
python app.py
```

Terminal ma 2 address batashe:
```
On this computer:  http://127.0.0.1:5000
On your network:   http://192.168.1.X:5000   (phone mate aa vaparo)
```

## Project Structure

```
app.py                    main entry point
config.py                  settings (secret key, folders, mail, MySQL)
db.py                       MySQL database (users + history)
mailer.py                   email token + sending helper (APP_BASE_URL aware)
auth.py                     signup / login / logout / forgot / reset / verify
profile.py                   profile edit / picture / change password
tools_resizer.py             Image Resizer - Compressor (bulk + ZIP)
tools_removebg.py            RemoveBG Pro (bulk + ZIP + bg color)
history.py                    unified history (delete single / all)
templates/                    all HTML pages
static/css/style.css          shared site design (nav, forms, dashboard, etc.)
static/css/resizer-tool.css   Resizer tool's original look
static/css/removebg-tool.css  RemoveBG tool's original look
static/js/resizer-tool.js     Resizer tool front-end behavior
static/js/removebg-tool.js    RemoveBG tool front-end behavior
static/js/validate.js         auth forms client-side validation
```

## Notes
- Database: MySQL — settings from `.env`. Auto-creates on first run.
- Uploaded/processed images per user, per batch, store under
  `static/uploads/<tool>/<user_id>/<batch_id>/`.
- Passwords are hashed (never stored in plain text).
- All server-side validation stays authoritative (client-side JS is
  just for a nicer experience) — forms are re-checked on the server
  regardless of what the browser sends.
- Login-required routes redirect to login if not logged in; already
  logged-in users are redirected away from `/login`/`/signup`.
