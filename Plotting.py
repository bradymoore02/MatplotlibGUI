import os
import sys

import ttkthemes
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2Tk
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import pandas as pd
from datetime import datetime
import numpy as np
from random import randint
from scipy.interpolate import UnivariateSpline as spline
import math
from scipy.optimize import curve_fit as cf
from scipy.signal import savgol_filter
from ttkthemes import ThemedTk, THEMES

'''
This file creates a GUI that enables the user to plot different combinations
of the wetting data saved to this computer.
'''
font = {'family' : 'arial',
        'weight' : 'normal',
        'size'   : 18}
matplotlib.rc('font', **font)


class MainApp(tk.Tk):
    def __init__(self):
        '''
        Initializes the tkinter window and creates the layout and buttons.
        '''
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.title("Wetting Plots")

        self.style = ttk.Style()
        print(self.style.theme_names())
        self.colors = ["blue", "green","red","magenta","yellow","black","cyan","white"]
        self.i = 0
        self.shapes = {"Square":'s',"Circle":'o',"Diamond":'d',"Star":'*',"Pentagon":'p',"Upwards Triangle":'^',"Downwards Triangle":'v'}
        #,'h','.','o','<','>','1','2','3','4','8'
        self.data_on_plot = False

        # creates frames
        self.plotting_frame = tk.Frame()
        self.plotting_frame.grid(row=0, column=1,rowspan="2", sticky="news")
        self.left_frame = tk.Frame()
        self.left_frame.grid(row=0, column=0,sticky="news")
        self.right_frame = tk.Frame()
        self.right_frame.grid(row=0, column=2, sticky="news")

        # sets up plotting frame
        self.fig, self.ax = plt.subplots(1,figsize=[8,6])
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plotting_frame)
        self.canvas.draw()
        self.ax.clear()
        self.canvas.get_tk_widget().pack(expand=1, fill=tk.BOTH)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plotting_frame)
        self.toolbar.update()

        # label for directions
        ttk.Label(self.left_frame, text="Choose which data to plot:", anchor="center").grid(row=0,column=0)
        # buttons to choose data to plot
    ### Left Frame ###
        self.clearbtn = ttk.Button(self.left_frame, text="Clear plot", command=self.clear)
        self.clearbtn.grid(row=20, column=0, sticky="ew")
        self.savebtn = ttk.Button(self.left_frame, text="Save", command=self.save_window)
        self.savebtn.grid(row=21, column=0, sticky="ew")

    ### Right Frame ###

        # Plot title
        ttk.Label(self.right_frame, text="Title:", anchor="e").grid(row=2, column=0, sticky="ew")
        self.title1 = tk.StringVar()
        self.title1.set("Untitled")
        ttk.Entry(self.right_frame, textvariable=self.title1, width=30).grid(row=2, column=1, sticky="ew", columnspan=2)
        self.title1.trace('w',self.update_titles)

        # X axis
        ttk.Label(self.right_frame, text="X-Axis Label:", anchor="e").grid(row=8, column=0, sticky="ew")
        self.x_title = tk.StringVar()
        self.x_title.set("")
        ttk.Entry(self.right_frame, textvariable=self.x_title, width=30).grid(row=8, column=1, sticky="ew", columnspan=2)
        self.x_title.trace('w',self.update_titles)

        # Y axis
        ttk.Label(self.right_frame, text="Y-Axis Label:", anchor="e").grid(row=7, column=0, sticky="ew")
        self.y_title = tk.StringVar()
        self.y_title.set("")
        ttk.Entry(self.right_frame, textvariable=self.y_title, width=30).grid(row=7, column=1, sticky="ew", columnspan=2)
        self.y_title.trace('w',self.update_titles)

        # limits
        ttk.Label(self.right_frame, text="x lims:", anchor="e").grid(row=13, column=0, sticky="ew")
        self.xlow = tk.StringVar()
        self.xup = tk.StringVar()
        self.xlow.set(0)
        self.xup.set(100)
        ttk.Entry(self.right_frame, textvariable=self.xlow, width=5).grid(row=13, column=1, sticky="ew")
        self.xlow.trace('w',self.update_lims)
        ttk.Entry(self.right_frame, textvariable=self.xup, width=5).grid(row=13, column=2, sticky="ew")
        self.xup.trace('w',self.update_lims)

        ttk.Label(self.right_frame, text="y lims:", anchor="e").grid(row=12, column=0, sticky="ew")
        self.ylow = tk.StringVar()
        self.yup = tk.StringVar()
        self.ylow.set(0)
        self.yup.set(100)
        ttk.Entry(self.right_frame, textvariable=self.ylow, width=5).grid(row=12, column=1, sticky="ew")
        self.ylow.trace('w',self.update_lims)
        ttk.Entry(self.right_frame, textvariable=self.yup, width=5).grid(row=12, column=2, sticky="ew")
        self.yup.trace('w',self.update_lims)

        # Choose between scatter and line
        self.types = ["Scatter", "Line"]
        self.type = tk.StringVar()
        self.type.set(self.types[0])
        ttk.Label(self.right_frame, text="Type:", anchor="e").grid(row=1, column=0, sticky="ew")
        ttk.OptionMenu(self.right_frame, self.type, self.type.get(), *self.types).grid(row=1, column=1, columnspan=2, sticky="ew")
        self.type.trace('w', self.update_axes)

        # add another plot
        self.next_line = 18
        self.addbtn = ttk.Button(self.right_frame, text='+', command=self.new_line)

        self.subbtn = ttk.Button(self.right_frame, text='-', command=self.less_data)

        self.addbtn.grid(row=self.next_line, column=0, columnspan=3, sticky='ew')
        self.plot_number = 0
        self.update_titles()
        self.update_lims()


    def new_line(self):
        Line()


    def less_data(self):

        # Remove
        try:
            self.x_labels[len(self.x_labels)-1].destroy()
            self.x_labels.pop()
            self.x_data[len(self.x_data)-1].destroy()
            self.x_data.pop()
            self.y_labels[len(self.y_labels)-1].destroy()
            self.y_labels.pop()
            self.y_data[len(self.y_data)-1].destroy()
            self.y_data.pop()
            self.plot_titles[len(self.plot_titles)-1].destroy()
            self.plot_titles.pop()
            self.x_list[len(self.x_list)-1].destroy()
            self.x_list.pop()
            self.y_list[len(self.y_list)-1].destroy()
            self.y_list.pop()
            self.file_lists[len(self.file_lists)-1].destroy()
            self.file_lists.pop()
            self.file_labels[len(self.file_labels)-1].destroy()
            self.file_labels.pop()
            self.plot_number-=1
        except Exception:
            pass
        if len(self.x_labels)==0:
            self.subbtn.destroy()
            self.addbtn.grid(row=self.next_line, column=0, columnspan=3, sticky='ew')





    #def add_axes(self):

    def choose_axes(self, *args):

        # choose axes
        print(self.options[0])
        self.columns=[]
        try:
            for col in self.files[self.file.get()].columns:
                if type(self.files[self.file.get()][col][0]) != str:
                    self.columns.append(col)
        except Exception:
            print(3)
        print(self.columns)

        menu = self.x_list[0]["menu"]
        menu.delete(0, "end")
        for string in self.columns:
            menu.add_command(label=string,
                             command=lambda value=string: self.x_axis.set(value))
        # Makes variables for the axes

        # Option menus for choosing the axes
        #self.x_list=ttk.OptionMenu(self.right_frame, self.x_axis, self.x_axis.get(), *columns)

        #self.y_list=ttk.OptionMenu(self.right_frame, self.y_axis, self.y_axis.get(), *columns)


        menu = self.y_list[0]["menu"]
        menu.delete(0, "end")
        for string in self.columns:
            menu.add_command(label=string,
                             command=lambda value=string: self.y_axis.set(value))

    def set_xlabel(self, *args):
        self.x_title.set(self.x_axis.get())
        self.update_titles()

    def set_ylabel(self, *args):
        self.y_title.set(self.y_axis.get())
        self.update_titles()

    def update_titles(self, *args):
        plt.title(self.title1.get())
        plt.xlabel(self.x_title.get())
        plt.ylabel(self.y_title.get())
        self.canvas.draw()


    def update_axes(self, *args):
        self.ax.clear()

        try:
            if self.type.get() == "Line":
                self.ax.plot(self.files[self.file.get()][self.x_axis.get()], self.files[self.file.get()][self.y_axis.get()])
            elif self.type.get() == "Scatter":
                self.ax.scatter(self.files[self.file.get()][self.x_axis.get()], self.files[self.file.get()][self.y_axis.get()])
            minx = min(self.files[self.file.get()][self.x_axis.get()])
            maxx = max(self.files[self.file.get()][self.x_axis.get()])
            self.xlow.set(minx -.1*(maxx-minx))
            self.xup.set(maxx+.1*(maxx-minx))

            miny = min(self.files[self.file.get()][self.y_axis.get()])
            maxy = max(self.files[self.file.get()][self.y_axis.get()])
            self.ylow.set(0)
            self.yup.set(maxy + .1*(maxy-miny))
            self.update_lims()
            self.update_titles()
            print(2)
        except Exception:
            print(1)


    def update_lims(self, *args):
        self.ax.set_xlim(float(self.xlow.get()), float(self.xup.get()))
        self.ax.set_ylim(float(self.ylow.get()), float(self.yup.get()))
        self.canvas.draw()


    def clear(self):
        self.ax.clear()
        self.i = 0
        self.canvas.draw()
        self.data_on_plot = False


    def save_window(self):
        if self.data_on_plot:
            win = tk.Toplevel()
            win.geometry("500x150")
            win.title("Save")

            # Entry box for file name
            ttk.Label(win, text="Figure name:").grid(row=0, column=0, sticky='ew')
            self.name = tk.StringVar()
            self.name.set(self.tests[self.material.get()][0].split('/')[-3])
            ttk.Entry(win, textvariable=self.name).grid(row=0,column=1, columnspan=3,sticky="ew")

            # Entry box for file path
            ttk.Label(win, text="Select path:").grid(row=1, column=0, sticky='ew')
            self.save_path = tk.StringVar()
            self.save_path.set('/Users/bradymoore/Desktop/CPMI/Lithium_Wetting/GF-Wetting/')
            ttk.Entry(win, textvariable=self.save_path, width=60).grid(row=1, column=1)

            # Button to confirm choices
            self.save_final = ttk.Button(win, text="Save as", command=self.save)
            self.save_final.grid(row=2,column=0,sticky="ew")

            '''
            self.save_final["state"] = tk.DISABLED
            if self.name.get() != "" and self.save_path.get() != "":
                self.save_final["state"] = tk.NORMAL
            '''
        else:
            # Creates window letting user know that no data is plotted
            win = tk.Toplevel()
            win.geometry("200x75")
            win.title("No Data")
            ttk.Label(win, text="There is no data plotted").grid(row=0, column=0, sticky='ew')
            ttk.Button(win, text="Ok", command=self.exit_window).grid(row=1, column=0, sticky='ew')


    def save(self):
        # get rid of save as window
        self.exit_window()

        # save data to user-specified location
        plt.savefig(f'{self.save_path.get()}{self.name.get()}', dpi=300)


    def exit_window(self):
        for widget in self.winfo_children():
            if widget.winfo_class() == 'Toplevel':
                widget.destroy()


    def on_closing(self):
        '''
        Closes out of app.
        '''
        self.quit()
        self.destroy()

class Line():
    def __init__(self):

        # Creating data structures
        self.x_labels=[]
        self.x_data=[]
        self.y_labels=[]
        self.y_data=[]
        self.files={}
        self.file = tk.StringVar()
        self.file.set('Select file')
        self.columns=[]
        self.options=[]
        self.x_axis = tk.StringVar()
        self.y_axis = tk.StringVar()


        #ttk.OptionMenu(self.right_frame, self.file, self.file.get(), *self.options).grid(row=0, column=1, sticky='ew')
        self.x_axis.trace('w', self.update_axes)
        self.x_axis.trace('w', self.set_xlabel)
        self.y_axis.trace('w', self.update_axes)
        self.y_axis.trace('w', self.set_ylabel)


        self.next_xlabel = ttk.Label(app.right_frame, text="x-axis:", anchor="c")
        self.next_xlabel.grid(row=app.next_line+4, column=0, columnspan=3, sticky="ew")
        self.next_xdata = ttk.Label(app.right_frame, text="Data:", anchor="e")
        self.next_xdata.grid(row=app.next_line+5, column=0, sticky="ew")

        self.x_axis.set('Select Data')
        self.next_xlist=ttk.OptionMenu(app.right_frame, self.x_axis, self.x_axis.get(), *self.columns)
        self.next_xlist.grid(row=app.next_line+5, column=1, sticky='ew')

        # Y axis
        self.next_ylabel = ttk.Label(app.right_frame, text="y-axis:", anchor="c")
        self.next_ylabel.grid(row=app.next_line+2, column=0, columnspan=3,sticky="ew")
        self.next_ydata = ttk.Label(app.right_frame, text="Data:", anchor="e")
        self.next_ydata.grid(row=app.next_line+3, column=0, sticky="ew")


        self.y_axis.set('Select Data')
        self.next_ylist=ttk.OptionMenu(app.right_frame, self.y_axis, self.y_axis.get(), *self.columns)
        self.next_ylist.grid(row=app.next_line+3, column=1, sticky='ew')

        # File list
        ttk.Label(app.right_frame, text='Choose data files:', anchor='e').grid(row=app.next_line+1, column=0, sticky='ew')

        self.databtn =ttk.Button(app.right_frame, text="Select", command=self.select_data)
        self.databtn.grid(row=app.next_line+1, column=1, sticky='ew')

        #title
        app.plot_number+=1
        self.next_title = ttk.Label(app.right_frame, text='Plot #%d'%app.plot_number, anchor='c')
        self.next_title.grid(row=app.next_line, column=0, columnspan=3, sticky='ew')


        app.next_line = app.next_line + 8
        app.addbtn.grid(row=app.next_line, column=1, columnspan=1, sticky='ew')
        app.subbtn.grid(row=app.next_line, column=2, columnspan=1, sticky='ew')

    def select_data(self):
        win = tk.Toplevel()
        win.geometry("300x300")
        ttk.Label(app.right_frame, text="Selected files:").grid(row=0,column=0,sticky="ew")
        self.add = ttk.Button(app.right_frame, text="Add", command=self.select_file)
        self.remove = ttk.Button(app.right_frame, text="Remove", command=self.remove_file)

        self.add.grid(row=0,column=0,sticky="ew")
        self.remove.grid(row=0, column=1, sticky="ew")

    def select_file(self):
        pass
    def remove_file(self):
        pass

    def update_axes(self):
        pass
    def set_xlabel(self):
        pass
    def set_ylabel(self):
        pass

if __name__ == '__main__':
    app = MainApp()
    app.mainloop()
