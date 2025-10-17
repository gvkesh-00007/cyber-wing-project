# WeasyPrint Troubleshooting Guide for Windows

This document provides comprehensive troubleshooting steps for fixing WeasyPrint-related import errors in the CyberComplaintBot project, particularly on Windows systems.

## Problem Overview

### The Import Error

You may encounter an error like:

```
ImportError: cannot import name 'ConversationManager' from 'conversation'
```

Or:

```
OSError: cannot load library 'gobject-2.0-0': error 0x7e
```

### Root Cause

The import error is triggered because the module import chain fails while loading WeasyPrint's native dependencies on Windows. Python never finishes importing your `conversation` module to expose `ConversationManager` because `pdf_generator.py` (which is imported by `conversation.py`) tries to import WeasyPrint, which fails due to missing native Windows libraries (GTK/Pango/Cairo).

## Quick Solution: Use the Fallback PDF Generator

**Good News**: The project has been updated with a **ReportLab fallback** that works immediately without installing WeasyPrint dependencies!

### How It Works

1. The updated `pdf_generator.py` uses **lazy import** - WeasyPrint is only loaded when actually generating a PDF, not during module import
2. If WeasyPrint fails to load, the system automatically falls back to ReportLab for basic PDF generation
3. This means your bot can start and run immediately while you work on installing WeasyPrint for enhanced PDF formatting

### Installation Steps

1. **Update your dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   This will install both `weasyprint` and `reportlab` packages.

2. **Test the application:**
   ```bash
   python app.py
   ```
   
   The application should now start successfully!

3. **Verify PDF generation:**
   - When you complete a complaint, a PDF will be generated
   - If WeasyPrint isn't working, you'll see a note in the PDF footer: "This PDF was generated using fallback mode (ReportLab)"
   - The PDF will contain all complaint data in a simple text format

## Full WeasyPrint Installation (For Enhanced PDFs)

If you want the full HTML-templated PDFs with enhanced formatting, follow these steps to install WeasyPrint's native dependencies on Windows.

### Option A: Using GTK Runtime for Windows (Recommended)

1. **Download and install GTK for Windows:**
   - Visit: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
   - Download the latest installer (e.g., `gtk3-runtime-x.x.x-x-ts-win64.exe`)
   - Run the installer and follow the installation wizard
   - **Important**: Check the box to add GTK to your system PATH during installation

2. **Restart your terminal/command prompt** (important to load new PATH variables)

3. **Verify the installation:**
   ```bash
   python -m weasyprint --info
   ```
   
   You should see output showing WeasyPrint and Pango versions without errors.

4. **Test PDF generation:**
   ```bash
   python app.py
   ```
   
   PDFs should now be generated with full HTML templating!

### Option B: Using MSYS2 (Advanced)

For users familiar with MSYS2:

1. **Install MSYS2** from https://www.msys2.org/

2. **Install required packages:**
   ```bash
   pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-cairo mingw-w64-x86_64-pango
   ```

3. **Set environment variable before running Python:**
   ```bash
   set WEASYPRINT_DLL_DIRECTORIES=C:\msys64\mingw64\bin
   python app.py
   ```

4. **Or permanently add to your environment** via Windows System Properties → Environment Variables

### Common Installation Issues

#### Issue 1: "cannot load library 'gobject-2.0-0'"

**Solution:**
- Ensure the GTK `bin` directory is in your system PATH
- The DLL file should be at: `C:\Program Files\GTK3-Runtime Win64\bin\libgobject-2.0-0.dll`
- If missing, reinstall GTK runtime
- Restart your terminal/IDE after installation

#### Issue 2: WeasyPrint installs but still fails

**Solution:**
- Check your Python version - use Python 3.9, 3.10, or 3.11 (most tested)
- Create a fresh virtual environment:
  ```bash
  python -m venv venv_new
  .\venv_new\Scripts\activate
  pip install -r requirements.txt
  ```

#### Issue 3: DLL conflicts or version mismatches

**Solution:**
- Uninstall any conflicting GTK installations
- Remove GTK directories from PATH
- Reinstall the GTK runtime as described in Option A
- Ensure no other applications (like GIMP, Inkscape) are providing conflicting GTK DLLs in PATH

## Verification Checklist

After installation, verify everything works:

- [ ] **Import test**: Open Python shell and run:
  ```python
  from conversation import ConversationManager
  print("✓ ConversationManager imported successfully")
  ```

- [ ] **WeasyPrint test**: Run in Python shell:
  ```python
  python -m weasyprint --info
  ```
  Should show versions without errors.

- [ ] **Full app test**:
  ```bash
  python app.py
  ```
  Should start Flask server without import errors.

- [ ] **PDF generation test**: Complete a test complaint through WhatsApp and verify:
  - PDF is generated in `uploads/` directory
  - PDF opens without errors
  - Check PDF footer - if using WeasyPrint successfully, there should be no fallback notice

## Understanding the Lazy Import Fix

### What Changed in `pdf_generator.py`

The updated code uses lazy import:

```python
class PDFGenerator:
    def __init__(self):
        self._ready = False
        try:
            # Lazy import - only loads when class is instantiated
            from weasyprint import HTML
            self.HTML = HTML
            self._ready = True
        except Exception as e:
            # Falls back to ReportLab
            from reportlab.pdfgen import canvas
            self._use_fallback = True
```

### Why This Works

1. **Before**: WeasyPrint was imported at module level (`from weasyprint import HTML` at the top of the file)
   - This meant any import error would prevent `pdf_generator` from loading
   - Which prevented `conversation.py` from loading
   - Which caused "cannot import ConversationManager"

2. **After**: WeasyPrint is imported inside the class `__init__` method
   - Module loads successfully even if WeasyPrint has issues
   - Error only occurs if you actually try to generate a PDF
   - Fallback to ReportLab if WeasyPrint unavailable

## Next Steps

### For Immediate Use

Just run with the ReportLab fallback:
```bash
pip install -r requirements.txt
python app.py
```

### For Enhanced PDF Formatting

Install GTK runtime following Option A above, then:
```bash
python -m weasyprint --info  # Verify installation
python app.py  # Run with full WeasyPrint support
```

### If You Still Have Issues

1. Check `bot.log` for detailed error messages
2. Ensure you're using Python 3.9-3.11
3. Try in a fresh virtual environment
4. Open a GitHub issue with:
   - Your Python version (`python --version`)
   - Your OS version
   - Full error traceback
   - Output of `python -m weasyprint --info`

## Additional Resources

- **WeasyPrint Official Docs**: https://doc.courtbouillon.org/weasyprint/stable/
- **WeasyPrint Windows Installation**: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows
- **GTK for Windows**: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
- **ReportLab Documentation**: https://www.reportlab.com/docs/reportlab-userguide.pdf

---

**Last Updated**: October 2025  
**Status**: Fallback system active and working ✓
