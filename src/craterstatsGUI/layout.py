#  Copyright (c) 2026, Greg Michael
#  Licensed under BSD 3-Clause License. See LICENSE.txt for details.


import customtkinter as ctk

import CTkListbox as ctk_Listbox
import craterstats as cst

def layout_GUI(app):
    # configure window
    app.title("Craterstats-III")
    app.iconbitmap(app.path + r'assets/images/cs.ico')
    ctk.set_widget_scaling(app.scaling)  # can look nicer, but also scales plot image: would need to scale click coords

    # Grid configuration for resizing
    app.grid_columnconfigure(0, weight=0)
    app.grid_columnconfigure(1, weight=0)
    app.grid_columnconfigure(2, weight=0)
    app.grid_columnconfigure(3, weight=1)  # Allow column 3 to resize for image_frame
    app.grid_columnconfigure(4, weight=0)
    app.grid_rowconfigure(0, weight=0)
    app.grid_rowconfigure(1, weight=0)
    app.grid_rowconfigure(2, weight=0)
    app.grid_rowconfigure(3, weight=1)  # Allow to resize for image_frame

    # menu frame
    app.menu_frame = ctk.CTkFrame(app)
    app.menu_frame.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
    app.button_menu_file = ctk.CTkOptionMenu(app.menu_frame, dynamic_resizing=False, values=["Open", "Save...", "Close", "Exit"], command=app.menu_file)
    app.button_menu_file.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    app.button_menu_file.set("File")
    # self.button_menu_export = ctk.CTkOptionMenu(self.menu_frame, dynamic_resizing=False, values=["Map"], command=self.menu_export)
    # self.button_menu_export.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    # self.button_menu_export.set("Export")
    app.button_menu_about = ctk.CTkButton(app.menu_frame, text="About", command=app.menu_about)
    app.button_menu_about.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

    # presentation frame
    app.presentation_frame = ctk.CTkFrame(app)
    app.presentation_frame.grid(row=1, column=0, rowspan=1, padx=5, pady=5, sticky="nsew")
    app.label_presentation = ctk.CTkLabel(master=app.presentation_frame, text="Presentation")
    app.label_presentation.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="")

    app.radiobuttons_presentation = []
    for i, e in enumerate(cst.PRESENTATIONS):
        rb = ctk.CTkRadioButton(master=app.presentation_frame, variable=app.GUIval['set']['presentation'], value=e, text=e, command=app.presentation_event)
        app.radiobuttons_presentation.append(rb)
        if i <= 8:
            rb.grid(row=i % 6 + 1, column=i // 6, pady=3, padx=10, sticky="n")
        else:
            rb.grid(row=i % 6 + 2, column=i // 6, pady=3, padx=10, sticky="n")
    app.label_randomness = ctk.CTkLabel(master=app.presentation_frame, text="Randomness")
    app.label_randomness.grid(row=4, column=1, columnspan=1, padx=10, pady=[10, 0], sticky="")

    # functions frame
    app.functions_frame = ctk.CTkFrame(app)
    app.functions_frame.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="nsew")

    app.label_body = ctk.CTkLabel(app.functions_frame, text="Body")
    app.label_body.grid(row=0, column=0, columnspan=1, padx=(10, 0), pady=(10, 5), sticky="e")
    app.optionmenu_body = ctk.CTkOptionMenu(app.functions_frame, dynamic_resizing=False, values=app.body, command=app.body_event, variable=app.body_val)
    app.optionmenu_body.grid(row=0, column=1, padx=10, pady=(10, 5), sticky="ew")

    app.label_cs = ctk.CTkLabel(master=app.functions_frame, text="Chronology system")
    app.label_cs.grid(row=1, column=0, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.optionmenu_cs = ctk.CTkOptionMenu(app.functions_frame, dynamic_resizing=False, values=[], command=app.chronology_system_event, variable=app.cs_val)
    app.optionmenu_cs.grid(row=1, column=1, padx=10, pady=(5, 5), sticky="ew")

    app.label_epochs = ctk.CTkLabel(app.functions_frame, text="Epochs")
    app.label_epochs.grid(row=2, column=0, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.optionmenu_epochs = ctk.CTkOptionMenu(app.functions_frame, dynamic_resizing=False, values=[], variable=app.GUIval['set']['epochs'], command=app.request_update_event)
    app.optionmenu_epochs.grid(row=2, column=1, padx=10, pady=(5, 5), sticky="ew")

    app.label_equilibrium = ctk.CTkLabel(app.functions_frame, text="Equilibrium function")
    app.label_equilibrium.grid(row=3, column=0, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.optionmenu_equilibrium = ctk.CTkOptionMenu(app.functions_frame, dynamic_resizing=False, values=app.equilibrium, variable=app.GUIval['set']['equilibrium'],
                                                   command=app.request_update_event)
    app.optionmenu_equilibrium.grid(row=3, column=1, padx=10, pady=(5, 5), sticky="ew")

    app.label_title = ctk.CTkLabel(app.functions_frame, text="Title")
    app.label_title.grid(row=4, column=0, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.entry_title = ctk.CTkEntry(app.functions_frame, textvariable=app.GUIval['set']['title'])
    app.entry_title.grid(row=4, column=1, padx=10, pady=(5, 5), sticky="ew")
    app.entry_title.bind("<KeyRelease>", app.on_key_release)

    app.label_isochrons = ctk.CTkLabel(app.functions_frame, text="Isochrons")
    app.label_isochrons.grid(row=5, column=0, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.entry_isochrons = ctk.CTkEntry(app.functions_frame, textvariable=app.GUIval['set']['isochrons'])
    app.entry_isochrons.grid(row=5, column=1, padx=10, pady=(5, 5), sticky="ew")
    app.entry_isochrons.bind("<KeyRelease>", app.on_key_release)

    app.entry_selection = ctk.CTkEntry(app.functions_frame, textvariable=app.GUIval['set']['select'])
    app.entry_selection.grid(row=5, column=1, padx=10, pady=(5, 5), sticky="ew")
    app.entry_selection.bind("<KeyRelease>", app.on_key_release)
    app.entry_selection.grid_remove()  # start hidden

    # range sub-frame
    app.range_frame = ctk.CTkFrame(app.functions_frame)
    app.range_frame.grid(row=6, column=1, columnspan=1, padx=(0, 0), pady=(0, 0), sticky="nsew")

    app.label_xrange = ctk.CTkLabel(app.functions_frame, text="log x-range")
    app.label_xrange.grid(row=6, column=0, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.entry_xrange = ctk.CTkEntry(app.range_frame, width=80, textvariable=app.GUIval['set']['xrange'])
    app.entry_xrange.grid(row=0, column=0, padx=10, pady=(5, 5), sticky="ew")
    app.entry_xrange.bind("<KeyRelease>", app.on_key_release)

    app.label_yrange = ctk.CTkLabel(app.range_frame, text="log y-range")
    app.label_yrange.grid(row=0, column=1, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.entry_yrange = ctk.CTkEntry(app.range_frame, width=80, textvariable=app.GUIval['set']['yrange'])
    app.entry_yrange.grid(row=0, column=2, padx=10, pady=(5, 5), sticky="w")
    app.entry_yrange.bind("<KeyRelease>", app.on_key_release)

    # self.label_ra_offset = ctk.CTkLabel(self.range_frame, text="ra_offset")
    # self.label_ra_offset.grid(row=0, column=3, columnspan=1, padx=(10,0), pady=(5,5), sticky="e")
    # self.entry_ra_offset = ctk.CTkEntry(self.range_frame, textvariable=self.GUIval['set']["ra_offset"])
    # self.entry_ra_offset.grid(row=0, column=4, padx=10, pady=(5,5),sticky="ew")

    # legend frame
    app.legend_frame = ctk.CTkFrame(app)
    app.legend_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

    app.label_legend = ctk.CTkLabel(master=app.legend_frame, text="Legend")
    app.label_legend.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="")

    app.legend_checkboxes = []
    for i, e in enumerate(app.legend_options):
        cb = ctk.CTkCheckBox(master=app.legend_frame, text=e, variable=app.GUIval['set']['legend_elements'][i], command=app.request_update_event)
        cb.grid(row=1 + i % 4, column=i // 4, pady=3, padx=10, sticky="nw")
        app.legend_checkboxes.append(cb)

    # global options frame
    app.global_frame = ctk.CTkFrame(app)
    app.global_frame.grid(row=2, column=2, padx=5, pady=5, sticky="nsew")

    app.label_global = ctk.CTkLabel(master=app.global_frame, text="Other settings")
    app.label_global.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="")

    save_options_i = 6  # first checkbox in save options column
    for i, e in enumerate(app.global_options[:save_options_i]):
        cb = ctk.CTkCheckBox(master=app.global_frame, text=app.global_options_ui[i], variable=app.GUIval['set'][e], command=app.request_update_event)
        cb.grid(row=1 + i % 4, column=i // 4, pady=3, padx=10, sticky="nw")

    # dmin
    app.dmin_frame = ctk.CTkFrame(app.global_frame, fg_color="transparent")
    app.dmin_frame.grid(row=3, column=1, columnspan=1, padx=0, pady=0, sticky="nsew")
    app.entry_dmin = ctk.CTkEntry(app.dmin_frame, width=50, textvariable=app.GUIval['set']['min_diameter'])
    app.entry_dmin.grid(row=0, column=0, pady=3, padx=(5, 0), sticky="nw")
    app.entry_dmin.bind("<KeyRelease>", app.on_key_release)
    app.label_dmin = ctk.CTkLabel(app.dmin_frame, text="d_min")
    app.label_dmin.grid(row=0, column=1, columnspan=1, padx=(5, 0), pady=(0, 0), sticky="e")

    # dref
    app.dref_frame = ctk.CTkFrame(app.global_frame, fg_color="transparent")
    app.dref_frame.grid(row=4, column=1, columnspan=1, padx=0, pady=0, sticky="nsew")
    app.entry_dref = ctk.CTkEntry(app.dref_frame, width=50, textvariable=app.GUIval['set']['ref_diameter'])
    app.entry_dref.grid(row=0, column=0, pady=3, padx=(5, 0), sticky="nw")
    app.entry_dref.bind("<KeyRelease>", app.on_key_release)
    app.label_dref = ctk.CTkLabel(app.dref_frame, text="d_ref")
    app.label_dref.grid(row=0, column=1, columnspan=1, padx=(5, 0), pady=(0, 0), sticky="e")

    # save options frame
    app.label_save = ctk.CTkLabel(master=app.global_frame, text="Save")
    app.label_save.grid(row=0, column=2, columnspan=1, padx=10, pady=5, sticky="")

    for i, e in enumerate(app.global_options[save_options_i:]):  # for now, just tight
        cb = ctk.CTkCheckBox(master=app.global_frame, text=app.global_options_ui[save_options_i + i], variable=app.GUIval['set'][e], command=app.request_update_event)
        cb.grid(row=1 + (i + 1) % 4, column=2, pady=3, padx=10, sticky="nw")

    for i, e in enumerate(app.formats):
        cb = ctk.CTkCheckBox(master=app.global_frame, text=e, variable=app.GUIval['set']['format_elements'][i], command=app.request_update_event)
        cb.grid(row=1 + (i + 2) % 4, column=2, pady=3, padx=10, sticky="nw")

    # plot frame
    app.plot_frame = ctk.CTkFrame(app)
    app.plot_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

    app.label_xxx = ctk.CTkLabel(app.plot_frame, text="Overplots")
    app.label_xxx.grid(row=0, column=0, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="ew")

    app.listbox = ctk_Listbox.CTkListbox(app.plot_frame, command=app.plotlist_select, justify='left')  # height=100,
    app.listbox.grid(row=1, column=0, rowspan=4, padx=10, pady=0, sticky="nsew")

    app.label_source = ctk.CTkLabel(app.plot_frame, text="source")
    app.label_source.grid(row=0, column=1, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.entry_source = ctk.CTkEntry(app.plot_frame, textvariable=app.GUIval['plot']["source"])
    app.entry_source.grid(row=0, column=2, columnspan=3, padx=(10, 100), pady=(5, 5), sticky="ew")
    app.entry_source.bind("<Return>", app.request_update_event)

    app.button_browse = ctk.CTkButton(app.plot_frame, text="Browse...", command=app.browse_source, width=80)
    app.button_browse.grid(row=0, column=4, columnspan=1, padx=(0, 10), pady=(5, 5), sticky="e")

    app.label_area = ctk.CTkLabel(app.plot_frame, text="area")
    app.label_area.grid(row=1, column=1, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.entry_area = ctk.CTkEntry(app.plot_frame, textvariable=app.GUIval['plot']["shp_area"])
    app.entry_area.grid(row=1, column=2, columnspan=3, padx=(10, 100), pady=(5, 5), sticky="ew")
    app.entry_area.bind("<Return>", app.request_update_event)

    app.button_browse_area = ctk.CTkButton(app.plot_frame, text="Browse...", command=app.browse_area, width=80)
    app.button_browse_area.grid(row=1, column=4, columnspan=1, padx=(0, 10), pady=(5, 5), sticky="e")

    app.label_name = ctk.CTkLabel(app.plot_frame, text="name")
    app.label_name.grid(row=2, column=1, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.entry_name = ctk.CTkEntry(app.plot_frame, textvariable=app.GUIval['plot']["name"])
    app.entry_name.grid(row=2, column=2, padx=10, pady=(5, 5), sticky="ew")
    app.entry_name.bind("<KeyRelease>", app.on_key_release)

    app.label_range = ctk.CTkLabel(app.plot_frame, text="range")
    app.label_range.grid(row=2, column=3, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.entry_range = ctk.CTkEntry(app.plot_frame, textvariable=app.GUIval['plot']["range"])
    app.entry_range.grid(row=2, column=4, padx=10, pady=(5, 5), sticky="ew")
    app.entry_range.bind("<KeyRelease>", app.on_key_release)

    app.label_type = ctk.CTkLabel(app.plot_frame, text="plot type")
    app.label_type.grid(row=3, column=1, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.optionmenu_type = ctk.CTkOptionMenu(app.plot_frame, dynamic_resizing=False, values=cst.OPLOT_TYPES, variable=app.GUIval['plot']["type"],
                                            command=app.request_update_event)
    app.optionmenu_type.grid(row=3, column=2, padx=10, pady=(5, 5), sticky="ew")

    app.label_binning = ctk.CTkLabel(app.plot_frame, text="binning")
    app.label_binning.grid(row=3, column=3, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.optionmenu_binning = ctk.CTkOptionMenu(app.plot_frame, dynamic_resizing=False, values=cst.Cratercount.BINNINGS, variable=app.GUIval['plot']["binning"],
                                               command=app.request_update_event)
    app.optionmenu_binning.grid(row=3, column=4, padx=10, pady=(5, 5), sticky="ew")

    app.label_symbol = ctk.CTkLabel(app.plot_frame, text="symbol")
    app.label_symbol.grid(row=4, column=1, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.optionmenu_symbol = ctk.CTkOptionMenu(app.plot_frame, dynamic_resizing=False, values=app.psyms, variable=app.GUIval['plot']["psym"], command=app.request_update_event)
    app.optionmenu_symbol.grid(row=4, column=2, padx=10, pady=(5, 5), sticky="ew")

    app.label_colour = ctk.CTkLabel(app.plot_frame, text="colour")
    app.label_colour.grid(row=4, column=3, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.optionmenu_colour = ctk.CTkOptionMenu(app.plot_frame, dynamic_resizing=False, values=app.colours, variable=app.GUIval['plot']["colour"],
                                              command=app.request_update_event)
    # self.optionmenu_colour = ctk.CTkComboBox(self.plot_frame, values=self.colours, variable=self.GUIval['plot']["colour"],command=self.request_update_event) # works, but over-complicated
    app.optionmenu_colour.grid(row=4, column=4, padx=10, pady=(5, 5), sticky="ew")

    app.label_offset = ctk.CTkLabel(app.plot_frame, text="offset")
    app.label_offset.grid(row=5, column=1, columnspan=1, padx=(10, 0), pady=(5, 5), sticky="e")
    app.entry_offset = ctk.CTkEntry(app.plot_frame, textvariable=app.GUIval['plot']["offset_age"])
    app.entry_offset.grid(row=5, column=2, padx=10, pady=(5, 5), sticky="ew")
    app.entry_offset.bind("<KeyRelease>", app.on_key_release)

    app.button_ra = ctk.CTkButton(app.plot_frame, text="Randomness analysis", state=ctk.DISABLED, command=app.do_randomness_analysis)
    app.button_ra.grid(row=5, column=4, columnspan=1, padx=5, pady=5, sticky="ew")

    # list buttons subframe
    app.list_buttons_frame = ctk.CTkFrame(app.plot_frame, fg_color="transparent")
    app.list_buttons_frame.grid(row=5, column=0, columnspan=1, rowspan=2, padx=5, pady=5, sticky="nsew")
    pad = 2
    app.button_1 = ctk.CTkButton(app.list_buttons_frame, text="New", width=85, command=app.plotlist_new)
    app.button_1.grid(row=0, column=0, padx=pad, pady=pad)
    app.button_2 = ctk.CTkButton(app.list_buttons_frame, text="Duplicate", width=85, command=app.plotlist_duplicate)
    app.button_2.grid(row=1, column=0, padx=pad, pady=pad, sticky="ew")
    app.button_3 = ctk.CTkButton(app.list_buttons_frame, text="Up", width=85, command=app.plotlist_up)
    app.button_3.grid(row=0, column=1, padx=pad, pady=pad, sticky="ew")
    app.button_4 = ctk.CTkButton(app.list_buttons_frame, text="Down", width=85, command=app.plotlist_down)
    app.button_4.grid(row=1, column=1, padx=pad, pady=pad, sticky="ew")
    app.button_5 = ctk.CTkButton(app.list_buttons_frame, text="Delete", width=85, command=app.plotlist_delete)
    app.button_5.grid(row=2, column=0, padx=pad, pady=pad, sticky="ew")

    # plot_toggles sub-frame
    app.plot_toggles_frame = ctk.CTkFrame(app.plot_frame, fg_color="transparent")
    app.plot_toggles_frame.grid(row=6, column=1, columnspan=4, padx=(10, 10), pady=(0, 10), sticky="nsew")
    app.plot_toggles_checkboxes = [
        ctk.CTkCheckBox(master=app.plot_toggles_frame, text=app.plot_toggles_ui[i], variable=app.GUIval['plot'][e], command=app.request_update_event)
        for i, e in enumerate(app.plot_toggles)]
    for i, e in enumerate(app.plot_toggles_checkboxes):
        i1 = i  # if i==0 else i+1
        e.grid(row=1 + i1 % 2, column=i1 // 2, pady=3, padx=0, sticky="nsew")

    # Image Frame (Resizable)
    app.image_frame = ctk.CTkFrame(app)
    app.image_frame.grid(row=0, column=3, columnspan=2, rowspan=4, padx=5, pady=5, sticky="nsew")
    app.image_frame.grid_rowconfigure(0, weight=1)  # Make sure the image inside the frame can expand
    app.image_frame.grid_columnconfigure(0, weight=1)  # Allow resizing for the image column
    app.image_frame.bind("<Configure>", app.resize_image)
    app.image = ctk.CTkLabel(master=app.image_frame, text="", image=app.photo)
    app.image.grid(row=0, column=0, padx=50, pady=50, sticky="nsew")  # Ensure it stretches within the frame

    app.image.bind("<Button-1>", app.on_press)
    app.image.bind("<ButtonRelease-1>", app.on_release)

    # command frame
    app.command_frame = ctk.CTkFrame(app)  # , fg_color="transparent")
    app.command_frame.grid(row=4, column=0, columnspan=5, padx=5, pady=5, sticky="nsew")
    app.command_frame.grid_columnconfigure(0, weight=1)
    app.command_frame.grid_columnconfigure(1, weight=0)
    app.textbox_command = ctk.CTkTextbox(master=app.command_frame, height=60)
    app.textbox_command.grid(row=0, column=0, columnspan=1, padx=(10, 10), pady=5, sticky="nsew")

    app.button_update = ctk.CTkButton(master=app.command_frame, command=app.do_update_event, text="Update", width=100, state=ctk.DISABLED)
    app.button_update.grid(row=0, column=1, padx=10, pady=10, sticky="e")
    app.bind("<Return>", lambda e: app.button_update.cget("state") == "normal" and app.button_update.invoke())

    app.progressbar = ctk.CTkProgressBar(master=app.command_frame)
    app.progressbar.grid(row=1, column=0, columnspan=2, padx=(10, 10), pady=5, sticky="nsew")
    app.progressbar.set(1.0)

    app.bind("<Button-1>", app.remove_entry_focus)