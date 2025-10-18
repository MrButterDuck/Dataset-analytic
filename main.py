import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from data_preparer import load_data, basic_clean, infer_types, summary_stats
from data_viz import fig_histogram, fig_top_categories, fig_corr_heatmap, fig_time_series


class DataExplorerApp:
    def __init__(self, root):
        self.root = root
        root.title("Data Explorer — Desktop")
        root.geometry("1200x760")

        self.df = None
        self.date_cols = []
        self.numeric_cols = []
        self.categorical_cols = []

        left = ttk.Frame(root, width=320, padding=8)
        left.pack(side='left', fill='y')

        ttk.Label(left, text="Load CSV (file or URL)").pack(anchor='w')
        self.url_entry = ttk.Entry(left, width=40)
        self.url_entry.pack(anchor='w', pady=4)
        ttk.Button(left, text="Load from URL", command=self.load_from_url).pack(anchor='w', pady=2)
        ttk.Separator(left).pack(fill='x', pady=6)

        ttk.Button(left, text="Open CSV file...", command=self.open_file).pack(anchor='w', pady=2)
        ttk.Separator(left).pack(fill='x', pady=6)

        ttk.Label(left, text="Detected columns").pack(anchor='w', pady=(6,0))
        ttk.Label(left, text="Numeric:").pack(anchor='w')
        self.num_list = tk.Listbox(left, height=6, exportselection=False)
        self.num_list.pack(fill='x', pady=2)
        ttk.Label(left, text="Categorical:").pack(anchor='w')
        self.cat_list = tk.Listbox(left, height=6, exportselection=False)
        self.cat_list.pack(fill='x', pady=2)
        ttk.Label(left, text="Date cols:").pack(anchor='w')
        self.date_list = tk.Listbox(left, height=2, exportselection=False)
        self.date_list.pack(fill='x', pady=2)

        ttk.Separator(left).pack(fill='x', pady=6)
        ttk.Button(left, text="Show sample (20 rows)", command=self.show_sample).pack(fill='x', pady=2)
        ttk.Button(left, text="Show numeric summary", command=self.show_summary).pack(fill='x', pady=2)

        ttk.Label(left, text="Visualizations").pack(anchor='w', pady=(8,0))
        ttk.Button(left, text="Histogram (selected numeric)", command=self.plot_hist).pack(fill='x', pady=2)
        ttk.Button(left, text="Top categories (selected categorical)", command=self.plot_topcat).pack(fill='x', pady=2)
        ttk.Button(left, text="Correlation heatmap", command=self.plot_corr).pack(fill='x', pady=2)
        ttk.Button(left, text="Time series (selected date)", command=self.plot_timeseries).pack(fill='x', pady=2)

        ttk.Separator(left).pack(fill='x', pady=6)
        ttk.Button(left, text="Clear plot", command=self.clear_plot).pack(fill='x', pady=2)

        right = ttk.Frame(root, padding=6)
        right.pack(side='right', expand=True, fill='both')
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        right.rowconfigure(1, weight=0)


        self.plot_frame = ttk.Frame(right)
        self.plot_frame.grid(row=0, column=0, sticky='nsew')
        self.canvas = None
        self.bottom_area = ttk.Frame(right, height=220)
        self.bottom_area.grid(row=1, column=0, sticky='nsew')
        self.bottom_area.grid_propagate(False)
        self.text_widget = None
        self.table_widget = None
        self._create_text_widget()
        self.bottom_area.bind('<Configure>', self._on_bottom_resize)

    def load_from_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showinfo("Info", "Введите URL или выберите файл.")
            return
        try:
            df = load_data(url)
            self.set_dataframe(df)
        except Exception as e:
            messagebox.showerror("Error", f"Не удалось загрузить URL:\n{e}")

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files","*.csv"), ("All files","*.*")])
        if not path:
            return
        try:
            df = load_data(path)
            self.set_dataframe(df)
        except Exception as e:
            messagebox.showerror("Error", f"Не удалось открыть файл:\n{e}")

    def set_dataframe(self, df):
        df = basic_clean(df)
        self.df = df
        self.date_cols, self.numeric_cols, self.categorical_cols = infer_types(df)
        self.refresh_lists()
        self._show_text(f"Loaded: {len(df)} rows, {len(df.columns)} columns\n")
        self._append_text(f"Detected date cols: {self.date_cols}\n")
        self._append_text(f"Numeric cols: {self.numeric_cols[:20]}\n")
        self._append_text(f"Categorical cols: {self.categorical_cols[:20]}\n")

    def refresh_lists(self):
        self.num_list.delete(0, tk.END)
        for c in self.numeric_cols:
            self.num_list.insert(tk.END, c)
        self.cat_list.delete(0, tk.END)
        for c in self.categorical_cols:
            self.cat_list.insert(tk.END, c)
        self.date_list.delete(0, tk.END)
        for c in self.date_cols:
            self.date_list.insert(tk.END, c)

    def _create_text_widget(self):
        for w in self.bottom_area.winfo_children():
            w.destroy()
        frm = ttk.Frame(self.bottom_area)
        frm.pack(expand=True, fill='both')
        txt = tk.Text(frm, wrap='none', height=12)
        vsb = ttk.Scrollbar(frm, orient='vertical', command=txt.yview)
        hsb = ttk.Scrollbar(frm, orient='horizontal', command=txt.xview)
        txt.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        txt.pack(side='left', expand=True, fill='both')
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.text_widget = txt
        self.table_widget = None

    def _create_table_widget(self, max_rows=20):
        for w in self.bottom_area.winfo_children():
            w.destroy()
        frm = ttk.Frame(self.bottom_area)
        frm.pack(expand=True, fill='both')
        if self.df is None:
            lbl = ttk.Label(frm, text='No data loaded')
            lbl.pack()
            return
        cols = list(self.df.columns)
        tree = ttk.Treeview(frm, columns=cols, show='headings', height=max_rows)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=120, anchor='w', stretch=True)
        vsb = ttk.Scrollbar(frm, orient='vertical', command=tree.yview)
        hsb = ttk.Scrollbar(frm, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        head = self.df.head(max_rows)
        for idx, row in head.iterrows():
            values = [self._shorten_text(str(row[c])) for c in cols]
            tree.insert('', 'end', values=values)
        tree.pack(side='left', expand=True, fill='both')
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.table_widget = tree
        self.text_widget = None
        self._autosize_table_delayed()

    def _shorten_text(self, s, maxlen=120):
        if len(s) > maxlen:
            return s[:maxlen-3] + '...'
        return s

    def _show_text(self, txt):
        if self.text_widget is None:
            self._create_text_widget()
        self.text_widget.delete('1.0', tk.END)
        self.text_widget.insert(tk.END, txt)

    def _append_text(self, txt):
        if self.text_widget is None:
            self._create_text_widget()
        self.text_widget.insert(tk.END, txt)

    def show_sample(self):
        if self.df is None:
            messagebox.showinfo("Info", "Сначала загрузите данные.")
            return
        self._create_table_widget(max_rows=20)

    def show_summary(self):
        if self.df is None:
            messagebox.showinfo("Info", "Сначала загрузите данные.")
            return
        stats = summary_stats(self.df, self.numeric_cols)
        if stats.empty:
            self._show_text("Нет числовых колонок для статистики.")
        else:
            self._show_text(stats.to_string())

    def plot_on_canvas(self, fig):
        self.clear_plot()
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.draw()
        widget = self.canvas.get_tk_widget()
        widget.pack(expand=True, fill='both')

    def clear_plot(self):
        for child in self.plot_frame.winfo_children():
            child.destroy()
        self.canvas = None

    def get_selected_numeric(self):
        sel = self.num_list.curselection()
        if not sel:
            return None
        return self.num_list.get(sel[0])

    def get_selected_categorical(self):
        sel = self.cat_list.curselection()
        if not sel:
            return None
        return self.cat_list.get(sel[0])

    def get_selected_date(self):
        sel = self.date_list.curselection()
        if not sel:
            return None
        return self.date_list.get(sel[0])

    def plot_hist(self):
        if self.df is None:
            messagebox.showinfo("Info", "Сначала загрузите данные.")
            return
        col = self.get_selected_numeric()
        if not col:
            messagebox.showinfo("Info", "Выберите числовую колонку в списке.")
            return
        try:
            fig = fig_histogram(self.df, col)
            self.plot_on_canvas(fig)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def plot_topcat(self):
        if self.df is None:
            messagebox.showinfo("Info", "Сначала загрузите данные.")
            return
        col = self.get_selected_categorical()
        if not col:
            messagebox.showinfo("Info", "Выберите категориальную колонку в списке.")
            return
        try:
            fig = fig_top_categories(self.df, col)
            self.plot_on_canvas(fig)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def plot_corr(self):
        if self.df is None:
            messagebox.showinfo("Info", "Сначала загрузите данные.")
            return
        try:
            fig = fig_corr_heatmap(self.df, self.numeric_cols)
            self.plot_on_canvas(fig)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def plot_timeseries(self):
        if self.df is None:
            messagebox.showinfo("Info", "Сначала загрузите данные.")
            return
        date_col = self.get_selected_date()
        if not date_col:
            messagebox.showinfo("Info", "Выберите колонку с датой.")
            return
        try:
            fig = fig_time_series(self.df, date_col, self.numeric_cols, resample='D')
            self.plot_on_canvas(fig)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _autosize_table_delayed(self, delay=100):
        self.root.after(delay, self._autosize_table)

    def _on_bottom_resize(self, event):
        if self.table_widget:
            self.root.after_idle(self._autosize_table)

    def _autosize_table(self):
        tree = self.table_widget
        if not tree:
            return
        try:
            parent = tree.master
            available = parent.winfo_width()
            if available <= 1:
                self._autosize_table_delayed(200)
                return
            cols = tree['columns']
            n = len(cols)
            if n == 0:
                return
            vsb_width = 15
            min_col_width = 80
            target = max(min_col_width, int((available - vsb_width) / n))
            for c in cols:
                tree.column(c, width=target, stretch=True)
        except Exception:
            pass


if __name__ == '__main__':
    root = tk.Tk()
    app = DataExplorerApp(root)
    root.mainloop()
