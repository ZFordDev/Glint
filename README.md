# **GlassHUD — A Modern Glass‑Rendered Desktop System Monitor for Windows**

GlassHUD is a lightweight, always‑visible desktop system monitor for Windows.  
It renders a translucent glass panel directly on the desktop using **QPainter**, delivering smooth, modern system stats without HTML widgets, web engines, or heavy UI frameworks.

GlassHUD is built with a **Linux‑style modular architecture**, a **dedicated updater micro‑application**, and a **clean packaging pipeline**, making it both lightweight and highly maintainable.

The HUD is frameless, draggable, and designed to stay visually unobtrusive while remaining readable at a glance.

---

## **Current Capabilities**

### 🎨 Modern Glass UI  
- Custom‑drawn frosted panel  
- Gradient overlays and soft borders  
- Highlight lines and subtle depth cues  
- Smooth, pixel‑perfect bar graphs  
- Fully painter‑rendered (no HTML, no layout jitter)

### 📊 Live System Stats  
- CPU usage  
- RAM usage  
- Disk usage (first two drives)  
- Modular sensor backend for future expansion (temps, GPU, etc.)

### 🖥 Desktop Behavior  
- Always‑on‑desktop (below windows, above wallpaper)  
- Draggable with left‑click  
- Right‑click context menu  
- Lightweight, low‑resource, no background services

### 🧩 Modular Architecture  
- `glasshud/` — main application package  
- `core/` — system stats + sensor logic  
- `ui/` — painter‑rendered HUD + menus  
- `glasshub-updater/` — standalone updater micro‑app  
- Clean separation of UI, logic, and update pipeline

---

## **Project Direction**

GlassHUD is transitioning from a simple HUD into a **fully structured desktop utility** with:

### 🔧 A dedicated updater subsystem  
- Separate updater executable  
- Version comparison via GitHub  
- Safe file replacement  
- Checksum validation  
- Rollback protection  
- Relaunch logic  
- Update button in HUD context menu

### ⚙️ A settings subsystem  
- Start‑on‑login toggle  
- Saved window position  
- Opacity control  
- Refresh rate control  
- Theme presets  
- JSON‑based configuration

### 📦 A full packaging pipeline  
- PyInstaller build  
- Inno Setup installer  
- Version stamping  
- Auto‑update integration  
- Clean uninstall support

This is no longer “just a HUD” — it’s becoming a **proper Windows desktop application** with a Linux‑inspired internal structure.

---

## **Installation (Development Mode)**

### 1. Clone the repository
```
git clone https://github.com/<your-username>/GlassHUD.git
cd GlassHUD
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

Dependencies include:
- `PyQt6` — GUI framework  
- `psutil` — system stats  
- `wmi` / `pywin32` — optional sensor support  
- `requests` — updater networking  

---

## **Usage**

Run the HUD:

```
python main.py
```

The widget will appear on your desktop.

### Controls
- **Left‑click + drag** — move the HUD  
- **Right‑click** — context menu (Exit, Update, future settings)

---

## **Project Structure**

```
sys_stat/
├── main.py
├── pyproject.toml
├── requirements.txt
├── glasshub-updater/
│   ├── updater-main.py
│   └── updater.py
└── glasshud/
    ├── __init__.py
    ├── core/
    │   ├── sensors.py
    │   └── stats.py
    └── ui/
        ├── hud.py
        └── menu.py
```

---

## **How It Works**

### QPainter‑Driven Rendering  
GlassHUD uses QPainter to draw:

- Rounded glass background  
- Gradient overlays  
- Highlight lines  
- Smooth usage bars  
- Segoe UI text  

This approach provides:

- Zero layout jitter  
- Pixel‑perfect alignment  
- Faster rendering  
- A native Windows aesthetic  
- Full control over visuals

### Stats Pipeline  
- `stats.py` collects CPU, RAM, and disk usage  
- `hud.py` renders them using painter primitives  
- Update loop runs every 1 second  

### Updater Pipeline  
- Separate updater executable  
- GitHub release scanning  
- Version comparison  
- Safe file replacement  
- Checksum validation  
- Relaunch logic  

---

## **Roadmap**

### Near‑term
- GPU usage (Iris Xe compatible)  
- CPU/GPU temperature support via LibreHardwareMonitor  
- Acrylic blur (real Windows frosted glass)  
- Settings panel (opacity, refresh rate, auto‑start)  
- System tray icon  
- Compact mode  

### Mid‑term
- Plugin system  
- Theme packs  
- Multi‑monitor support  
- Auto‑positioning presets  

---

## **Requirements**

- Windows 10 or later  
- Python 3.10+  
- psutil  
- PyQt6  

---

## **License**

MIT License (or your preferred license)

