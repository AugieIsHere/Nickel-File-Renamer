import os
import json
import requests
import threading
import queue
from typing import List, Dict, Tuple
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NickelFileRenamer:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            messagebox.showerror("Error", "Please set OPENROUTER_API_KEY in your .env file")
            raise ValueError("OpenRouter API key not found")
            
        self.window = tk.Tk()
        self.window.title("Nickel File Renamer")
        self.window.geometry("1000x700")
        
        # Set ttk style for checkboxes in treeview
        self.setup_styles()
        
        # Store the root directory
        self.root_directory = None
        
        # Store items as tuples (path, is_folder)
        self.selected_items: List[Tuple[str, bool]] = []
        self.rename_suggestions: Dict[str, str] = {}
        
        # Saved instructions presets, last selected preset, and last selected model
        self.instructions_presets, self.last_selected_preset_name, self.last_selected_model_name = self.load_instructions_presets()
        
        # Available models for OpenRouter
        self.models = [
            # Anthropic models
            "anthropic/claude-3-opus-20240229",
            "anthropic/claude-3-sonnet-20240229", 
            "anthropic/claude-3-haiku-20240307",
            # OpenAI models
            "openai/gpt-4o-2024-05-13",
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
            # Google models
            "google/gemini-1.5-pro-latest",
            "google/gemini-1.5-flash-latest",
            # Mistral models
            "mistralai/mistral-large-latest",
            "mistralai/mistral-medium-latest",
            "mistralai/mistral-small-latest",
            # Meta models
            "meta/llama-3-70b-instruct",
            "meta/llama-3-8b-instruct",
            # Cohere models
            "cohere/command-r-plus",
            "cohere/command-r",
            # DeepSeek models (Updated 03/27/2025)
            "deepseek/deepseek-chat-v3-0324:free",
            "deepseek/deepseek-chat-v3-0324",
            "deepseek/deepseek-r1",
            "deepseek/deepseek-r1:free"
        ]

        # Bind the closing event
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # First prompt the user to select a root directory
        self.select_root_directory()

    def load_instructions_presets(self):
        """Load saved instruction presets, last selected preset, and last selected model from file"""
        presets_file = "instruction_presets.json"
        last_selected_preset = None
        last_selected_model = None
        default_presets = {
            "Clear and organized": "Suggest clearer, organized names for these items",
            "Lowercase with underscores": "Convert all names to lowercase and replace spaces with underscores",
            "Add date prefix": "Add today's date as a prefix (YYYY-MM-DD) to all names",
            "Descriptive names": "Create more descriptive names based on likely content",
            "Standardize format": "Standardize naming across all files following a consistent pattern"
        }
        
        if os.path.exists(presets_file):
            try:
                with open(presets_file, 'r') as f:
                    data = json.load(f)
                    last_selected_preset = data.pop('_last_selected', None) # Extract last selected preset
                    last_selected_model = data.pop('_last_selected_model', None) # Extract last selected model
                    return data, last_selected_preset, last_selected_model
            except Exception as e:
                print(f"Error loading presets: {e}") # Log error
                return default_presets, None, None
        else:
            return default_presets, None, None
            
    def save_instructions_presets(self):
        """Save instruction presets, last selected preset, and last selected model to file"""
        presets_file = "instruction_presets.json"
        try:
            # Create a copy to avoid modifying the live dict permanently
            data_to_save = self.instructions_presets.copy()
            
            # Add the currently selected preset name
            current_preset = self.preset_var.get()
            if current_preset in data_to_save: # Only save if it's a valid preset
                 data_to_save['_last_selected'] = current_preset

            # Add the currently selected model name
            current_model = self.model_var.get()
            # Basic check if model seems valid (has '/') - could be more robust
            if '/' in current_model: 
                data_to_save['_last_selected_model'] = current_model
            
            with open(presets_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)
        except Exception as e:
            # Don't show popup on close, maybe log instead?
                json.dump(presets_to_save, f, indent=2)
        except Exception as e:
            # Don't show popup on close, maybe log instead?
            print(f"Error saving presets: {str(e)}") 
            # messagebox.showerror("Error", f"Failed to save presets: {str(e)}") # Avoid popup on close

    def on_closing(self):
        """Handle window closing: save presets and destroy window."""
        self.save_instructions_presets()
        self.window.destroy()

    def setup_styles(self):
        """Setup ttk styles for the application"""
        self.style = ttk.Style()
        # Configure treeview to show checkboxes
        self.style.configure("Treeview", rowheight=25)
        
    def select_root_directory(self):
        """Prompt user to select a root directory before showing the main UI"""
        root_dir = filedialog.askdirectory(title="Select Root Directory")
        if not root_dir:
            # If user cancels, exit program
            self.window.destroy()
            return
            
        self.root_directory = root_dir
        
        # Try to force focus back to the main window and process idle tasks
        self.window.focus_force() 
        self.window.update_idletasks() # Process pending events
        # Now set up the main UI immediately
        self.setup_ui() 

    def setup_ui(self):
        """Set up the main UI after selecting a root directory"""
        # Main container - left panel for directory tree, right panel for operations
        main_pane = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Directory tree
        left_frame = ttk.Frame(main_pane, width=300)
        main_pane.add(left_frame, weight=1)
        
        # Directory tree
        self.setup_directory_tree(left_frame)
        
        # Right panel - Controls and results
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=2)
        
        # Selection info and controls
        selection_frame = ttk.LabelFrame(right_frame, text="Selected Items")
        selection_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Button to clear selection
        ttk.Button(selection_frame, text="Clear Selection", 
                  command=self.clear_selection).pack(anchor=tk.W, padx=5, pady=5)
        
        # Selected items view
        self.setup_selected_items_view(selection_frame)
        
        # AI options frame
        ai_frame = ttk.LabelFrame(right_frame, text="AI Settings")
        ai_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Model selection
        ttk.Label(ai_frame, text="AI Model:").pack(side=tk.LEFT, padx=5, pady=5)
        
        # Set initial model based on saved value or default
        initial_model = self.models[0] # Default to first in list
        if self.last_selected_model_name:
             # Check if the saved model is in our default list or just use it directly
             # (Allows custom models entered by user to be saved/restored)
             initial_model = self.last_selected_model_name
             # Optional: Add saved model to list if not present?
             # if initial_model not in self.models:
             #    self.models.insert(0, initial_model) # Add to beginning

        # Make combobox editable to allow custom model input
        self.model_var = tk.StringVar(value=initial_model)
        model_dropdown = ttk.Combobox(ai_frame, textvariable=self.model_var, values=self.models, width=40)
        model_dropdown.pack(side=tk.LEFT, padx=5, pady=5)
        # Set state to 'normal' and ensure it can take focus
        model_dropdown.configure(state='normal', takefocus=True) 
        
        # Add help button for models
        ttk.Button(ai_frame, text="?", width=2, 
                  command=self.show_model_help).pack(side=tk.LEFT, padx=2, pady=5)
        
        # Rename instructions frame
        rename_frame = ttk.LabelFrame(right_frame, text="Rename Instructions")
        rename_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Instructions entry row
        instructions_entry_frame = ttk.Frame(rename_frame)
        instructions_entry_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Instructions entry - changed from Entry to Text widget for more space
        instruction_frame = ttk.Frame(instructions_entry_frame)
        instruction_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.rename_instructions = tk.Text(instruction_frame, width=80, height=4, wrap=tk.WORD)
        self.rename_instructions.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.rename_instructions.insert("1.0", "Suggest clearer, organized names for these items")
        # Add scrollbar for text widget
        instructions_scrollbar = ttk.Scrollbar(instruction_frame, orient=tk.VERTICAL, command=self.rename_instructions.yview)
        instructions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.rename_instructions.config(yscrollcommand=instructions_scrollbar.set)
        # Explicitly ensure it's editable and can take focus
        self.rename_instructions.configure(state='normal', takefocus=True)
        
        # Presets dropdown
        presets_frame = ttk.Frame(rename_frame)
        presets_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(presets_frame, text="Presets:").pack(side=tk.LEFT)
        
        # Create dropdown for saved presets
        preset_names = list(self.instructions_presets.keys())
        self.preset_var = tk.StringVar()
        
        # Set initial preset based on saved value or default
        initial_preset = None
        if self.last_selected_preset_name and self.last_selected_preset_name in preset_names:
            initial_preset = self.last_selected_preset_name
        elif preset_names:
             initial_preset = preset_names[0] # Fallback to first preset

        if initial_preset:
             self.preset_var.set(initial_preset)
            
        self.preset_dropdown = ttk.Combobox(presets_frame, textvariable=self.preset_var, 
                                           values=preset_names, width=30)
        self.preset_dropdown.pack(side=tk.LEFT, padx=5)

        # Apply the initial preset's instruction text if one was set
        if initial_preset:
            self.load_preset() # Call load_preset to update the instruction entry
        
        # Load preset button
        ttk.Button(presets_frame, text="Load", 
                  command=self.load_preset).pack(side=tk.LEFT, padx=2)
                  
        # Save preset button
        ttk.Button(presets_frame, text="Save Current", 
                  command=self.save_preset).pack(side=tk.LEFT, padx=2)
                  
        # Delete preset button
        ttk.Button(presets_frame, text="Delete", 
                  command=self.delete_preset).pack(side=tk.LEFT, padx=2)
        
        # Get suggestions button in its own frame
        suggestions_btn_frame = ttk.Frame(rename_frame)
        suggestions_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Store the suggestions button to disable/enable it
        self.suggestions_button = ttk.Button(suggestions_btn_frame, text="Get AI Suggestions", 
                                            command=self.get_ai_suggestions)
        self.suggestions_button.pack(side=tk.LEFT, padx=5, pady=5) # Align left

        # Status label (moved here)
        self.status_label = ttk.Label(suggestions_btn_frame, text="", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=5, pady=5) # Align left, next to button
        
        # Results frame
        results_frame = ttk.LabelFrame(right_frame, text="Rename Suggestions")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a treeview for showing original and suggested names
        self.results_tree = ttk.Treeview(results_frame, columns=("Original", "Suggested", "Type"),
                                       show="headings", selectmode="extended")
        self.results_tree.heading("Original", text="Original Name")
        self.results_tree.heading("Suggested", text="Suggested Name")
        self.results_tree.heading("Type", text="Type")
        self.results_tree.column("Original", width=200)
        self.results_tree.column("Suggested", width=200)
        self.results_tree.column("Type", width=80)
        self.results_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bind double-click for editing suggested names
        self.results_tree.bind("<Double-1>", self.on_results_tree_double_click)
        
        # Results buttons frame
        results_buttons_frame = ttk.Frame(results_frame)
        results_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(results_buttons_frame, text="Select All", 
                  command=self.select_all_suggestions).pack(side=tk.LEFT, padx=5)
        ttk.Button(results_buttons_frame, text="Deselect All", 
                  command=self.deselect_all_suggestions).pack(side=tk.LEFT, padx=5)
        ttk.Button(results_buttons_frame, text="Reject Selected", 
                  command=self.reject_selected_suggestions).pack(side=tk.LEFT)
        
        # Apply button
        self.apply_button = ttk.Button(right_frame, text="Apply Selected Renames", 
                                      command=self.apply_renames)
        self.apply_button.pack(pady=10) # Restore original padding or adjust as needed
                  
        # Force focus back to the main window, then set focus to the entry after a delay
        self.window.focus_force() 
        self.window.after(100, self.rename_instructions.focus_set)

    def setup_directory_tree(self, parent_frame):
        """Set up the directory tree browser in the left panel"""
        # Label for the directory tree
        ttk.Label(parent_frame, text=f"Root: {self.root_directory}").pack(anchor=tk.W, padx=5, pady=2)
        
        # Frame for the tree
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create the directory treeview with checkbox column
        self.dir_tree = ttk.Treeview(tree_frame, columns=("Selected", "Type"), 
                                    show="tree headings", selectmode="browse")
        self.dir_tree.heading("#0", text="Path")
        self.dir_tree.heading("Selected", text="")  # Checkbox column
        self.dir_tree.heading("Type", text="Type")
        self.dir_tree.column("#0", width=250)
        self.dir_tree.column("Selected", width=30, anchor=tk.CENTER)
        self.dir_tree.column("Type", width=50)
        self.dir_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, 
                                command=self.dir_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.dir_tree.config(yscrollcommand=scrollbar.set)
        
        # Populate the tree with the root directory
        self.populate_directory_tree()
        
        # Bind events
        # Checkbox click handler (handles single left-clicks on checkbox column)
        self.dir_tree.bind("<ButtonRelease-1>", self.on_tree_checkbox_click)
        # Double-click handler (for toggling open/close)
        self.dir_tree.bind("<Double-1>", self.on_dir_tree_double_click)
        # Event handler for when a node is opened
        self.dir_tree.bind("<<TreeviewOpen>>", self.on_folder_expanded)

        # Context menu
        self.create_tree_context_menu()

    def on_tree_checkbox_click(self, event):
        """Handle clicks on the checkbox column"""
        # Identify the region clicked
        region = self.dir_tree.identify_region(event.x, event.y)
        # If clicked on a cell in the checkbox column
        if region == "cell" and self.dir_tree.identify_column(event.x) == "#1":
            item_id = self.dir_tree.identify_row(event.y)
            if item_id:
                # Toggle checkbox state
                current_value = self.dir_tree.set(item_id, "Selected")
                if current_value == "☑":
                    self.dir_tree.set(item_id, "Selected", "☐")
                    self.remove_tree_item_from_selection(item_id)
                else:
                    self.dir_tree.set(item_id, "Selected", "☑")
                    self.add_tree_item_to_selection(item_id)

    def add_tree_item_to_selection(self, item_id):
        """Add an item to the selection"""
        item_path = self.get_full_path(item_id)
        item_type = self.dir_tree.item(item_id, "values")[1]  # Type is now at index 1
        
        is_folder = (item_type == "Folder")
        
        # Add to selection if not already there
        if not any(item[0] == item_path for item in self.selected_items):
            self.selected_items.append((item_path, is_folder))
            # Insert into items_tree without checkbox value
            self.items_tree.insert("", tk.END, text=os.path.basename(item_path), 
                                values=(item_type,)) # Only item_type

    def remove_tree_item_from_selection(self, item_id):
        """Remove an item from the selection"""
        item_path = self.get_full_path(item_id)
        
        # Find and remove from selected_items
        for i, (path, _) in enumerate(self.selected_items):
            if path == item_path:
                self.selected_items.pop(i)
                # Also remove from selected items tree
                # Find the item_id in items_tree corresponding to the path's basename
                item_to_delete = None
                for child_id in self.items_tree.get_children():
                    if self.items_tree.item(child_id, "text") == os.path.basename(path):
                         item_to_delete = child_id
                         break
                if item_to_delete:
                    self.items_tree.delete(item_to_delete)
                break # Exit the loop over self.selected_items

    def create_tree_context_menu(self):
        """Create context menu for the directory tree"""
        self.tree_context_menu = tk.Menu(self.window, tearoff=0)
        self.tree_context_menu.add_command(label="Select Item", command=self.select_tree_item)
        self.tree_context_menu.add_command(label="Deselect Item", command=self.deselect_tree_item)
        self.tree_context_menu.add_command(label="Select Contents", command=self.select_tree_item_contents)
        self.tree_context_menu.add_separator()
        self.tree_context_menu.add_command(label="Expand", command=self.expand_tree_item)
        self.tree_context_menu.add_command(label="Collapse", command=self.collapse_tree_item)
        
        # Bind right-click to show context menu
        self.dir_tree.bind("<Button-3>", self.show_tree_context_menu)

    def show_tree_context_menu(self, event):
        """Show context menu on right-click"""
        # Select the item under cursor
        item = self.dir_tree.identify_row(event.y)
        if item:
            self.dir_tree.selection_set(item)
            
            # Enable/disable menu items as appropriate
            item_path = self.get_full_path(item)
            is_selected = any(path == item_path for path, _ in self.selected_items)
            
            if is_selected:
                self.tree_context_menu.entryconfigure("Select Item", state=tk.DISABLED)
                self.tree_context_menu.entryconfigure("Deselect Item", state=tk.NORMAL)
            else:
                self.tree_context_menu.entryconfigure("Select Item", state=tk.NORMAL)
                self.tree_context_menu.entryconfigure("Deselect Item", state=tk.DISABLED)
            
            # Check if it's a folder for the "Select Contents" option
            item_type = self.dir_tree.item(item, "values")[1]  # Type is now at index 1
            if item_type == "Folder":
                self.tree_context_menu.entryconfigure("Select Contents", state=tk.NORMAL)
            else:
                self.tree_context_menu.entryconfigure("Select Contents", state=tk.DISABLED)
                
            self.tree_context_menu.post(event.x_root, event.y_root)

    def select_tree_item(self):
        """Add the selected tree item to the selection"""
        selected = self.dir_tree.selection()
        if not selected:
            return
            
        item_id = selected[0]
        # Set checkbox to checked
        self.dir_tree.set(item_id, "Selected", "☑")
        self.add_tree_item_to_selection(item_id)
        
    def deselect_tree_item(self):
        """Remove the selected tree item from the selection"""
        selected = self.dir_tree.selection()
        if not selected:
            return
            
        item_id = selected[0]
        # Set checkbox to unchecked
        self.dir_tree.set(item_id, "Selected", "☐")
        self.remove_tree_item_from_selection(item_id)

    def select_tree_item_contents(self):
        """Add all children of the selected folder to the selection"""
        selected = self.dir_tree.selection()
        if not selected:
            return
            
        item_id = selected[0]
        item_type = self.dir_tree.item(item_id, "values")[1]  # Type is now at index 1
        
        # Only process if it's a folder
        if item_type != "Folder":
            return
            
        item_path = self.get_full_path(item_id)
        
        # Make sure the folder is expanded to see all children
        self.dir_tree.item(item_id, open=True)
        
        # Get all immediate children in the folder
        try:
            for child_name in os.listdir(item_path):
                child_path = os.path.join(item_path, child_name)
                is_folder = os.path.isdir(child_path)
                
                # Add to selection if not already there
                if not any(item[0] == child_path for item in self.selected_items):
                    self.selected_items.append((child_path, is_folder))
                    # Insert into items_tree without checkbox value
                    self.items_tree.insert("", tk.END, text=child_name, 
                                       values=("Folder" if is_folder else "File",)) # Only type
                    
                    # Also mark checkbox in directory tree if the item is visible
                    for child_id in self.dir_tree.get_children(item_id):
                        if self.dir_tree.item(child_id, "text") == child_name:
                            self.dir_tree.set(child_id, "Selected", "☑")
                            break
                    
        except PermissionError:
            messagebox.showwarning("Permission Error", f"Cannot access {item_path}")

    def expand_tree_item(self):
        """Expand the selected tree item"""
        selected = self.dir_tree.selection()
        if selected:
            # Just set the open state; <<TreeviewOpen>> will handle loading
            self.dir_tree.item(selected[0], open=True)

    def collapse_tree_item(self):
        """Collapse the selected tree item"""
        selected = self.dir_tree.selection()
        if selected:
            self.dir_tree.item(selected[0], open=False)
    def get_full_path(self, item_id):
        """Get the full path of a tree item"""
        # If it's the root, return the root directory
        if item_id == "root":
            return self.root_directory
            
        # Get item text (the basename)
        item_text = self.dir_tree.item(item_id, "text")
        
        # Get parent path recursively
        parent_id = self.dir_tree.parent(item_id)
        parent_path = self.get_full_path(parent_id)
        
        # Combine
        return os.path.join(parent_path, item_text)

    def populate_directory_tree(self):
        """Populate the directory tree with the root directory"""
        # Clear existing items
        for item in self.dir_tree.get_children():
            self.dir_tree.delete(item)
            
        # Insert the root node
        root_name = os.path.basename(self.root_directory) or self.root_directory
        root = self.dir_tree.insert("", tk.END, "root", text=root_name, 
                                  values=("☐", "Folder"), open=True)
        
        # Populate the first level
        self.populate_directory_subtree(root, self.root_directory)
        
    def populate_directory_subtree(self, parent_node, parent_path):
        """Recursively populate a subtree"""
        try:
            # Get all items in this directory
            items = os.listdir(parent_path)
            
            # Sort them (folders first, then files)
            items.sort(key=lambda x: (0 if os.path.isdir(os.path.join(parent_path, x)) else 1, x.lower()))
            
            # Add each item
            for item in items:
                item_path = os.path.join(parent_path, item)
                try:
                    is_dir = os.path.isdir(item_path)
                    
                    # Check if it's already in our selected items
                    is_selected = any(path == item_path for path, _ in self.selected_items)
                    checkbox = "☑" if is_selected else "☐"
                    
                    # Insert the item
                    node = self.dir_tree.insert(parent_node, tk.END, text=item, 
                                            values=(checkbox, "Folder" if is_dir else "File"))
                    
                    # If it's a directory, add a dummy node so we can expand it later
                    if is_dir:
                        self.dir_tree.insert(node, tk.END, text="Loading...", values=("", ""))
                except PermissionError:
                    # Skip items we can't access
                    continue
                    
        except PermissionError:
            messagebox.showwarning("Permission Error", f"Cannot access {parent_path}")

    def on_dir_tree_double_click(self, event):
        """Handle double-click on directory tree"""
        # Get the item under cursor
        item_id = self.dir_tree.identify_row(event.y)
        if not item_id:
            return
            
        # Ignore if clicked on checkbox column
        if self.dir_tree.identify_column(event.x) == "#1":
            return
            
        # Get item type
        item_type = self.dir_tree.item(item_id, "values")[1]  # Type is now at index 1
        
        # Only expand/collapse folders
        if item_type == "Folder":
            # Toggle open/closed state
            is_open = self.dir_tree.item(item_id, "open")
            self.dir_tree.item(item_id, open=not is_open)
            
            # Let <<TreeviewOpen>> handle population if opening
            # if not is_open:
            #     self.on_folder_expanded(item_id) # Removed

    # def on_dir_tree_click(self, event): # This function was empty and binding overwritten
    #     """Handle click on directory tree"""
    #     pass

    def on_folder_expanded(self, event): # Changed signature to accept event
        """When a folder is expanded, load its contents if necessary"""
        # Get the item that was just opened (the one that has focus)
        item_id = self.dir_tree.focus()
        if not item_id: return # Should not happen with <<TreeviewOpen>>

        # Get the children
        children = self.dir_tree.get_children(item_id)

        # If there's only one child and it's the "Loading..." placeholder, replace it
        if len(children) == 1 and self.dir_tree.item(children[0], "text") == "Loading...":
            # Delete the loading placeholder
            self.dir_tree.delete(children[0])

            # Get the path for the expanded folder
            path = self.get_full_path(item_id)

            # Load the actual contents into the node
            self.populate_directory_subtree(item_id, path)
        # Else: Already populated or empty folder, do nothing

    def setup_selected_items_view(self, parent_frame):
        """Set up the view for selected items"""
        # Frame for the selected items list
        items_frame = ttk.Frame(parent_frame)
        items_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create the selected items treeview (removed checkbox column)
        self.items_tree = ttk.Treeview(items_frame, columns=("Type",), 
                                      show="tree headings")
        self.items_tree.heading("#0", text="Name")
        # self.items_tree.heading("Selected", text="") # Removed Checkbox column
        self.items_tree.heading("Type", text="Type")
        self.items_tree.column("#0", width=330) # Adjusted width
        # self.items_tree.column("Selected", width=30, anchor=tk.CENTER) # Removed
        self.items_tree.column("Type", width=80)
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, 
                                command=self.items_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.items_tree.config(yscrollcommand=scrollbar.set)
        
        # Add right-click menu to remove items
        self.items_tree.bind("<Button-3>", self.show_selected_item_menu)
        
        # Create the context menu
        self.selected_item_menu = tk.Menu(self.window, tearoff=0)
        self.selected_item_menu.add_command(label="Remove from Selection", command=self.remove_selected_item)
        
        # Removed checkbox click handler binding as column is removed
        # self.items_tree.bind("<ButtonRelease-1>", self.on_selected_item_checkbox_click)

    # Removed on_selected_item_checkbox_click method as column is removed
    # def on_selected_item_checkbox_click(self, event): ...

    def show_selected_item_menu(self, event):
        """Show context menu for selected items tree"""
        item = self.items_tree.identify_row(event.y)
        if item:
            self.items_tree.selection_set(item)
            self.selected_item_menu.post(event.x_root, event.y_root)

    def remove_selected_item(self):
        """Remove an item from the selection"""
        selected = self.items_tree.selection()
        if not selected:
            return
            
        for item_id in selected:
            # Get the item name
            item_name = self.items_tree.item(item_id, "text")
            
            # Find and remove from selected_items
            for i, (path, is_folder) in enumerate(self.selected_items):
                if os.path.basename(path) == item_name:
                    self.selected_items.pop(i)
                    
                    # Also update checkbox in directory tree if visible
                    self.update_dir_tree_checkbox(path, False)
                    break
                    
            # Remove from tree
            self.items_tree.delete(item_id)
            
    def update_dir_tree_checkbox(self, path, is_selected):
        """Update the checkbox state in the directory tree for a given path"""
        # This is a helper function to find an item in the tree by path
        def find_item_by_path(node, current_path):
            if current_path == path:
                return node
                
            # If this is a directory, search its children
            if self.dir_tree.item(node, "values")[1] == "Folder":
                # Only search expanded nodes to avoid unnecessary expansion
                if self.dir_tree.item(node, "open"):
                    for child in self.dir_tree.get_children(node):
                        child_text = self.dir_tree.item(child, "text")
                        child_path = os.path.join(current_path, child_text)
                        result = find_item_by_path(child, child_path)
                        if result:
                            return result
            return None
            
        # Start the search from root
        root_path = self.root_directory
        found_item = find_item_by_path("root", root_path)
        
        # Update checkbox if found
        if found_item:
            self.dir_tree.set(found_item, "Selected", "☑" if is_selected else "☐")

    def show_model_help(self):
        help_text = """
Model Format: provider/model-name
        
Available on OpenRouter (examples):
- anthropic/claude-3-opus-20240229
- openai/gpt-4o-2024-05-13
- google/gemini-1.5-pro-latest
- mistralai/mistral-large-latest
- meta/llama-3-70b-instruct
- cohere/command-r-plus

You can enter any model ID supported by OpenRouter.
Visit https://openrouter.ai/models for the current list.
        """
        messagebox.showinfo("Model Selection Help", help_text)

    def clear_selection(self):
        # Clear the selection list
        self.selected_items = []
        
        # Clear the selected items tree
        self.items_tree.delete(*self.items_tree.get_children())
        
        # Update checkboxes in directory tree
        self.update_all_dir_tree_checkboxes(False)
        
    def update_all_dir_tree_checkboxes(self, is_selected):
        """Update all checkboxes in the directory tree"""
        def update_node_and_children(node):
            # Update this node
            checkbox = "☑" if is_selected else "☐"
            self.dir_tree.set(node, "Selected", checkbox)
            
            # Update all children
            for child in self.dir_tree.get_children(node):
                update_node_and_children(child)
                
        # Update starting from root
        update_node_and_children("root")

    def select_all_suggestions(self):
        for item in self.results_tree.get_children():
            self.results_tree.selection_add(item)
            
    def deselect_all_suggestions(self):
        for item in self.results_tree.get_children():
            self.results_tree.selection_remove(item)

    def reject_selected_suggestions(self):
        """Move selected suggestions back to the selection list"""
        selected_items = self.results_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select suggestions to reject!")
            return

        for item in selected_items:
            values = self.results_tree.item(item)['values']
            original_name = values[0]
            item_type = values[2]  # "File" or "Folder"

            # Find the original path in rename_suggestions
            if original_name in self.rename_suggestions:
                # Find the full path (we need to reconstruct it since we cleared selection)
                for path, is_folder in self.selected_items:
                    if os.path.basename(path) == original_name:
                        # Add back to selected items if not already there
                        if not any(item[0] == path for item in self.selected_items):
                            self.selected_items.append((path, is_folder))
                            # Add to items_tree
                            self.items_tree.insert("", tk.END, text=original_name,
                                                values=(item_type,))
                            # Update checkbox in directory tree
                            self.update_dir_tree_checkbox(path, True)
                        break

                # Remove from results tree
                self.results_tree.delete(item)
                # Remove from rename_suggestions
                del self.rename_suggestions[original_name]

    def get_ai_suggestions(self):
        """Initiates the AI suggestion process in a separate thread."""
        if not self.selected_items:
            messagebox.showwarning("Warning", "Please select files or folders first!")
            return

        # Update UI for loading state
        self.status_label.config(text="Generating suggestions...")
        self.suggestions_button.config(state=tk.DISABLED)
        self.apply_button.config(state=tk.DISABLED) # Disable apply button too
        self.window.update_idletasks() # Ensure UI updates immediately

        # Prepare the items list with type information
        items_list = []
        for path, is_folder in self.selected_items:
            name = os.path.basename(path)
            type_str = "folder" if is_folder else "file"
            items_list.append(f"{name} (type: {type_str})")
        
        items_text = "\n".join(items_list)
        
        # Prepare the prompt for AI
        prompt = f"""Given these file/folder names:
        {items_text}
        
        {self.rename_instructions.get("1.0", tk.END).strip()}
        
        Provide suggestions in a JSON format with original names as keys and suggested names as values.
        Keep the file extensions unchanged for files.
        Return ONLY valid JSON with no other explanatory text."""

        # Get the selected or manually entered model
        selected_model = self.model_var.get()
        
        # OpenRouter API call
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": selected_model,
            "messages": [{"role": "user", "content": prompt}]
        }

        # Create a queue to communicate between threads
        self.result_queue = queue.Queue()

        # Start the API call in a separate thread
        thread = threading.Thread(target=self._run_ai_request_thread, 
                                  args=(headers, data, self.result_queue),
                                  daemon=True) # Daemon threads exit when the main program exits
        thread.start()

        # Start checking the queue for results
        self._check_ai_thread()

    def _run_ai_request_thread(self, headers, data, result_queue):
        """Runs the API request in a background thread."""
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60 # Add a timeout (e.g., 60 seconds)
            )
            
            if response.status_code != 200:
                error_message = f"API Error: Status {response.status_code}"
                try:
                    error_data = response.json()
                    error_message += f"\n{error_data.get('error', {}).get('message', 'Unknown error')}"
                except:
                    pass # Keep the original status code error if JSON parsing fails
                raise Exception(error_message)
            
            response_data = response.json()
            suggestions_text = response_data['choices'][0]['message']['content']
            
            # Extract JSON from the response
            if not suggestions_text.strip().startswith('{'):
                import re
                json_match = re.search(r'({.*})', suggestions_text, re.DOTALL)
                if json_match:
                    suggestions_text = json_match.group(1)
                else:
                    # If no JSON object found, raise an error
                    raise ValueError("AI response did not contain a valid JSON object.")

            suggestions_dict = json.loads(suggestions_text)
            result_queue.put(suggestions_dict) # Put successful result in queue

        except Exception as e:
            result_queue.put(e) # Put exception in queue if error occurs

    def _check_ai_thread(self):
        """Checks the queue for results from the AI thread."""
        try:
            result = self.result_queue.get_nowait() # Check queue without blocking

            # Process the result (success or error)
            if isinstance(result, Exception):
                messagebox.showerror("Error", f"Failed to get AI suggestions: {str(result)}")
            else:
                # Success - update UI with new suggestions
                for path, is_folder in self.selected_items:
                    original_name = os.path.basename(path)
                    if original_name in result:
                        # Update the rename_suggestions dictionary with new suggestions
                        self.rename_suggestions[original_name] = result[original_name]
                        
                        # Remove any existing entry for this item in results_tree
                        for item in self.results_tree.get_children():
                            if self.results_tree.item(item)['values'][0] == original_name:
                                self.results_tree.delete(item)
                                break
                                
                        # Add the new suggestion
                        suggested_name = self.rename_suggestions[original_name]
                        item_type = "Folder" if is_folder else "File"
                        self.results_tree.insert("", tk.END, values=(original_name, suggested_name, item_type))
                
                self.select_all_suggestions() # Select all by default
                self.clear_selection() # Clear selected items list after processing

            # Reset UI state regardless of success/failure
            self.status_label.config(text="")
            self.suggestions_button.config(state=tk.NORMAL)
            self.apply_button.config(state=tk.NORMAL)

        except queue.Empty:
            # If queue is empty, check again after 100ms
            self.window.after(100, self._check_ai_thread)

    def apply_renames(self):
        selected_items = self.results_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select items to rename!")
            return
            
        renamed_count = 0
        error_count = 0

        for item in selected_items:
            values = self.results_tree.item(item)['values']
            original_name = values[0]
            new_name = values[1]
            
            # Skip if names are the same
            if original_name == new_name:
                continue

            # Find the full path of the original item
            original_path = None
            is_folder = False
            for path, folder_flag in self.selected_items:
                if os.path.basename(path) == original_name:
                    original_path = path
                    is_folder = folder_flag
                    break

            if original_path:
                try:
                    new_path = os.path.join(os.path.dirname(original_path), new_name)
                    os.rename(original_path, new_path)
                    renamed_count += 1
                    
                    # Update the selected items list with the new path
                    idx = self.selected_items.index((original_path, is_folder))
                    self.selected_items[idx] = (new_path, is_folder)
                    
                except Exception as e:
                    error_count += 1
                    messagebox.showerror("Error", f"Failed to rename {original_name}: {str(e)}")

        # Show results summary
        if renamed_count > 0:
            messagebox.showinfo("Success", f"Renamed {renamed_count} items successfully." + 
                               (f" Failed to rename {error_count} items." if error_count > 0 else ""))
        elif error_count == 0:
            messagebox.showinfo("Info", "No items needed renaming.")
        
        # Refresh the directory tree
        self.populate_directory_tree()
        
        # Refresh the selected items tree
        self.items_tree.delete(*self.items_tree.get_children())
        for path, is_folder in self.selected_items:
            # Insert into items_tree without checkbox value
            self.items_tree.insert("", tk.END, text=os.path.basename(path), 
                                values=("Folder" if is_folder else "File",)) # Only type

    # --- Methods for editing results_tree ---
    def on_results_tree_double_click(self, event):
        """ Handle double-click event on the results tree. """
        region = self.results_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.results_tree.identify_column(event.x)
        # Allow editing only in the 'Suggested' column (index #2)
        if column == "#2": 
            item_id = self.results_tree.identify_row(event.y)
            self.edit_cell(item_id, column)

    def edit_cell(self, item_id, column):
        """ Create an Entry widget over the selected cell. """
        # Get the bounding box of the cell
        x, y, width, height = self.results_tree.bbox(item_id, column)

        # Get the current value
        value = self.results_tree.set(item_id, column)

        # Create an Entry widget
        entry_var = tk.StringVar(value=value)
        entry = ttk.Entry(self.results_tree, textvariable=entry_var)
        entry.place(x=x, y=y, width=width, height=height, anchor='nw')
        entry.lift() # Ensure the entry widget is drawn on top
        entry.focus_set()

        # Bind events to save the edited value
        entry.bind("<Return>", lambda e: self.save_edited_cell(entry, item_id, column))
        entry.bind("<FocusOut>", lambda e: self.save_edited_cell(entry, item_id, column))
        entry.bind("<Escape>", lambda e: entry.destroy()) # Cancel edit on Escape

    def save_edited_cell(self, entry_widget, item_id, column):
        """ Save the edited value back to the treeview item. """
        new_value = entry_widget.get()
        self.results_tree.set(item_id, column, new_value)
        entry_widget.destroy()
    # --- End of editing methods ---

    def load_preset(self):
        """Load a saved instruction preset"""
        preset_name = self.preset_var.get()
        if preset_name in self.instructions_presets:
            # Clear the current text - use Text widget method
            self.rename_instructions.delete("1.0", tk.END)
            # Insert the preset text at the beginning
            self.rename_instructions.insert("1.0", self.instructions_presets[preset_name])
            
    def save_preset(self):
        """Save the current instruction as a preset"""
        current_instruction = self.rename_instructions.get("1.0", tk.END).strip()
        if not current_instruction:
            messagebox.showwarning("Warning", "Please enter an instruction to save.")
            return
            
        # Ask for a name for the preset
        preset_name = tk.simpledialog.askstring("Save Preset", 
                                              "Enter a name for this preset:",
                                              parent=self.window)
        if preset_name and preset_name.strip():
            # Save the preset
            self.instructions_presets[preset_name.strip()] = current_instruction
            # Update the dropdown values
            self.preset_dropdown['values'] = list(self.instructions_presets.keys())
            # Set the dropdown to the new preset
            self.preset_var.set(preset_name.strip())
            # Save to file
            self.save_instructions_presets()
            messagebox.showinfo("Success", f"Preset '{preset_name}' saved successfully.")
            
    def delete_preset(self):
        """Delete a saved instruction preset"""
        preset_name = self.preset_var.get()
        if not preset_name:
            messagebox.showwarning("Warning", "Please select a preset to delete.")
            return
            
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete the preset '{preset_name}'?"):
            # Delete the preset
            if preset_name in self.instructions_presets:
                del self.instructions_presets[preset_name]
                # Update the dropdown values
                preset_names = list(self.instructions_presets.keys())
                self.preset_dropdown['values'] = preset_names
                # Set the dropdown to the first preset if any remain
                if preset_names:
                    self.preset_var.set(preset_names[0])
                else:
                    self.preset_var.set("")
                # Save to file
                self.save_instructions_presets()
                messagebox.showinfo("Success", f"Preset '{preset_name}' deleted successfully.")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = NickelFileRenamer()
    app.run()
