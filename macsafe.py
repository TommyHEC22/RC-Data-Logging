"""Cross-platform UI helpers (macOS dark mode + navbar buttons)."""
import sys
import tkinter as tk

def force_light_mode(root):
    """macOS Tk follows the system dark mode, which clashes with the hard-coded
    white cards / dark navbar. Pin the window to the light (aqua) look."""
    if sys.platform != "darwin":
        return
    print("Tk", root.tk.call("info", "patchlevel"))
    try:
        root.tk.call("::tk::unsupported::MacWindowStyle", "appearance", root._w, "aqua")
    except tk.TclError as e:
        print("appearance call failed:", e)

    # Belt and braces: give every classic tk widget explicit light defaults via
    # the option database. Explicit bg/fg set in the code still win, so the dark
    # navbar and white cards are unchanged - only the "system" colours that
    # follow dark mode are replaced.
    root.tk_setPalette(background="#ececec", foreground="black",
                       activeBackground="#dcdcdc", activeForeground="black",
                       highlightBackground="#ececec", highlightColor="black",
                       selectBackground="#b5d5ff", selectForeground="black",
                       insertBackground="black", troughColor="#d0d0d0",
                       disabledForeground="#999999")
    for cls in ("Entry", "Listbox", "Text", "Spinbox"):
        root.option_add(f"*{cls}.background", "white")
        root.option_add(f"*{cls}.foreground", "black")
    root.option_add("*TCombobox*Listbox.background", "white")
    root.option_add("*TCombobox*Listbox.foreground", "black")
    try:
        from tkinter import ttk
        st = ttk.Style(root)
        for w in ("TCombobox", "TEntry", "TSpinbox"):
            st.configure(w, fieldbackground="white", foreground="black",
                         background="#ececec")
        st.map("TCombobox", fieldbackground=[("readonly", "white")],
               foreground=[("readonly", "black")])
        for w in ("TLabel", "TFrame", "TCheckbutton", "TRadiobutton", "TLabelframe"):
            st.configure(w, background="#ececec", foreground="black")
    except Exception as e:
        print("ttk style failed:", e)


def make_navbtn(parent, text, cmd, bg="#2d2d2d", hover="#3d3d3d"):
    """Dark navbar button. macOS ignores bg on tk.Button (it always draws a
    native button), so there we use a clickable Label, which does honour bg."""
    if sys.platform != "darwin":
        tk.Button(parent, text=text, command=cmd,
                  bg=bg, fg="white",
                  activebackground=hover, activeforeground="white",
                  relief="flat", bd=0, font=("Segoe UI", 11),
                  padx=18, pady=6, cursor="hand2"
                  ).pack(side="left", padx=(12, 0), pady=8)
        return

    lbl = tk.Label(parent, text=text, bg=bg, fg="white",
                   font=("Segoe UI", 11), padx=18, pady=6, cursor="hand2")

    def recolour(c):
        try:
            lbl.configure(bg=c)
        except tk.TclError:
            pass   # page was rebuilt and the label is gone

    lbl.bind("<Enter>", lambda e: recolour(hover))
    lbl.bind("<Leave>", lambda e: recolour(bg))
    lbl.bind("<ButtonRelease-1>", lambda e: cmd())
    lbl.pack(side="left", padx=(12, 0), pady=8)
