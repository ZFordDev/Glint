# Glint

Glint is a lightweight, painter‑rendered system monitor designed for **my personal Windows PC**.  
It sits on the desktop, stays out of the way, and gives a clean, at‑a‑glance view of system usage without relying on HTML, Electron, or heavy widget engines.

If it works for you, great.  
If it doesn’t, open an issue with your **system specs** and I’ll see if support can be added.

Ubuntu support exists in theory (PyQt + psutil), but **Glint has not been tested on Ubuntu yet**.

---

## **Features**

### **Minimal Desktop UI**
- Painter‑rendered interface (no web engine, no layout jitter)  
- Frameless, draggable, unobtrusive  
- Crisp usage bars and clean text  

### **Live System Stats**
- CPU usage  
- RAM usage  
- Disk usage (first two drives)  
- Modular backend for future sensors (GPU, temps, etc.)

### **Desktop Behavior**
- Always‑on‑desktop layer (below windows, above wallpaper)  
- Right‑click context menu  
- Lightweight footprint  

### **Architecture**
- Modular Linux‑style layout  
- Dedicated updater micro‑application (half working on might never make it) 
- JSON configuration  
- Clean packaging pipeline (PyInstaller + installer)

---

## **Why Glint Exists**

Most Windows system monitors rely on HTML widgets, Electron shells, or heavy UI frameworks.  
Glint takes a different approach:

- **Zero web stack**  
- **Fully painter‑rendered**  
- **Fast, stable, pixel‑perfect**  
- **Always visible without getting in the way**  
- **Modular internal design**  

It’s built to be simple, reliable, and personal.

---

## **Installation (Development Mode)**

### 1. Clone the repository
```bash
git clone https://github.com/ZFordDev/Glint.git
cd Glint
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
# working on the pyproject.toml
```

Dependencies include:
- PyQt6  
- psutil  
- wmi / pywin32 (optional Windows sensors)  
- requests (updater)

---

## **Usage**

Run Glint:

```bash
python main.py
```

### **Controls**
- **Left‑click + drag** — move the HUD  
- **Right‑click** — context menu (Exit, Update, Settings)

---

## **Project Structure**

```
glint/
├── main.py
├── pyproject.toml
├── requirements.txt
├── updater/
│   ├── updater-main.py
│   └── updater.py
└── glint/
    ├── __init__.py
    ├── core/
    │   ├── sensors.py
    │   └── stats.py
    └── ui/
        ├── hud.py
        └── menu.py
```

---

## **Roadmap**

### **Near‑Term**
- GPU usage  
- CPU/GPU temperatures (LibreHardwareMonitor)  
- Acrylic blur  
- Settings panel (opacity, refresh rate, auto‑start)  
- System tray icon  
- Compact mode  

### **Mid‑Term**
- Plugin system  
- Theme packs  
- Multi‑monitor support  
- Auto‑positioning presets  

---

## **Compatibility**

- **Windows 10+** — fully supported  
- **Ubuntu / Linux** — *not tested yet*  
- Python 3.10+  

If Glint doesn’t run on your system, open an issue with:
- CPU model  
- GPU model  
- OS version  
- Python version  

I’ll check if support can be added.

---

## **License**

MIT License

---
