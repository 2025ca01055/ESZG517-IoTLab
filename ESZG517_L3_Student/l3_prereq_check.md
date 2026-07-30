# ESZG517 — Lab Session L3 — Prerequisite Check

Run each command below in your terminal (Mac/Linux) or command prompt (Windows).
Compare your output to the expected output.
If anything fails, follow the fix instructions before coming to class.

---

## 1. Python

**Mac/Linux:**
```bash
python3 --version
```
**Windows:**
```cmd
python --version
```
**Expected:**
```
Python 3.x.x
```
**Fix:** Download from https://www.python.org/downloads/

---

## 2. paho-mqtt

**Mac/Linux:**
```bash
python3 -c "import paho.mqtt.client; print('OK')"
```
**Windows:**
```cmd
python -c "import paho.mqtt.client; print('OK')"
```
**Expected:**
```
OK
```
**Fix:**

Mac/Linux:
```bash
pip3 install paho-mqtt
```
Windows:
```cmd
pip install paho-mqtt
```

---

## 3. Node.js

**Mac/Linux/Windows:**
```bash
node --version
```
**Expected:**
```
v18.x.x  (or higher)
```
**Fix:** Download LTS version from https://nodejs.org/

---

## 4. Node-RED

**Mac/Linux/Windows:**
```bash
node-red --version
```
**Expected:**
```
Node-RED version: v3.x.x  (or higher)
```
**Fix:**

Mac/Linux:
```bash
npm install -g --unsafe-perm node-red
```
Windows (run Command Prompt as Administrator):
```cmd
npm install -g --unsafe-perm node-red
```

---

## 5. Node-RED Dashboard Palette

**Mac/Linux:**
```bash
ls ~/.node-red/node_modules | grep node-red-dashboard
```
**Windows:**
```cmd
dir %USERPROFILE%\.node-red\node_modules | findstr node-red-dashboard
```
**Expected:**
```
node-red-dashboard
```
**Fix:**

Mac/Linux:
```bash
cd ~/.node-red && npm install node-red-dashboard
```
Windows:
```cmd
cd %USERPROFILE%\.node-red && npm install node-red-dashboard
```

---

## 6. MQTT Explorer

Open your browser and go to: https://mqtt-explorer.com

Download and install the version for your operating system.

To verify it is installed:
- Mac: Open Finder → Applications → MQTT Explorer
- Windows: Search MQTT Explorer in the Start Menu
- Linux: Run `mqtt-explorer` in terminal

**Expected:** MQTT Explorer opens with a connection screen.

---

## All checks passed?

If all 6 show the expected output, you are ready for L3.
If anything fails, fix it before the session or message the instructor.
