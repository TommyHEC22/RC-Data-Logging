import os
import tkinter as tk
from tkinter import ttk
import easygui

GOOD, BAD, NEUTRAL = "#1a7f37", "#c0392b", "#777777"

def show_save_run(root, df, show_analysis, show_steeringthrottle_graph,
                  show_friction_circle, show_gforces, show_histograms,
                  show_loader, show_load_df2, show_laptime_chart, show_channel_plot):
    root.state("zoomed")
    for w in root.winfo_children():
        w.destroy()

    outer = tk.Frame(root)
    outer.pack(fill="both", expand=True)

    # ── top nav bar ──────────────────────────────────────
    navbar = tk.Frame(outer, bg="#1e1e1e", height=52)
    navbar.pack(side="top", fill="x")
    navbar.pack_propagate(False)

    def navbtn(text, cmd):
        tk.Button(navbar, text=text, command=cmd,
                  bg="#2d2d2d", fg="white",
                  activebackground="#3d3d3d", activeforeground="white",
                  relief="flat", bd=0, font=("Segoe UI", 11),
                  padx=18, pady=6, cursor="hand2"
                  ).pack(side="left", padx=(12, 0), pady=8)

    navbtn("Load Data", lambda: show_loader())
    navbtn("Comparison Run", lambda: show_load_df2(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("Analysis", lambda: show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("Lap Times", lambda: show_laptime_chart(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_channel_plot))
    navbtn("Steering & Throttle", lambda: show_steeringthrottle_graph(root, df, show_analysis, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("Friction Circle", lambda: show_friction_circle(root, df, show_analysis, show_steeringthrottle_graph, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("G-Forces", lambda: show_gforces(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("Histograms", lambda: show_histograms(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("Custom Plot", lambda: show_channel_plot(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart))
    navbtn("Save Run", lambda: show_save_run(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_laptime_chart, show_channel_plot))

    # ── centred body ─────────────────────────────────────
    body = tk.Frame(outer)
    body.pack(side="top", fill="both", expand=True)

    inner = tk.Frame(body)
    inner.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(inner, text="Save Run", font=("Segoe UI", 28, "bold")).pack(pady=(0, 20))

    tk.Label(inner, text="Comment for this run:",
             font=("Segoe UI", 12)).pack(anchor="w")

    comment_box = tk.Text(inner, width=54, height=5, font=("Segoe UI", 11),
                          relief="solid", bd=1, wrap="word")
    comment_box.pack(pady=(4, 16))

    status = tk.Label(inner, text="", font=("Segoe UI", 11))

    def save_run():
        comment = comment_box.get("1.0", "end-1c").strip()
        path = easygui.filesavebox(msg="Save run as…", default="run.csv")
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            with open(path, "w", newline="") as f:
                for line in comment.splitlines():
                    f.write("# " + line + "\n")     # comment as header lines
                df.to_csv(f, index=False)
            status.config(text=f"Saved to {path}", fg=GOOD)
            print("Run saved to", path)
        except Exception as e:
            status.config(text=f"Error: {e}", fg=BAD)
            print("Save error:", e)

    tk.Button(inner, text="Choose location & save…", command=save_run,
              bg="#2d2d2d", fg="white",
              activebackground="#3d3d3d", activeforeground="white",
              relief="flat", bd=0, font=("Segoe UI", 12),
              padx=30, pady=12, cursor="hand2").pack(pady=(0, 6))

    status.pack(pady=(0, 24))

    # ── comparison run comment (from df2.csv) ────────────
    with open("comment.txt", "r", encoding="utf-8") as f:
        df2_comment = f.read()
    box = tk.LabelFrame(inner, text="Comparison run (df2) comment",
                        font=("Segoe UI", 11, "bold"), padx=14, pady=10)
    box.pack(fill="x")
    tk.Label(box,
             text=df2_comment if df2_comment else "No comment found in df2.",
             font=("Segoe UI", 11),
             fg="#333" if df2_comment else "#999",
             wraplength=460, justify="left").pack(anchor="w")