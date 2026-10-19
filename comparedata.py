import os
import tkinter as tk
from macsafe import make_navbtn, force_light_mode
import easygui
import pandas as pd

OUTPUT = "df2.csv"          # overwritten on every load; read this in your other files


def show_load_df2(root, df, show_analysis, show_steeringthrottle_graph,
                  show_friction_circle, show_gforces, show_histograms, show_loader, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data):
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
        make_navbtn(navbar, text, cmd)

    navbtn("Load Data", lambda: show_loader())
    navbtn("Prep Data", lambda: show_prep_data(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("Comparison Run", lambda: show_load_df2(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data))
    navbtn("Analysis", lambda: show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data))
    navbtn("Lap Times", lambda: show_laptime_chart(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_channel_plot, show_prep_data))
    navbtn("Steering & Throttle", lambda: show_steeringthrottle_graph(root, df, show_analysis, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data))
    navbtn("Friction Circle", lambda: show_friction_circle(root, df, show_analysis, show_steeringthrottle_graph, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data))
    navbtn("G-Forces", lambda: show_gforces(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data))
    navbtn("Histograms", lambda: show_histograms(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data))
    navbtn("Custom Plot", lambda: show_channel_plot(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_prep_data))
    navbtn("Save Run", lambda: show_save_run(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_laptime_chart, show_channel_plot, show_prep_data))

    # ── centred load area ────────────────────────────────
    body = tk.Frame(outer)
    body.pack(side="top", fill="both", expand=True)

    inner = tk.Frame(body)
    inner.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(inner, text="Load a comparison run (.csv)",
             font=("Segoe UI", 28, "bold")).pack(pady=(0, 10))

    status = tk.Label(inner, text="", font=("Segoe UI", 12), fg="#1a7f37")
    status.pack(pady=(0, 20))

    def load_csv():
        try:
            file = easygui.fileopenbox()
            def read_comment(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()

                            if line.startswith("#"):
                                return line[1:].strip()

                            if line:
                                break

                    return ""

                except Exception as e:
                    print("Error reading comment:", e)
                    return ""
            comment = read_comment(file)
            with open("comment.txt", "w", encoding="utf-8") as f:
                f.write(comment)
            if not file:
                return
            data = pd.read_csv(file, comment="#")          # ignore comment lines starting with #
            data.to_csv(OUTPUT, index=False)          # overwrites the previous df2.csv
            status.config(text="Comparison run loaded successfully", fg="#1a7f37")
            print("df2 saved to", os.path.abspath(OUTPUT), f"({len(data)} rows)")
        except Exception as e:
            status.config(text=f"Error: {e}", fg="#c0392b")
            print("Error loading file:", e)

    def delete_csv():
        try:
            if os.path.exists(OUTPUT):
                os.remove(OUTPUT)
                status.config(text=f"Deleted {OUTPUT}", fg="#1a7f37")
                print(f"{OUTPUT} deleted")
            else:
                status.config(text=f"{OUTPUT} does not exist", fg="#c0392b")
                print(f"{OUTPUT} does not exist")
        except Exception as e:
            status.config(text=f"Error: {e}", fg="#c0392b")
            print("Error deleting file:", e)

    tk.Button(inner, text="Load .csv Data", command=load_csv,
              bg="#2d2d2d", fg="white",
              activebackground="#3d3d3d", activeforeground="white",
              relief="flat", bd=0, font=("Segoe UI", 12),
              padx=30, pady=14, cursor="hand2").pack(pady=8)

    tk.Button(inner, text="Clear comparisson run", command=delete_csv,
                  bg="#2d2d2d", fg="white",
                  activebackground="#3d3d3d", activeforeground="white",
                  relief="flat", bd=0, font=("Segoe UI", 12),
                  padx=30, pady=14, cursor="hand2").pack(pady=8)