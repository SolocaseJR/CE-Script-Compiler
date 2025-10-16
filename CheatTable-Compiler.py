import tkinter as tk
from tkinter import scrolledtext, messagebox

cheat_table_texts = []
script_type_labels = []
# Keep a parallel list of frames for each cheat table to allow renumbering
cheat_table_frames = []
# Maintain a list of radio buttons for selecting which cheat table to delete
cheat_table_radios = []
# The index of the currently selected script. Will be initialised after the main window is created.
selected_script_var = None

def identify_script_type(script):
    if "aobscanmodule" in script:
        return "AOB Injection Script"
    elif "define" in script:
        return "Full Injection Script"
    elif "originalcode:" in script:
        return "Normal Injection Script"
    else:
        return "Unknown Script Type"

def update_script_type_labels():
    script_type_counts = {
        "AOB Injection Script": 0,
        "Full Injection Script": 0,
        "Normal Injection Script": 0,
        "Unknown Script Type": 0
    }
    
    for text_widget, label in zip(cheat_table_texts, script_type_labels):
        script = text_widget.get("1.0", tk.END)  # Modify this line
        script_type = identify_script_type(script)
        label.config(text=f"Script Type: {script_type}")
        
        if script_type == "AOB Injection Script":
            script_type_counts["AOB Injection Script"] += 1
        elif script_type == "Full Injection Script":
            script_type_counts["Full Injection Script"] += 1
        elif script_type == "Normal Injection Script":
            script_type_counts["Normal Injection Script"] += 1
        else:
            script_type_counts["Unknown Script Type"] += 1
    
    for i, label in enumerate(script_type_labels):
        script_type = label["text"].split(":")[1].strip()
        count = script_type_counts[script_type]
        label.config(text=f"{script_type} (Count: {count})")
    
    # Update the scrollbar visibility
    update_scrollbar()

def check_script_types():
    while True:
        update_script_type_labels()
        window.update()

def compile_cheat_tables():
    """
    Compile all cheat tables into a single script. Supports mixing AOB, Full and Normal injection scripts.
    Each script is assigned a unique index based on its position and any labels / symbols within are
    suffixed with that index to avoid collisions. Define blocks from Full scripts are consolidated at the
    top of the compiled [ENABLE] section.
    """
    compiled_define = ""
    compiled_enable = ""
    compiled_disable = ""

    # If there are no cheat tables, inform the user
    if not cheat_table_texts:
        messagebox.showwarning("No Scripts", "Please add at least one cheat table script to compile.")
        return

    # Process each cheat table individually
    for idx, text_widget in enumerate(cheat_table_texts):
        cheat_table = text_widget.get("1.0", "end-1c")
        script_type = identify_script_type(cheat_table)
        # Use 1-based index for script numbering
        i = idx + 1

        # Determine positions of [ENABLE] and [DISABLE] markers
        enable_pos = cheat_table.find("[ENABLE]")
        disable_pos = cheat_table.find("[DISABLE]")

        if enable_pos == -1 or disable_pos == -1:
            messagebox.showwarning("Invalid Script", f"Script #{i} is missing [ENABLE] or [DISABLE] sections.")
            return

        define_section = cheat_table[:enable_pos].strip()
        enable_section = cheat_table[enable_pos + len("[ENABLE]"):disable_pos].strip()
        disable_section = cheat_table[disable_pos + len("[DISABLE]"):].strip()

        if script_type == "AOB Injection Script":
            # Modify labels to include index to avoid conflicts
            mod_enable = enable_section
            mod_enable = mod_enable.replace("INJECT", f"INJECT{i}")
            mod_enable = mod_enable.replace("return", f"return{i}")
            mod_enable = mod_enable.replace("newmem", f"newmem{i}")
            mod_enable = mod_enable.replace("code", f"code{i}")

            mod_disable = disable_section
            mod_disable = mod_disable.replace("INJECT", f"INJECT{i}")
            mod_disable = mod_disable.replace("newmem", f"newmem{i}")

            compiled_enable += f"// AOB Injection Script #{i}\n{mod_enable}\n\n"
            compiled_disable += f"// AOB Injection Script #{i} Disable\n{mod_disable}\n\n"

        elif script_type == "Full Injection Script":
            # Collect define section and modify names
            mod_define = define_section
            mod_define = mod_define.replace("address", f"address{i}")
            mod_define = mod_define.replace("bytes", f"bytes{i}")
            compiled_define += f"{mod_define}\n"

            # Modify enable section to include index
            mod_enable = enable_section
            mod_enable = mod_enable.replace("address", f"address{i}")
            mod_enable = mod_enable.replace("bytes", f"bytes{i}")
            mod_enable = mod_enable.replace("newmem", f"newmem{i}")
            mod_enable = mod_enable.replace("code", f"code{i}")
            mod_enable = mod_enable.replace("return", f"return{i}")

            # Modify disable section to include index
            mod_disable = disable_section
            mod_disable = mod_disable.replace("address:", f"address{i}:")
            mod_disable = mod_disable.replace("address", f"address{i}")
            mod_disable = mod_disable.replace("bytes", f"bytes{i}")
            mod_disable = mod_disable.replace("newmem", f"newmem{i}")

            compiled_enable += f"// Full Injection Script #{i}\n{mod_enable}\n\n"
            compiled_disable += f"// Full Injection Script #{i} Disable\n{mod_disable}\n\n"

        elif script_type == "Normal Injection Script":
            # Modify enable section labels
            mod_enable = enable_section
            mod_enable = mod_enable.replace("originalcode", f"originalcode{i}")
            mod_enable = mod_enable.replace("returnhere", f"returnhere{i}")
            mod_enable = mod_enable.replace("newmem", f"newmem{i}")
            mod_enable = mod_enable.replace("exit", f"exit{i}")

            # Modify disable section
            mod_disable = disable_section
            mod_disable = mod_disable.replace("newmem", f"newmem{i}")

            compiled_enable += f"// Normal Injection Script #{i}\n{mod_enable}\n\n"
            compiled_disable += f"// Normal Injection Script #{i} Disable\n{mod_disable}\n\n"

        else:
            messagebox.showwarning("Unknown Script Type", f"Script #{i} could not be recognised.")
            return

    # Construct final compiled script
    compiled_script = "[ENABLE]\n"
    if compiled_define.strip():
        compiled_script += compiled_define.strip() + "\n\n"
    compiled_script += compiled_enable
    compiled_script += "[DISABLE]\n"
    compiled_script += compiled_disable

    # Display the compiled script in the GUI
    compiled_text.config(state=tk.NORMAL)
    compiled_text.delete("1.0", "end")
    compiled_text.insert("1.0", compiled_script)
    compiled_text.config(state=tk.DISABLED)

assembly_script_counts = {
        "Cheat Table Script": 0
    }

def add_cheat_table():
    """
    Add a new cheat table area to the GUI. The script number is derived from the current
    number of cheat tables instead of a running counter so numbers stay contiguous if tables are deleted.
    """
    # Determine the index for this cheat table
    script_number = len(cheat_table_frames) + 1

    # Create a new label frame for the cheat table
    cheat_table_frame = tk.LabelFrame(
        cheat_tables_inner_frame,
        text=f"Cheat Table Script #{script_number}",
        fg="black",
        font=("Candara", 10, "bold")
    )
    cheat_table_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
    cheat_table_frames.append(cheat_table_frame)

    # Create a new text widget for the cheat table
    cheat_table_text = scrolledtext.ScrolledText(cheat_table_frame, width=50, height=10)
    cheat_table_text.pack(side=tk.TOP, padx=10, pady=(10, 5))
    cheat_table_texts.append(cheat_table_text)

    # Create a corresponding script type label
    script_type_label = tk.Label(cheat_table_frame, text="Unknown Script Type", fg="black", font=("Segoe UI", 9, "bold"))
    script_type_label.pack(side=tk.TOP, padx=10, pady=(0, 5))
    script_type_labels.append(script_type_label)

    # Add a radio button to allow selecting this script for deletion. A value of
    # `script_number` will later correspond to its index (1-based). The radio
    # buttons all share the same variable `selected_script_var`, which is set
    # after the main window has been created. When a radio is selected the
    # corresponding value will be stored in `selected_script_var`.
    select_radio = tk.Radiobutton(
        cheat_table_frame,
        text="Select",
        variable=selected_script_var,
        value=script_number
    )
    # Pack the radio button towards the top with a left anchor so it aligns
    # nicely within the frame.
    select_radio.pack(side=tk.TOP, padx=10, anchor="w")
    cheat_table_radios.append(select_radio)

    # Enable delete button if at least one table exists
    delete_button.config(state=tk.NORMAL)

    # Update numbering labels in case of prior deletions
    update_script_numbers()

    # Update the scrollbar visibility
    update_scrollbar()

def delete_cheat_table():
    """
    Remove a cheat table from the GUI. If the user has selected a script via the
    radio buttons, that specific table will be removed. Otherwise, the most
    recently added table will be removed. After removal, all tables are
    re-numbered to maintain a contiguous sequence. The radio button selection
    will be cleared.
    """
    # Only proceed if there is at least one cheat table
    if cheat_table_frames:
        # Retrieve the user-selected script index. A value of 0 or an out-of-range
        # value means no valid selection was made.
        try:
            selected_idx = selected_script_var.get()
        except Exception:
            selected_idx = 0
        # Determine which index to delete (0-based)
        if selected_idx <= 0 or selected_idx > len(cheat_table_frames):
            delete_index = len(cheat_table_frames) - 1  # default to last
        else:
            delete_index = selected_idx - 1
        # Remove the selected widgets from all tracking lists
        frame = cheat_table_frames.pop(delete_index)
        text_widget = cheat_table_texts.pop(delete_index)
        label_widget = script_type_labels.pop(delete_index)
        radio_widget = cheat_table_radios.pop(delete_index)

        # Destroy the actual widgets
        text_widget.destroy()
        label_widget.destroy()
        frame.destroy()
        radio_widget.destroy()

        # Reset the selection; user must re-select after deletion
        selected_script_var.set(0)

        # Re-number remaining cheat table frames and update radio values
        update_script_numbers()

    # Disable the delete button if there are no tables left
    if not cheat_table_frames:
        delete_button.config(state=tk.DISABLED)

    # Always update the scrollbar visibility after removal
    update_scrollbar()

def update_script_numbers():
    """
    Ensure each cheat table frame is labeled with a contiguous script number and
    that each associated radio button has the correct value corresponding to
    its 1-based index. Called when tables are added or removed.
    """
    for idx, frame in enumerate(cheat_table_frames):
        # Update frame title
        frame.config(text=f"Cheat Table Script #{idx + 1}")
        # Update corresponding radio button value if it exists
        if idx < len(cheat_table_radios):
            cheat_table_radios[idx].config(value=idx + 1)

def copy_compiled_cheat_tables():
    compiled_script = compiled_text.get("1.0", "end-1c")
    window.clipboard_clear()
    window.clipboard_append(compiled_script)
    messagebox.showinfo("Copy Success", "Compiled Cheat Table has been copied to clipboard!")

def update_scrollbar():
    cheat_tables_canvas.update_idletasks()
    cheat_tables_canvas.configure(scrollregion=cheat_tables_canvas.bbox("all"))
    if cheat_tables_canvas.winfo_height() < cheat_tables_canvas.bbox("all")[3]:
        cheat_tables_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    else:
        cheat_tables_scrollbar.pack_forget()

# Create the main window
window = tk.Tk()
window.title("Cheat Table Script Compiler - @solocase")

# Initialise the variable used by radio buttons to select a script. A value of 0 means no selection.
selected_script_var = tk.IntVar(value=0)

# Maximize the window
window.state('zoomed')

# Get screen width and height
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

# Calculate window size based on screen width and height
window_width = int(screen_width * 0.8)
window_height = int(screen_height * 0.8)
window.geometry(f"{window_width}x{window_height}")

# Create a frame for the cheat tables
cheat_tables_frame = tk.Frame(window)
cheat_tables_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

# Create a canvas for the cheat tables
cheat_tables_canvas = tk.Canvas(cheat_tables_frame)
cheat_tables_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create a frame to hold the cheat tables and the add/delete buttons
cheat_tables_inner_frame = tk.Frame(cheat_tables_canvas)

# Create a scrollbar for the canvas
cheat_tables_scrollbar = tk.Scrollbar(cheat_tables_frame, orient=tk.VERTICAL, command=cheat_tables_canvas.yview, width=25)
cheat_tables_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Configure the canvas to use the scrollbar
cheat_tables_canvas.configure(yscrollcommand=cheat_tables_scrollbar.set)

# Create a window inside the canvas
cheat_tables_canvas.create_window((0, 0), window=cheat_tables_inner_frame, anchor="nw")

# Create a button to add cheat tables
add_button = tk.Button(cheat_tables_inner_frame, text="Add Cheat Table", command=add_cheat_table)
add_button.pack(side=tk.TOP, padx=10, pady=5, anchor="nw")

# Create a button to delete cheat tables
delete_button = tk.Button(cheat_tables_inner_frame, text="Delete Cheat Table", command=delete_cheat_table, state=tk.DISABLED)
delete_button.pack(side=tk.TOP, padx=10, pady=5, anchor="nw")

# Create a frame for the compiled script
compiled_frame = tk.Frame(window)
compiled_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

# Create a text widget to display the compiled script
compiled_text = scrolledtext.ScrolledText(compiled_frame, width=60, height=20)
compiled_text.pack(fill=tk.BOTH, expand=True)


# Create a frame for the buttons
button_frame = tk.Frame(compiled_frame)
button_frame.pack(side=tk.TOP, pady=5)

# Create a button to compile the cheat tables
compile_button = tk.Button(button_frame, text="Compile Scripts", command=compile_cheat_tables)
compile_button.pack(side=tk.LEFT, padx=5)

# Create a button to copy the compiled cheat tables
copy_button = tk.Button(button_frame, text="Copy Compiled Scripts", command=copy_compiled_cheat_tables)
copy_button.pack(side=tk.LEFT, padx=5)

# Start the script type checking loop in a separate thread
window.after(10, check_script_types)

# Update the scrollbar visibility
update_scrollbar()

# Start the GUI event loop
window.mainloop()