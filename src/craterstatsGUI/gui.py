#  Copyright (c) 2026, Greg Michael
#  Licensed under BSD 3-Clause License. See LICENSE.txt for details.

import argparse
import copy
import hashlib
import json
import multiprocessing
from queue import Empty
import os
import re
import shlex
import time

import tkinter as tk
import customtkinter as ctk
import CTkListbox as ctk_Listbox
from PIL import Image

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

import craterstats as cst
import craterstats.gm as gm
import craterstats.cli as cli

from craterstatsGUI import __version__

class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.path = gm.filename(__file__,'p')
        self.scaling = .9 # widget and plot image scaling - nice at .9, but complicates pixel coords

        self.resize_timer = None
        self.established = False
        self.last_keypress_time = 0
        self.update_timer_id = None

        self.populate_option_names()
        self.create_GUIdict()
        self.layout_GUI()

        self.cps_dict = copy.deepcopy(cst.DEFAULTS['set'])
        self.cp_dicts = [copy.deepcopy(cst.DEFAULTS['plot'])]
        self.set_GUI_values()
        self.update_disabled_controls()

        self.toplevel_window_about = None
        self.update_idletasks()
        self.width,self.height = (0,0)
        self.min_dim = (self.winfo_reqwidth(),self.winfo_reqheight())
        self.geometry(f"{self.min_dim[0]}x{self.min_dim[1]}")
        self.minsize(*self.min_dim)
        self.bind('<Configure>', self.on_resize)

        self.standard_colour = self.button_update.cget('fg_color')
        self.workdir = gm.get_documents_path()
        self.cps = None

        self.queue = multiprocessing.Queue()
        self.process = None
        self.process_finished = False
        self.poll_queue

    def populate_option_names(self):
        fl = cst.Functionslist()
        self.functions = fl.functions

        self.cs = [e['name'].split(', ',1) for e in self.functions['chronology_system']]
        self.body = sorted({e[0] for e in self.cs})
        self.epochs = ['None']+[e['name'].split(', ', 1) for e in self.functions['epochs']]
        self.equilibrium = ['None']+[e['name'] for e in self.functions['equilibrium']]


        image_path = self.path + r"assets/cs.png"
        image = Image.open(image_path)
        self.image_dim = 700
        self.photo = ctk.CTkImage(light_image=image, dark_image=image,size=(self.image_dim,self.image_dim))

        self.legend_options = ['functions', 'name', 'area', 'perimeter', 'number', 'range', 'N(1)', 'age']
        self.legend_codes = 'fnapcrNA'
        self.formats = ['png', 'svg', 'csv']

        self.global_options = ['3 sf', 'mu', 'invert', 'text_halo','ra_show','bins','tight']
        self.global_options_ui = ['3 sf', 'μ-notation', 'invert', 'text halo','randomness','bins','tight']

        self.plot_toggles = ('age_left', 'show_age', 'isochron', 'error_bars', 'resurf', 'resurf_showall')
        self.plot_toggles_ui = ('align age left', 'show age', 'isochron', 'error bars', 'resurf-correction', 'resurf-showall')

        self.psyms = [e[1] for e in cst.MARKERS]
        self.colours = [e[2] for e in cst.PALETTE]

    def create_GUIdict(self):
        GUIval = {}
        for d in cst.DEFAULTS:
            GUIval[d] = {}
            for k, v in cst.DEFAULTS[d].items():
                if k in ('chronology_system', 'epochs', 'equilibrium', 'presentation', 'print_dimensions', 'pt_size', 'ref_diam', 'sig_figs',
                         'style', 'format', 'min_diameter', 'global_area', 'n_samples', 'ra_offset',
                         'type', 'binning'):
                    GUIval[d][k] = ctk.StringVar(value = v if v else 'None')
                elif k in ('title', 'isochrons', 'source', 'name'):
                    GUIval[d][k] = ctk.StringVar(value=v if v else '')
                elif k in {'invert', 'transparent', 'text_halo', 'mu', 'ra_show','tight', 'bins',
                            'snap', 'error_bars', 'hide', 'age_left', 'show_age', 'resurf', 'resurf_showall', 'isochron'}:
                    GUIval[d][k] = ctk.BooleanVar(value = v==1)
                elif k == 'psym':
                    GUIval[d][k] = ctk.StringVar(value=self.psyms[v])
                elif k == 'colour':
                    GUIval[d][k] = ctk.StringVar(value=self.colours[v])
                elif k in ('range', 'offset_age','ra_offset'):
                    GUIval[d][k] = ctk.StringVar(value='')
                else:
                    pass
                    #print(f"Unsupported key: {k}")
                if k == 'sig_figs': # make additional tag
                    GUIval[d]['3 sf'] = ctk.BooleanVar(value = v == 3)

        self.pr_xyranges = {}
        for k in ('xrange','yrange'):
            GUIval['set'][k] = ctk.StringVar(value='')
            self.pr_xyranges[k] = {}

        GUIval['plot']['default_name'] = ctk.StringVar(value='') # stores shortened src name to test if name needed in cs output
        GUIval['set']['legend_elements'] = [ctk.BooleanVar(value=False) for e in self.legend_codes]
        GUIval['set']['format_elements'] = [ctk.BooleanVar(value=False) for e in self.formats]

        self.GUIval = GUIval
        self.body_val = ctk.StringVar(value = '')
        self.cs_val = ctk.StringVar(value = '')


    def set_GUI_values(self):
        """
        read from cps_dict and cp_dicts into current GUI state
        """
        self.listbox.delete(0, "end")
        self.plotlist = []
        self.plotlist_previous_selection = None
        self.pr_range = dict() # to store x,y ranges for different presentations
        self.age_area_result = None
        self.uncertainty_ui_hash = None

        # plot items:
        for d in self.cp_dicts:
            pld = {}
            for k, v in d.items():
                if k == 'psym':
                    pld[k]=self.psyms[v]
                elif k == 'colour':
                    pld[k]=self.colours[v]
                elif k in ('cratercount'):
                    pass
                elif k in ('offset_age','range'):
                    pld[k] = ', '.join(v) if v not in (['0', '0'],['0','inf']) else ''
                else:
                    pld[k] = v
            pld['default_name'] = f"plot {len(self.plotlist) + 1}"
            self.plotlist.append(pld)

        if len(self.plotlist)==0: # put defaults as first plot
            self.plotlist_new(update=False) #self.plotlist_gui2cp(0)
        else: # put last read into gui
            self.plotlist_cp2gui(len(self.plotlist)-1)

        self.plotlist_update(len(self.plotlist)-1,update_event=False)

        for k in ('xrange','yrange'):
            self.GUIval['set'][k].set('') # clear in case not set
            for v in cst.PRESENTATIONS:
                self.pr_xyranges[k][v] = '' # clear GUI memory for different presentations

        # set items:
        for k, v in self.cps_dict.items():
            if k == 'chronology_system':
                match = re.search(r'(.+?),\s*(.+)', v)
                body, fn = (match.group(1), match.group(2))
                self.body_val.set(body)
                self.body_event(body,update_event=False)
                self.cs_val.set(fn)
            elif k in ('font','out','cf','pf','ef','trials','measure'):
                pass
            elif k in ('epochs','equilibrium'):
                if v:
                    self.GUIval['set'][k].set(v)
            elif k in ('invert','tight','mu','text_halo'):
                self.GUIval['set'][k].set(bool(v))
            elif k=='sig_figs':
                self.GUIval['set'][k].set(v==3)
            elif k=='legend':
                for i,e in enumerate(self.legend_codes):
                    self.GUIval['set']['legend_elements'][i].set(e in v)
            elif k=='format':
                for i,e in enumerate(self.formats):
                    self.GUIval['set']['format_elements'][i].set(e in v)
            elif k == 'presentation':
                self.GUIval['set'][k].set(v)
            elif k in ('xrange','yrange'):
                if isinstance((v[0]),str): # defaults are not str
                    self.GUIval['set'][k].set(','.join(v))
            else:
                self.GUIval['set'][k].set(v)


    def prepare_dicts(self):
        """
        translate from dictionaries in GUI convenient format (GUIval/plotlist) to cli prepared format (cps_dict,cp_dicts)
        """

        self.plotlist_gui2cp(self.plotlist_previous_selection) # do this first, so can access current plot for ra

        set_dict = {}
        for k,v0 in self.GUIval['set'].items():
            if k == 'legend_elements':
                set_dict['legend'] = ''.join([c for e,c in zip(v0,self.legend_codes) if e.get()])
                continue
            elif k == 'format_elements':
                set_dict['format'] = {c for e,c in zip(v0,self.formats) if e.get()}
                continue

            v = v0.get()
            if k == '3 sf':
                set_dict['sig_figs'] = 3 if v else 2
            elif v == 'None':
                set_dict[k] = None
            elif k in ('xrange','yrange'):
                match = re.search(r'(.+?),(.+)', v)
                if match:
                    v1, v2 = (match.group(1), match.group(2))
                    set_dict[k] = (v1,v2)
                else:
                    pr = self.GUIval['set']['presentation'].get()
                    set_dict[k] = cst.DEFAULT_XRANGE[pr] if k=='xrange' else cst.DEFAULT_YRANGE[pr]
            elif k in ['n_samples']:
                set_dict[k] = int(v)
            elif k in ['min_diameter']:
                set_dict[k] = float(v)
            elif k in ['ra_offset']:
                set_dict[k] = float(v) if v != '' else 0.
            elif k == 'presentation' and v in ('map', 'sdaa', 'm2cnd'):
                set_dict[k] = v
                set_dict['randomness_analysis'] = self.plotlist[self.plotlist_previous_selection]['source']
                if v in ('sdaa', 'm2cnd'):
                    set_dict['measure'] = v
            else:
                set_dict[k] = v

        cp_dicts = []
        for p in self.plotlist:
            cp = {}
            for k,v in p.items():
                if k == 'colour':
                    cp[k] = self.colours.index(v)
                elif k == 'psym':
                    cp[k] = self.psyms.index(v)
                elif k == 'type':
                    cp[k] = cst.OPLOT_TYPES_SHORT[cli.decode_abbreviation(cst.OPLOT_TYPES, v, allow_ambiguous=True)]
                elif k in ['range','offset_age']:
                    match = re.search(r'(.+?),(.+)', v)
                    if match:
                        cp[k] = [match.group(1),match.group(2)]
                    else:
                        cp[k] = ['0','inf'] if k=='range' else ['0','0']
                else:
                    cp[k] = v

            if cp['source'] != 'None':
                cp_dicts.append(cp)

        if 'randomness_analysis' in set_dict:
            set_dict = {k:set_dict[k] for k in ('randomness_analysis','presentation','title','invert','tight','measure','format') if k in set_dict}
        self.cps_dict = cli.construct_cps_dict(argparse.Namespace(**set_dict), cst.DEFAULTS['set'].copy(), self.functions)
        for k in ('tight','randomness_analysis'):
            if k in set_dict:
                self.cps_dict[k] = set_dict[k]
        self.cp_dicts = cp_dicts

    def prepare_commandline(self):
        """
        translate between dictionaries in GUI convenient format (GUIval/plotlist) and comannd line format (.cs) (via cli prepared format (cps_dict,cp_dicts))
        """
        ABBR_COMMAND_TAG = {
            'chronology_system': 'cs',
            'epochs': 'ep',
            'equilibrium': 'ef',
            'presentation': 'pr',
            'print_dimensions': 'pd',
            'randomness_analysis': 'ra',
            'min_diameter': 'd_min',
            'format':'f',
            'sig_figs':'sf',
        }
        self.prepare_dicts()
        cs=[]
        pr = self.cps_dict['presentation']
        for k,v in self.cps_dict.items():
            if k in ('xrange','yrange'):
                default = v == (cst.DEFAULT_XRANGE[pr] if k == 'xrange' else cst.DEFAULT_YRANGE[pr])
            elif k in ('cf','pf','ef','ep','global_area','text_halo'): # here, cf,pf,ef,ep are objects
                default = True
            elif k == 'randomness_analysis':
                default = False
            elif k == 'presentation':
                default = cst.DEFAULTS['set'][k] == v or v in ('sdaa','m2cnd')
            else:
                default = cst.DEFAULTS['set'][k]==v
            if not default:
                if k in ABBR_COMMAND_TAG:
                    k=ABBR_COMMAND_TAG[k]
                if k in ('cs','ep','ef'): # here, ef,ep are labels
                    v = re.sub(r'[^a-zA-Z0-9_]','', v)
                elif k in ('title'):
                    v = shlex.quote(v)
                elif k in ('f', 'xrange', 'yrange'):
                    v = ' '.join(v)
                elif k in ('measure'):
                    v = ','.join(v)
                elif isinstance(v, bool):
                    v = 1 if v else 0
                cs.append(f"-{k} {v}")

        if self.cps_dict['presentation'] not in ('uncertainty','map','sdaa','m2cnd'):
            for i,cp in enumerate(self.cp_dicts):
                s=[]
                for k,v in cp.items():
                    if k=='default_name':
                        continue
                    elif i>0 and (k in cst.CARRY_OVER_PROPERTIES or (k == 'type' and cp['source'] == self.cp_dicts[i-1]['source'])):
                        default = v == self.cp_dicts[i-1][k]
                    elif k in ('name'):
                        default = v in (cst.DEFAULTS['plot'][k],cp['default_name'])
                    else:
                        default = v == cst.DEFAULTS['plot'][k]
                    if not default:
                        if k in ('source','name'):
                            v = f'"{v}"'
                        elif k in ('offset_age','range'):
                            v = f"{v}".replace("'", "").replace(' ', '')
                        elif k == 'colour':
                            v = cst.PALETTE[v][2].lower()
                        elif k == 'psym':
                            v = cst.MARKERS[v][0]
                        elif isinstance(v, bool):
                            v = 1 if v else 0
                        s.append(f"{k}={v}")
                cs.append("-p "+','.join(s))
        self.cmd = cs

    def draw(self):
        self.cps = cst.Craterplotset(self.cps_dict)
        src = self.GUIval['plot']['source'].get()
        pr = self.cps_dict['presentation']
        if pr == 'map':
            scc = cst.Spatialcount(src)
            self.cps.create_map_plotspace()
            scc.plot(self.cps, grid=True)
            self.cps_dict['out'] = gm.filename(scc.filename, 'pn1','_map')
        elif pr in ('sdaa','m2cnd'):
            ra = cst.Randomnessanalysis(src, out=self.cps.out)
            self.cps.out = gm.filename(ra.ra_file, 'pn')
            ra.run_montecarlo(self.cps.trials, pr) #just read
            ra.calculate_stats()

            measure = self.cps_dict['presentation']
            match None:
                case None:
                    ra.plot_montecarlo_split(self.cps, measure)
                case 0:
                    ra.plot_n_sigma(self.cps, measure)
                case _:
                    ra.plot_map_and_histogram(self.cps, measure, list(ra.montecarlo[measure]['stats'].keys())[args.only - 1])
        else:
            for d in self.cp_dicts:
                if isinstance(d['colour'], int): d['colour'] = self.cps.palette[d['colour']]
            cpl = [cst.Craterplot(d) for d in self.cp_dicts]
            self.cps.craterplot = cpl

            if cpl and self.cps.presentation not in ('sequence', 'uncertainty'):
                self.cps.autoscale(self.cps_dict['xrange'] if self.GUIval['set']['xrange'].get() != '' else None,
                              self.cps_dict['yrange'] if self.GUIval['set']['yrange'].get() != '' else None)

            self.cps.draw()
            if self.cps.presentation == 'uncertainty':
                self.cps.age_area_plot('age',self.age_area_result)

        self.update_image()

    def run_job(self, target, args):
        self.process_finished = False
        queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(target=target, args=(*args, queue))
        self.process.start()
        self.poll_queue(queue)

    def resize_image(self, event):
        self.image_dim = (min(event.width,event.height)-110) / self.scaling # make slightly smaller than padding margin
        #print(self.image_dim)
        self.update_image()


    def update_image(self):
        if self.cps:
            sz = self.cps.fig.get_size_inches()
            dpi = (self.image_dim/max(sz))
            self.cps.fig.set_dpi(dpi)
            canvas = FigureCanvas(self.cps.fig)
            canvas.draw()

            img_array = np.frombuffer(canvas.tostring_argb(), dtype=np.uint8)
            img_array = img_array.reshape(self.cps.fig.canvas.get_width_height()[::-1] + (4,))
            rgba_array = img_array[..., [1, 2, 3, 0]]
            img_pil = Image.fromarray(rgba_array, 'RGBA')
            ctk_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=img_pil.size)

            self.image.configure(image=ctk_img,width=img_pil.size[0],height=img_pil.size[1])
            self.image.update()

            # Force the window to update its size
            self.update_idletasks()
            self.update()



    def layout_GUI(self):

        # configure window
        self.title("Craterstats-III")
        self.iconbitmap(self.path + r'assets/cs.ico')
        ctk.set_widget_scaling(self.scaling)  # can look nicer, but also scales plot image: would need to scale click coords

        # Grid configuration for resizing
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=1)  # Allow column 3 to resize for image_frame
        self.grid_columnconfigure(4, weight=0)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1) # Allow to resize for image_frame

        # menu frame
        self.menu_frame = ctk.CTkFrame(self)
        self.menu_frame.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.button_menu_file = ctk.CTkOptionMenu(self.menu_frame, dynamic_resizing=False, values=["Open", "Save...", "Close", "Exit"], command=self.menu_file)
        self.button_menu_file.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.button_menu_file.set("File")
        # self.button_menu_export = ctk.CTkOptionMenu(self.menu_frame, dynamic_resizing=False, values=["Map"], command=self.menu_export)
        # self.button_menu_export.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        # self.button_menu_export.set("Export")
        self.button_menu_about = ctk.CTkButton(self.menu_frame, text="About", command=self.menu_about)
        self.button_menu_about.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # presentation frame
        self.presentation_frame = ctk.CTkFrame(self)
        self.presentation_frame.grid(row=1, column=0, rowspan=1, padx=5, pady=5, sticky="nsew")
        self.label_presentation = ctk.CTkLabel(master=self.presentation_frame, text="Presentation")
        self.label_presentation.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="")

        self.radiobuttons_presentation = []
        for i, e in enumerate(cst.PRESENTATIONS):
            rb = ctk.CTkRadioButton(master=self.presentation_frame, variable=self.GUIval['set']['presentation'], value=e, text=e,  command=self.presentation_event)
            rb.grid(row=i%6+1, column=i//6, pady=3, padx=10, sticky="n")
            self.radiobuttons_presentation.append(rb)


        # functions frame
        self.functions_frame = ctk.CTkFrame(self)
        self.functions_frame.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="nsew")

        self.label_body = ctk.CTkLabel(self.functions_frame, text="Body")
        self.label_body.grid(row=0, column=0, columnspan=1, padx=(10,0), pady=(10,5), sticky="e")
        self.optionmenu_body = ctk.CTkOptionMenu(self.functions_frame, dynamic_resizing=False, values=self.body, command=self.body_event, variable=self.body_val)
        self.optionmenu_body.grid(row=0, column=1, padx=10, pady=(10,5),sticky="ew")

        self.label_cs = ctk.CTkLabel(master=self.functions_frame, text="Chronology system")
        self.label_cs.grid(row=1, column=0, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.optionmenu_cs = ctk.CTkOptionMenu(self.functions_frame, dynamic_resizing=False, values=[], command=self.chronology_system_event, variable=self.cs_val)
        self.optionmenu_cs.grid(row=1, column=1, padx=10, pady=(5,5), sticky="ew")

        self.label_epochs = ctk.CTkLabel(self.functions_frame, text="Epochs")
        self.label_epochs.grid(row=2, column=0, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.optionmenu_epochs = ctk.CTkOptionMenu(self.functions_frame, dynamic_resizing=False, values=[], variable=self.GUIval['set']['epochs'], command=self.request_update_event)
        self.optionmenu_epochs.grid(row=2, column=1, padx=10, pady=(5,5),sticky="ew")

        self.label_equilibrium = ctk.CTkLabel(self.functions_frame, text="Equilibrium function")
        self.label_equilibrium.grid(row=3, column=0, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.optionmenu_equilibrium = ctk.CTkOptionMenu(self.functions_frame, dynamic_resizing=False, values=self.equilibrium, variable=self.GUIval['set']['equilibrium'], command=self.request_update_event)
        self.optionmenu_equilibrium.grid(row=3, column=1, padx=10, pady=(5,5),sticky="ew")

        self.label_title = ctk.CTkLabel(self.functions_frame, text="Title")
        self.label_title.grid(row=4, column=0, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.entry_title = ctk.CTkEntry(self.functions_frame, textvariable=self.GUIval['set']['title'])
        self.entry_title.grid(row=4, column=1, padx=10, pady=(5,5),sticky="ew")
        self.entry_title.bind("<KeyRelease>", self.on_key_release)

        self.label_isochrons = ctk.CTkLabel(self.functions_frame, text="Isochrons")
        self.label_isochrons.grid(row=5, column=0, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.entry_isochrons = ctk.CTkEntry(self.functions_frame, textvariable=self.GUIval['set']['isochrons'])
        self.entry_isochrons.grid(row=5, column=1, padx=10, pady=(5,5),sticky="ew")
        self.entry_isochrons.bind("<KeyRelease>", self.on_key_release)


        # range sub-frame
        self.range_frame = ctk.CTkFrame(self.functions_frame)
        self.range_frame.grid(row=6, column=1, columnspan=1, padx=(0, 0), pady=(0, 0), sticky="nsew")

        self.label_xrange = ctk.CTkLabel(self.functions_frame, text="x-range")
        self.label_xrange.grid(row=6, column=0, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.entry_xrange = ctk.CTkEntry(self.range_frame, width=100, textvariable=self.GUIval['set']['xrange'])
        self.entry_xrange.grid(row=0, column=0, padx=10, pady=(5,5),sticky="ew")
        self.entry_xrange.bind("<KeyRelease>", self.on_key_release)

        self.label_yrange = ctk.CTkLabel(self.range_frame, text="y-range")
        self.label_yrange.grid(row=0, column=1, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.entry_yrange = ctk.CTkEntry(self.range_frame, width=100, textvariable=self.GUIval['set']['yrange'])
        self.entry_yrange.grid(row=0, column=2, padx=10, pady=(5,5),sticky="w")
        self.entry_yrange.bind("<KeyRelease>", self.on_key_release)

        # self.label_ra_offset = ctk.CTkLabel(self.range_frame, text="ra_offset")
        # self.label_ra_offset.grid(row=0, column=3, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        # self.entry_ra_offset = ctk.CTkEntry(self.range_frame, textvariable=self.GUIval['set']["ra_offset"])
        # self.entry_ra_offset.grid(row=0, column=4, padx=10, pady=(5,5),sticky="ew")


        # legend frame
        self.legend_frame = ctk.CTkFrame(self)
        self.legend_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        self.label_legend = ctk.CTkLabel(master=self.legend_frame, text="Legend")
        self.label_legend.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="")

        self.legend_checkboxes = []
        for i, e in enumerate(self.legend_options):
            cb = ctk.CTkCheckBox(master=self.legend_frame, text=e, variable=self.GUIval['set']['legend_elements'][i], command=self.request_update_event)
            cb.grid(row=1 + i % 4, column=i // 4, pady=3, padx=10, sticky="nw")
            self.legend_checkboxes.append(cb)

        # global options frame
        self.global_frame = ctk.CTkFrame(self)
        self.global_frame.grid(row=2, column=2, padx=5, pady=5, sticky="nsew")

        self.label_global = ctk.CTkLabel(master=self.global_frame, text="Other settings")
        self.label_global.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="")

        save_options_i = 6 # first checkbox in save options column
        for i, e in enumerate(self.global_options[:save_options_i]):
            cb = ctk.CTkCheckBox(master=self.global_frame, text=self.global_options_ui[i], variable=self.GUIval['set'][e], command=self.request_update_event)
            cb.grid(row=1 + i%4, column=i // 4, pady=3, padx=10, sticky="nw")

        # dmin
        self.dmin_frame = ctk.CTkFrame(self.global_frame,fg_color="transparent")
        self.dmin_frame.grid(row=3, column=1, columnspan=1, padx=0, pady=0, sticky="nsew")
        self.entry_dmin = ctk.CTkEntry(self.dmin_frame, width=50, textvariable=self.GUIval['set']['min_diameter'])
        self.entry_dmin.grid(row=0, column=0, pady=3, padx=(5,0), sticky="nw")
        self.entry_dmin.bind("<KeyRelease>", self.on_key_release)
        self.label_dmin = ctk.CTkLabel(self.dmin_frame, text="d_min")
        self.label_dmin.grid(row=0, column=1, columnspan=1, padx=(5,0), pady=(0,0), sticky="e")


        # save options frame
        self.label_save = ctk.CTkLabel(master=self.global_frame, text="Save")
        self.label_save.grid(row=0, column=2, columnspan=1, padx=10, pady=5, sticky="")

        for i, e in enumerate(self.global_options[save_options_i:]): # for now, just tight
            cb = ctk.CTkCheckBox(master=self.global_frame, text=self.global_options_ui[save_options_i+i], variable=self.GUIval['set'][e], command=self.request_update_event)
            cb.grid(row=1 + (i+1)%4, column=2, pady=3, padx=10, sticky="nw")

        for i, e in enumerate(self.formats):
            cb = ctk.CTkCheckBox(master=self.global_frame, text=e, variable=self.GUIval['set']['format_elements'][i], command=self.request_update_event)
            cb.grid(row=1 + (i+2)%4, column=2, pady=3, padx=10, sticky="nw")

        # plot frame
        self.plot_frame = ctk.CTkFrame(self)
        self.plot_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        self.label_xxx = ctk.CTkLabel(self.plot_frame, text="Overplots")
        self.label_xxx.grid(row=0, column=0, columnspan=1, padx=(10,0), pady=(5,5), sticky="ew")

        self.listbox = ctk_Listbox.CTkListbox(self.plot_frame, command=self.plotlist_select,  justify='left') #height=100,
        self.listbox.grid(row=1, column=0,  rowspan=4, padx=10, pady=0, sticky="nsew")

        self.label_source = ctk.CTkLabel(self.plot_frame, text="source")
        self.label_source.grid(row=0, column=1, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.entry_source = ctk.CTkEntry(self.plot_frame, textvariable=self.GUIval['plot']["source"])
        self.entry_source.grid(row=0, column=2, columnspan=3,padx=(10,100), pady=(5,5),sticky="ew")
        self.entry_source.bind("<Return>", self.request_update_event)

        self.button_browse = ctk.CTkButton(self.plot_frame, text="Browse...", command=self.browse_source, width=80)
        self.button_browse.grid(row=0, column=4, columnspan=1, padx=(0,10), pady=(5,5), sticky="e")

        self.label_name = ctk.CTkLabel(self.plot_frame, text="name")
        self.label_name.grid(row=1, column=1, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.entry_name = ctk.CTkEntry(self.plot_frame, textvariable=self.GUIval['plot']["name"])
        self.entry_name.grid(row=1, column=2, padx=10, pady=(5,5),sticky="ew")
        self.entry_name.bind("<KeyRelease>", self.on_key_release)

        self.label_range = ctk.CTkLabel(self.plot_frame, text="range")
        self.label_range.grid(row=1, column=3, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.entry_range = ctk.CTkEntry(self.plot_frame, textvariable=self.GUIval['plot']["range"])
        self.entry_range.grid(row=1, column=4, padx=10, pady=(5,5),sticky="ew")
        self.entry_range.bind("<KeyRelease>", self.on_key_release)

        self.label_type = ctk.CTkLabel(self.plot_frame, text="plot type")
        self.label_type.grid(row=2, column=1, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.optionmenu_type = ctk.CTkOptionMenu(self.plot_frame, dynamic_resizing=False, values=cst.OPLOT_TYPES, variable=self.GUIval['plot']["type"], command=self.request_update_event)
        self.optionmenu_type.grid(row=2, column=2, padx=10, pady=(5,5),sticky="ew")

        self.label_binning = ctk.CTkLabel(self.plot_frame, text="binning")
        self.label_binning.grid(row=2, column=3, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.optionmenu_binning = ctk.CTkOptionMenu(self.plot_frame, dynamic_resizing=False, values=cst.Cratercount.BINNINGS, variable=self.GUIval['plot']["binning"], command=self.request_update_event)
        self.optionmenu_binning.grid(row=2, column=4, padx=10, pady=(5,5),sticky="ew")

        self.label_symbol = ctk.CTkLabel(self.plot_frame, text="symbol")
        self.label_symbol.grid(row=3, column=1, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.optionmenu_symbol = ctk.CTkOptionMenu(self.plot_frame, dynamic_resizing=False, values=self.psyms, variable=self.GUIval['plot']["psym"], command=self.request_update_event)
        self.optionmenu_symbol.grid(row=3, column=2, padx=10, pady=(5,5),sticky="ew")

        self.label_colour = ctk.CTkLabel(self.plot_frame, text="colour")
        self.label_colour.grid(row=3, column=3, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.optionmenu_colour = ctk.CTkOptionMenu(self.plot_frame, dynamic_resizing=False, values=self.colours, variable=self.GUIval['plot']["colour"], command=self.request_update_event)
        self.optionmenu_colour.grid(row=3, column=4, padx=10, pady=(5,5),sticky="ew")

        self.label_offset = ctk.CTkLabel(self.plot_frame, text="offset")
        self.label_offset.grid(row=4, column=1, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
        self.entry_offset = ctk.CTkEntry(self.plot_frame, textvariable=self.GUIval['plot']["offset_age"])
        self.entry_offset.grid(row=4, column=2, padx=10, pady=(5,5),sticky="ew")
        self.entry_offset.bind("<KeyRelease>", self.on_key_release)

        self.button_ra = ctk.CTkButton(self.plot_frame, text="Randomness analysis",state=ctk.DISABLED, command=self.do_randomness_analysis)
        self.button_ra.grid(row=4, column=4, columnspan=1, padx=5, pady=5, sticky="ew")


        # list buttons subframe
        self.list_buttons_frame = ctk.CTkFrame(self.plot_frame,fg_color="transparent")
        self.list_buttons_frame.grid(row=5, column=0, columnspan=1, padx=5, pady=5, sticky="nsew")
        self.button_1 = ctk.CTkButton(self.list_buttons_frame, text="New", width=85, command=self.plotlist_new)
        self.button_1.grid(row=0, column=0, padx=5, pady=5)
        self.button_2 = ctk.CTkButton(self.list_buttons_frame, text="Delete", width=85, command=self.plotlist_delete)
        self.button_2.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.button_3 = ctk.CTkButton(self.list_buttons_frame, text="Up", width=85, command=self.plotlist_up)
        self.button_3.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.button_4 = ctk.CTkButton(self.list_buttons_frame, text="Down", width=85, command=self.plotlist_down)
        self.button_4.grid(row=1, column=1, padx=5, pady=5, sticky="ew")


        # plot_toggles sub-frame
        self.plot_toggles_frame = ctk.CTkFrame(self.plot_frame,fg_color="transparent")
        self.plot_toggles_frame.grid(row=5, column=1, columnspan=4, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.plot_toggles_checkboxes = [ctk.CTkCheckBox(master=self.plot_toggles_frame, text=self.plot_toggles_ui[i], variable=self.GUIval['plot'][e], command=self.request_update_event)
                              for i,e in enumerate(self.plot_toggles)]
        for i,e in enumerate(self.plot_toggles_checkboxes):
            e.grid(row=1+i%2, column=i//2, pady=3, padx=5, sticky="nsew")

        # Image Frame (Resizable)
        self.image_frame = ctk.CTkFrame(self)
        self.image_frame.grid(row=0, column=3, columnspan=2, rowspan=4, padx=5, pady=5, sticky="nsew")
        self.image_frame.grid_rowconfigure(0, weight=1)  # Make sure the image inside the frame can expand
        self.image_frame.grid_columnconfigure(0, weight=1)  # Allow resizing for the image column
        self.image_frame.bind("<Configure>", self.resize_image)
        self.image = ctk.CTkLabel(master=self.image_frame, text="", image=self.photo)
        self.image.grid(row=0, column=0, padx=50, pady=50, sticky="nsew")  # Ensure it stretches within the frame

        self.image.bind("<Button-1>", self.on_press)
        self.image.bind("<ButtonRelease-1>", self.on_release)

        # command frame
        self.command_frame = ctk.CTkFrame(self) #, fg_color="transparent")
        self.command_frame.grid(row=4, column=0, columnspan=5, padx=5, pady=5, sticky="nsew")
        self.command_frame.grid_columnconfigure(0, weight=1)
        self.command_frame.grid_columnconfigure(1, weight = 0)
        self.textbox_command = ctk.CTkTextbox(master=self.command_frame,height=60)
        self.textbox_command.grid(row=0, column=0, columnspan=1,padx=(10, 10), pady=5, sticky="nsew")

        self.button_update = ctk.CTkButton(master=self.command_frame, command=self.do_update_event, text="Update", width=100, state=ctk.DISABLED)
        self.button_update.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        self.progressbar = ctk.CTkProgressBar(master=self.command_frame)
        self.progressbar.grid(row=1, column=0, columnspan=2,padx=(10, 10), pady=5, sticky="nsew")
        self.progressbar.set(1.0)

        self.bind("<Button-1>", self.remove_entry_focus)


    def on_press(self, event):
        self.press = (event.x,event.y)
    def on_release(self, event):
        if self.cps_dict['presentation'] in ('cumulative', 'differential', 'R-plot', 'Hartmann'):
            x0, y0 = self.pixel_to_data_coords(*self.press)
            x1, y1 = self.pixel_to_data_coords(event.x, event.y)
            x0, x1 = (10 ** x0, 10 ** x1)
            if x0>x1:
                x0,x1 = (x1,x0)
            #print(f"click pos: {x0:.02g}, {x1:.02g}")

            current_plot = self.listbox.curselection()
            cpb = self.cps.craterplot[current_plot]
            if cpb.binning != 'none':
                bins = cpb.cratercount.generate_bins(cpb.binning, 10 ** self.cps.xrange)
                bin0 = bins[max(np.searchsorted(bins, x0 * 1.0001) - 1,0)]
                bin1 = bins[min(np.searchsorted(bins, x1 * .9999),len(bins) - 1)]
                x0,x1 = (bin0,bin1)

            #print(f"current plot {current_plot}:",x0,x1)
            self.GUIval['plot']["range"].set(f"{x0:.02g}, {x1:.02g}")
            self.request_update_event()

    def pixel_to_data_coords(self,x,y):
        #self.image.update_idletasks()
        norm_x = x / self.image_dim / self.scaling
        norm_y = 1 - (y / self.image_dim / self.scaling)
        bbox = self.cps.ax.get_position()  # axes position in figure coords
        ax_norm_x = (norm_x - bbox.x0) / (bbox.x1 - bbox.x0)
        ax_norm_y = (norm_y - bbox.y0) / (bbox.y1 - bbox.y0)

        # convert axes-normalized to data coordinates
        ylim0, ylim1 = (np.log10(self.cps.ax.get_ylim()[0]), np.log10(self.cps.ax.get_ylim()[1]))
        x_data = self.cps.ax.get_xlim()[0] + ax_norm_x * (self.cps.ax.get_xlim()[1] - self.cps.ax.get_xlim()[0])
        y_data = ylim0 + ax_norm_y * (ylim1 - ylim0)
        return x_data,y_data

    def plotlist_new(self,update=True):
        i=0 if self.listbox.curselection() is None else self.listbox.curselection()+1
        #print(f"curr:{i} {self.listbox.curselection()}")
        self.plotlist.insert(i, {})
        self.plotlist_gui2cp(i)
        self.plotlist[i]['default_name'] = f"plot {i+1}"
        self.plotlist[i]['name'] = self.plotlist[i]['default_name']
        if update: self.plotlist_update(i)
        self.plotlist_previous_selection = i

    def plotlist_delete(self):
        if len(self.plotlist)>1:
            i=self.listbox.curselection()
            del self.plotlist[i]
            i1=max(i-1,0)
            self.plotlist_previous_selection = None
            self.plotlist_update(i1)

    def plotlist_up(self):
        i=self.listbox.curselection()
        if i>0:
            item = self.plotlist.pop(i)
            self.plotlist.insert(i-1,item)
            self.plotlist_previous_selection = i - 1
            self.plotlist_update(i-1)

    def plotlist_down(self):
        i=self.listbox.curselection()
        if i<len(self.plotlist)-1:
            item = self.plotlist.pop(i)
            self.plotlist.insert(i+1,item)
            self.plotlist_previous_selection = i + 1
            self.plotlist_update(i+1)

    def plotlist_update(self,n,update_event=True):
        self.listbox.delete('all')
        for i,cp in enumerate(self.plotlist):
            self.listbox.insert(i, cp['default_name'])
        self.listbox.activate(n)
        self.listbox.see(n)
        self.plotlist_select(n)
        if update_event:
            self.request_update_event()

    def plotlist_select(self,b):
        i = self.listbox.curselection()
        if self.plotlist_previous_selection is not None:
            self.plotlist_gui2cp(self.plotlist_previous_selection)
        self.plotlist_cp2gui(i)
        #print(self.plotlist[i])
        self.plotlist_previous_selection = i

    def plotlist_gui2cp(self,i):
        for k in self.GUIval['plot']:
            self.plotlist[i][k] = self.GUIval['plot'][k].get()
            if k=='source': # scroll to right end of filename
                self.entry_source.xview_moveto(1)
                self.entry_source.icursor(len(self.entry_source.get()))

    def plotlist_cp2gui(self,i):
        for k in self.GUIval['plot']:
            self.GUIval['plot'][k].set(self.plotlist[i][k])


    def menu_file(self, c):
        self.button_menu_file.set("File")
        match c:
            case 'Open': self.menu_open()
            case 'Close': self.menu_close()
            case 'Save...': self.menu_save()
            case 'Exit': self.quit()


    def menu_open(self):
        self.prepare_commandline()
        file_path = tk.filedialog.askopenfilename(
            title="Select a File",
            filetypes=[("Craterstats files", "*.cs")],
            initialdir=self.workdir,
        )
        if file_path:
            self.workdir = gm.filename(file_path, 'p')
            os.chdir(self.workdir)
            cmd=gm.read_textfile(file_path,ignore_hash=True,ignore_blank=True)
            #print('\n'.join(cmd))
            args0=shlex.split(' '.join(cmd))
            args = cli.get_parser().parse_args(args0)
            args.input = True
            args.input_filename = file_path

            dflt = copy.deepcopy(cst.DEFAULTS)
            self.cps_dict = cli.construct_cps_dict(args, dflt['set'], self.functions)
            try:
                self.cp_dicts = cli.construct_plot_dicts(args, dflt['plot'], self.cps_dict)
            except:
                self.show_error(f"{gm.filename(file_path,'ne')} references invalid file path.\nPlease fix with text editor and retry.")
                return
            for e in self.cp_dicts:
                e['source'] = e['cratercount'].filename # always use full path in gui (relative may be lost on save)
            self.set_GUI_values()
            self.request_update_event()


    def menu_close(self):
        self.cps_dict = copy.deepcopy(cst.DEFAULTS['set'])
        self.cp_dicts = [copy.deepcopy(cst.DEFAULTS['plot'])]
        self.set_GUI_values()

    def menu_save(self):
        self.prepare_commandline()
        cli.set_default_filename(None,self.cps_dict,self.cp_dicts)
        default_filename = self.cps_dict['out']

        file_path = tk.filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".cs",
            filetypes=[("Craterstats files", "*.cs"),("All files", "*.*")],
            initialdir=self.workdir,
            initialfile=default_filename,
        )
        if file_path:
            gm.write_textfile(file_path,self.cmd)
            args = argparse.Namespace(randomness_analysis=False,tight=self.cps_dict['tight'])
            self.cps.out=gm.filename(file_path,'pn')
            cli.write_output_files(args, self.cps, drawn=True, age_area_result=self.age_area_result)
            self.workdir = gm.filename(file_path,'p')

    def show_error(self,msg):
        self.textbox_command.delete("1.0", "end")
        self.textbox_command.tag_config("red", foreground="#ff8888")
        self.textbox_command.insert("1.0", "Error: ", "red")
        self.textbox_command.insert("end", msg)


    def menu_export(self, c):
        self.button_menu_export.set("Export")
        match c:
            case 'PNG':
                self.prepare_commandline()
                cmd = ' '.join(self.cmd+['-f','png','-o','D:/mydocs/tmp/default'])
                a = shlex.split(cmd)
                cli.main(a)

    def menu_about(self):
        if self.toplevel_window_about is None or not self.toplevel_window_about.winfo_exists():
            self.toplevel_window_about = WindowAbout(self)

    def browse_source(self):
        file_path = tk.filedialog.askopenfilename(
            title="Select a File",
            filetypes=[("Crater count files",  ("*.scc", "*.diam", "*.shp", "*.stat"))],
            initialdir=self.workdir,
        )
        if file_path:
            self.entry_source.configure(state = "normal")
            self.entry_source.delete(0, ctk.END)
            self.entry_source.insert(0, file_path)
            self.entry_source.icursor(len(file_path))
            self.entry_source.xview(len(file_path))
            self.entry_source.configure(state="readonly")
            default_name = gm.filename(file_path,'n')
            self.GUIval['plot']['default_name'].set(default_name)
            self.GUIval['plot']['name'].set(default_name)
            self.request_update_event()

    def body_event(self,v,update_event=True):
        values = [e[1] for e in self.cs if e[0] == v]
        self.optionmenu_cs.configure(values=values)
        self.optionmenu_cs.set(values[0])
        self.optionmenu_epochs.configure(values=[e[1] for e in self.epochs if e[0] == v])
        self.optionmenu_epochs.set('None')
        self.chronology_system_event(update_event)

    def chronology_system_event(self,update_event=True,*args): #*args needed because some callback gives value
        self.GUIval['set']['chronology_system'] = ctk.StringVar(value = f"{self.body_val.get()}, {self.cs_val.get()}")
        if update_event:
            self.request_update_event()

    def presentation_event(self):
        pr_old = self.cps_dict['presentation']
        pr_new = self.GUIval['set']['presentation'].get()
        for k in ('xrange','yrange'):
            v = self.GUIval['set'][k].get()
            self.pr_xyranges[k][pr_old] = v
            self.GUIval['set'][k].set(value=self.pr_xyranges[k][pr_new])
        self.request_update_event()

    def request_update_event(self, value=None):
        if self.update_timer_id is not None: # cancel keypress timer if running
            self.after_cancel(self.update_timer_id)

        self.prepare_commandline()
        pr = self.GUIval['set']['presentation'].get()
        need_update_button = pr in ('sdaa','m2cnd') or (pr == 'uncertainty' and self.uncertainty_ui_hash != self.hash_uncertainty_params())
        if need_update_button:
            self.button_update.configure(state=ctk.NORMAL)
            self.button_update.configure(fg_color='red', hover_color='#8B0000')
        else:
            self.do_update_event()

    def do_update_event(self):
        self.prepare_commandline()
        self.textbox_command.delete("0.0", "end")
        self.textbox_command.insert("0.0", 'craterstats ' + ' '.join(self.cmd))
        self.update_idletasks()

        h = self.hash_uncertainty_params()
        if self.cps_dict['presentation'] == 'uncertainty' and self.uncertainty_ui_hash != h:
            self.uncertainty_ui_hash = h
            self.button_update.configure(state=ctk.DISABLED)
            self.button_update.configure(fg_color=self.standard_colour)
            self.update_idletasks()
            self.run_job(age_area_worker, (self.cps_dict,))  # plots after result in queue
        else:
            self.draw()
            self.button_update.configure(state=ctk.DISABLED)
            self.button_update.configure(fg_color=self.standard_colour)
            self.update_disabled_controls()
            self.update_idletasks()

    def update_disabled_controls(self):
        f = self.GUIval['plot']['source'].get()
        shape_present = gm.filename(f,'e') in ('.scc','.shp') and gm.file_exists(f)
        ra_present = shape_present and gm.file_exists(gm.filename(f,'pn1','_ra.txt'))
        self.button_ra.configure(state=ctk.NORMAL if shape_present else ctk.DISABLED)
        self.radiobuttons_presentation[8].configure(state=ctk.NORMAL if shape_present else ctk.DISABLED) # map
        self.radiobuttons_presentation[9].configure(state=ctk.NORMAL if ra_present else ctk.DISABLED) # sdaa
        self.radiobuttons_presentation[10].configure(state=ctk.NORMAL if ra_present else ctk.DISABLED) # m2cnd
        self.legend_checkboxes[7].configure(state=ctk.NORMAL if self.cps_dict['presentation'] == 'sequence' else ctk.DISABLED) # age
        self.label_dmin.configure(state=ctk.NORMAL if self.cps_dict['presentation'] == 'uncertainty' else ctk.DISABLED) # d_min



    def do_randomness_analysis(self):
        f = self.GUIval['plot']['source'].get()
        args = argparse.Namespace(randomness_analysis=f,trials=None,measure=None,only=None,tight=self.cps.tight)
        self.cps.out = f
        self.textbox_command.delete("0.0", "end")
        self.textbox_command.insert("0.0", 'craterstatsGUI -ra ' + f)
        self.update_progress(1, 1, f'\nWriting results to: {gm.filename(f, 'pn1', '_ra*')}\nProcessing...')

        # cps and queue must be non-class variables for multiprocessing
        cps = argparse.Namespace(trials=self.cps.trials,out=self.cps.out,measure=self.cps.measure) # need var analogous to self.cps
        queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(target=randomness_analysis_worker, args=(args, cps, queue))
        self.process.start()
        self.poll_queue(queue)
    def poll_queue(self, queue):
        try:
            while True:
                msg = queue.get_nowait()
                if msg[0] == "progress":
                    _, current, total = msg
                    self.progressbar.set(current / total)
                elif msg[0] == "age-area-result":
                    _, self.age_area_result = msg
                elif msg[0] == "log":
                    _, text = msg
                    self.textbox_command.insert(tk.END, '\n' + text) # CR before to not scroll early
                    self.textbox_command.see(tk.END)
        except Empty:
            pass
        if not self.process.is_alive() and not self.process_finished:
            self.process_finished = True
            self.do_update_event()
        self.after(100, self.poll_queue, queue)

    def on_key_release(self, event):
        self.last_keypress_time = time.time() # Update the last change time when a key is released
        if self.update_timer_id is not None: # If there's an existing timer, cancel it
            self.after_cancel(self.update_timer_id)
        self.update_timer_id = self.after(500, self.request_update_event) # Set a new timer to check for updates after 0.5 seconds

    def on_resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()
        if not self.established:
            if not (width == self.min_dim[0] and height == self.min_dim[1]): return
            self.established = True
            self.width = width
            self.height = height
        if self.width != width or self.height != height:
            self.width = width
            self.height = height
            #print(f"Final window size is: {width}x{height}")
            if self.resize_timer is not None:
                self.after_cancel(self.resize_timer)
            self.resize_timer = self.after(500,self.prepare_dicts)

    def on_exit(self):
        self.quit()

    def remove_entry_focus(self, event):
        if not isinstance(event.widget, tk.Entry):
            self.focus()
    def update_progress(self, current, total, text=None):
        if text:
            self.textbox_command.insert("end",text)
            self.textbox_command.see("end")
        self.progressbar.set(current / total)
        self.after(100, self.update_idletasks)

    def hash_uncertainty_params(self):
        d = {k: self.cps_dict[k] for k in ('xrange','yrange','chronology_system','min_diameter','global_area','n_samples') if k in self.cps_dict}
        return hash_dict(d)


class WindowAbout(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("About")
        self.after(201, lambda :self.iconbitmap(self.master.path + 'assets/cs.ico'))

        self.geometry("700x720")
        self.grid_columnconfigure(0, weight=1)

        self.textbox = ctk.CTkTextbox(self,width=640,height=710,wrap='word')
        self.textbox.grid(row=0, column=0, columnspan=1, padx=20, pady=20, sticky="ew")

        self.textbox.tag_config("bold", foreground="#ffffff")
        self.textbox.tag_config("normal", foreground="#aaaaaa")
        for i, line in enumerate(cst.ABOUT):
            if line != '' and line[0] =='*':
                self.textbox.insert(tk.END, line[1:], "bold")
            else:
                self.textbox.insert(tk.END, line, "normal")
            if i==3:
                self.textbox.insert(tk.END, f" (CraterstatsGUI wrapper: {__version__})", "normal")
            if i<len(cst.ABOUT)-2:
                self.textbox.insert(tk.END, "\n")

        self.button = ctk.CTkButton(self, text="OK", command=self.close)
        self.button.grid(row=1, column=0, padx=20, pady=0, sticky="nsew")

        self.wm_attributes('-topmost', True)
        self.focus_force()
        self.grab_set() # make it modal

    def close(self):
        self.destroy()
        self.toplevel_window_about=None



def randomness_analysis_worker(args, cps, queue): #outside class for pickling reasons
    cli.randomness_analysis(args, cps, progress_queue=queue)

def age_area_worker(cps_dict, queue):
    cps = cst.Craterplotset(cps_dict) # this instance will have no gui elements: picklable
    cps.calculate_time_axis_params()
    age_area_result = cps.compute_age_area(progress_queue=queue)
    queue.put(("age-area-result", age_area_result))

def hash_dict(d):
    dict_json = json.dumps(d, sort_keys=True)
    dict_hash = hashlib.sha256(dict_json.encode()).hexdigest()
    return dict_hash


def main():
    ctk.set_appearance_mode("Dark")  # "System"
    ctk.set_default_color_theme("dark-blue")
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
