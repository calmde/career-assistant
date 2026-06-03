"""
DEPRECATED: Tkinter GUI 已废弃，请使用 Flask Web 界面: python app.py
简单 Tkinter GUI：选择简历（支持 PDF/TXT）、输入城市与关键词，启动爬取并展示结果。
"""
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import json
import os

from find_jobs_from_resume import pipeline


class App:
    def __init__(self, root):
        self.root = root
        root.title('Resume -> Job Finder')

        tk.Label(root, text='简历文件:').grid(row=0, column=0, sticky='e')
        self.resume_var = tk.StringVar()
        tk.Entry(root, textvariable=self.resume_var, width=50).grid(row=0, column=1)
        tk.Button(root, text='选择...', command=self.select_resume).grid(row=0, column=2)

        tk.Label(root, text='城市:').grid(row=1, column=0, sticky='e')
        self.city_var = tk.StringVar(value='北京')
        tk.Entry(root, textvariable=self.city_var).grid(row=1, column=1, sticky='w')

        tk.Label(root, text='关键词(可选，逗号分隔):').grid(row=2, column=0, sticky='e')
        self.kws_var = tk.StringVar()
        tk.Entry(root, textvariable=self.kws_var, width=50).grid(row=2, column=1, columnspan=2, sticky='w')

        tk.Label(root, text='每关键词爬取页数:').grid(row=3, column=0, sticky='e')
        self.pages_var = tk.IntVar(value=2)
        tk.Entry(root, textvariable=self.pages_var, width=5).grid(row=3, column=1, sticky='w')

        tk.Label(root, text='代理文件(可选):').grid(row=4, column=0, sticky='e')
        self.proxies_var = tk.StringVar()
        tk.Entry(root, textvariable=self.proxies_var, width=40).grid(row=4, column=1, sticky='w')
        tk.Button(root, text='选择...', command=self.select_proxies).grid(row=4, column=2)

        tk.Button(root, text='开始爬取并筛选', command=self.run_pipeline).grid(row=5, column=0, columnspan=3, pady=8)

        self.output = scrolledtext.ScrolledText(root, width=80, height=20)
        self.output.grid(row=5, column=0, columnspan=3, padx=8, pady=8)

    def select_resume(self):
        fp = filedialog.askopenfilename(filetypes=[('PDF 文件', '*.pdf'), ('文本文件', '*.txt'), ('所有文件', '*.*')])
        if fp:
            self.resume_var.set(fp)

    def select_proxies(self):
        fp = filedialog.askopenfilename(filetypes=[('文本文件', '*.txt'), ('所有文件', '*.*')])
        if fp:
            self.proxies_var.set(fp)

    def run_pipeline(self):
        resume = self.resume_var.get().strip()
        if not resume or not os.path.exists(resume):
            messagebox.showerror('错误', '请选择有效的简历文件')
            return
        city = self.city_var.get().strip() or '北京'
        kws = [k.strip() for k in self.kws_var.get().split(',')] if self.kws_var.get().strip() else None
        pages = int(self.pages_var.get() or 2)

        self.output.delete('1.0', tk.END)
        self.output.insert(tk.END, '开始任务，可能需要一些时间，日志如下:\n')

        def worker():
            try:
                proxies_file = self.proxies_var.get().strip() or None
                top = pipeline(resume, city=city, keywords=kws, max_pages=pages, top_n=20, out_path=None, proxies_file=proxies_file)
                self.output.insert(tk.END, '\n--- 筛选结果（前20） ---\n')
                for i, item in enumerate(top, 1):
                    job = item.get('job_raw', {})
                    line = f"{i}. {job.get('title')} @ {job.get('company')} — 分数: {item.get('deepseek_score')}\n"
                    self.output.insert(tk.END, line)
            except Exception as e:
                self.output.insert(tk.END, f'任务失败: {e}\n')

        t = threading.Thread(target=worker, daemon=True)
        t.start()


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
