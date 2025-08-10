import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import zipfile
import json
import uuid
import subprocess
import tempfile
import shutil
import os
from pathlib import Path
import threading

# --- Constants and Helper Functions ---
APP_NAME = "Python Codex"
APP_VERSION = "1.3" 
FILE_EXTENSION = ".codex"
MANIFEST_NAME = "manifest.json"

def find_vscode_executable():
    if os.name != 'nt': return 'code'
    local_app_data = os.getenv('LOCALAPPDATA')
    if local_app_data:
        user_path = Path(local_app_data) / 'Programs' / 'Microsoft VS Code' / 'bin' / 'code.cmd'
        if user_path.exists(): return str(user_path)
    program_files = os.getenv('ProgramFiles')
    if program_files:
        system_path = Path(program_files) / 'Microsoft VS Code' / 'bin' / 'code.cmd'
        if system_path.exists(): return str(system_path)
    return 'code'

# --- Core Logic Class ---
class ScriptVault:
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.manifest = {"version": APP_VERSION, "projects": []}
        if self.filepath.exists(): self._load()
    def _load(self):
        try:
            with zipfile.ZipFile(self.filepath, 'r') as zf:
                if MANIFEST_NAME in zf.namelist():
                    self.manifest = json.loads(zf.read(MANIFEST_NAME))
        except (zipfile.BadZipFile, json.JSONDecodeError):
            raise ValueError(f"'{self.filepath.name}' is not a valid or is a corrupted vault file.")
    def get_projects(self):
        return sorted(self.manifest.get("projects", []), key=lambda p: p.get("name", "").lower())
    def add_project(self, source_disk_path, name, description, entry_point):
        project_id = str(uuid.uuid4())
        source_path = Path(source_disk_path)
        new_project_entry = { "id": project_id, "name": name, "description": description, "entry_point": entry_point, "source_path_in_zip": f"{project_id}/" }
        self.manifest["projects"].append(new_project_entry)
        with zipfile.ZipFile(self.filepath, 'a', zipfile.ZIP_DEFLATED) as zf:
            for file_path in source_path.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(source_path)
                    arcname = Path(new_project_entry["source_path_in_zip"]) / relative_path
                    zf.write(file_path, arcname)
        self._rewrite_archive_with_new_manifest()
        return project_id
    def remove_project(self, project_id):
        self.manifest["projects"] = [p for p in self.manifest["projects"] if p["id"] != project_id]
        self._rewrite_archive_with_new_manifest(id_to_exclude=project_id)
    def _rewrite_archive_with_new_manifest(self, id_to_exclude=None):
        temp_zip_path = self.filepath.with_suffix(f"{self.filepath.suffix}.tmp")
        with zipfile.ZipFile(self.filepath, 'r') as zf_in, zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf_out:
            zf_out.writestr(MANIFEST_NAME, json.dumps(self.manifest, indent=2))
            for item in zf_in.infolist():
                if item.filename == MANIFEST_NAME: continue
                if id_to_exclude and item.filename.startswith(f"{id_to_exclude}/"): continue
                buffer = zf_in.read(item.filename)
                zf_out.writestr(item, buffer)
        self.filepath.unlink()
        temp_zip_path.rename(self.filepath)
    def extract_project_to_temp(self, project_id):
        project = next((p for p in self.manifest["projects"] if p["id"] == project_id), None)
        if not project: return None, None
        temp_dir = Path(tempfile.gettempdir()) / APP_NAME / project_id
        if temp_dir.exists(): shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)
        source_path = project["source_path_in_zip"]
        with zipfile.ZipFile(self.filepath, 'r') as zf:
            project_files = [item for item in zf.infolist() if item.filename.startswith(source_path) and not item.is_dir()]
            zf.extractall(temp_dir, members=project_files)
        extracted_root = temp_dir / Path(source_path)
        return extracted_root, project["entry_point"]
    
    def export_single_project(self, project_id, destination_path):
        project = next((p for p in self.manifest["projects"] if p["id"] == project_id), None)
        if not project: raise ValueError("Project not found.")
        dest = Path(destination_path)
        dest.mkdir(parents=True, exist_ok=True)
        source_path = project["source_path_in_zip"]
        with zipfile.ZipFile(self.filepath, 'r') as zf:
            project_files = [item for item in zf.infolist() if item.filename.startswith(source_path) and not item.is_dir()]
            
            for member in project_files:
                target_path = dest / Path(member.filename).relative_to(source_path)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)

    def export_all_projects(self, destination_path):
        dest_root = Path(destination_path)
        for project in self.get_projects():
            project_dest = dest_root / project["name"]
            self.export_single_project(project["id"], project_dest)

class AddProjectDialog(simpledialog.Dialog):
    def __init__(self, parent, source_path):
        self.source_path = Path(source_path)
        super().__init__(parent, "Add New Project")
    def body(self, master):
        self.project_name = tk.StringVar(value=self.source_path.name)
        self.description = tk.StringVar()
        self.entry_point = tk.StringVar()
        py_files = sorted([f.name for f in self.source_path.glob('*.py')])
        if py_files:
        
            common_entry = next((f for f in py_files if f in ['main.py', 'app.py']), py_files[0])
            self.entry_point.set(common_entry)

        ttk.Label(master, text="Project Name:").grid(row=0, sticky="w", padx=5, pady=2)
        ttk.Entry(master, textvariable=self.project_name, width=40).grid(row=1, padx=5, pady=2, sticky="ew")
        ttk.Label(master, text="Description:").grid(row=2, sticky="w", padx=5, pady=2)
        ttk.Entry(master, textvariable=self.description, width=40).grid(row=3, padx=5, pady=2, sticky="ew")
        ttk.Label(master, text="Entry Point (main script):").grid(row=4, sticky="w", padx=5, pady=2)
        ttk.Combobox(master, textvariable=self.entry_point, values=py_files).grid(row=5, padx=5, pady=2, sticky="ew")
        return master
    def apply(self):
        self.result = { "name": self.project_name.get(), "description": self.description.get(), "entry_point": self.entry_point.get() }

class ScriptVaultApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - No Codex Open")
        self.geometry("900x600")
        self.vault = None
        self.temp_dirs_to_clean = []
        self.vscode_path = find_vscode_executable()
        self._create_widgets()
        self._update_ui_state()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_widgets(self):
        self.menu_bar = tk.Menu(self)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New Codex...", command=self.new_vault)
        self.file_menu.add_command(label="Open Codex...", command=self.open_vault)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Export All...", command=self.export_all_projects)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_closing)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.config(menu=self.menu_bar)

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=1); main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        list_frame = ttk.LabelFrame(main_frame, text="Projects")
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        list_frame.rowconfigure(0, weight=1); list_frame.columnconfigure(0, weight=1)
        
        self.project_list = tk.Listbox(list_frame)
        self.project_list.grid(row=0, column=0, sticky="nsew")
        self.project_list.bind("<<ListboxSelect>>", self.on_project_select)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.project_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.project_list.config(yscrollcommand=scrollbar.set)
        
        details_frame = ttk.Frame(main_frame)
        details_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        details_frame.rowconfigure(2, weight=1)
        details_frame.columnconfigure(0, weight=1)
        actions_frame = ttk.Frame(details_frame)
        actions_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.add_button = ttk.Button(actions_frame, text="Add Project...", command=self.add_project)
        self.add_button.pack(side="left", padx=2)
        self.remove_button = ttk.Button(actions_frame, text="Remove Project", command=self.remove_project)
        self.remove_button.pack(side="left", padx=2)
        self.export_button = ttk.Button(actions_frame, text="Export Project...", command=self.export_project)
        self.export_button.pack(side="left", padx=2)
        self.run_button = ttk.Button(actions_frame, text="Run", command=self.run_project)
        self.run_button.pack(side="right", padx=2)
        self.vscode_button = ttk.Button(actions_frame, text="Open in VS Code", command=self.open_in_vscode)
        self.vscode_button.pack(side="right", padx=2)
        
        desc_frame = ttk.LabelFrame(details_frame, text="Description")
        desc_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        self.description_text = tk.Text(desc_frame, wrap="word", state="disabled", height=4)
        self.description_text.pack(fill="x", expand=True, padx=5, pady=5)
        tree_frame = ttk.LabelFrame(details_frame, text="File Structure")
        tree_frame.grid(row=2, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1); tree_frame.columnconfigure(0, weight=1)
        self.file_tree = ttk.Treeview(tree_frame, selectmode='browse')
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=tree_scrollbar.set)
        self.file_tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")
        
    def _update_ui_state(self):
        is_vault_open = self.vault is not None
        self.add_button.config(state="normal" if is_vault_open else "disabled")
        self.file_menu.entryconfig("Export All...", state="normal" if is_vault_open else "disabled")
        
        is_project_selected = is_vault_open and self.project_list.curselection()
        self.remove_button.config(state="normal" if is_project_selected else "disabled")
        self.export_button.config(state="normal" if is_project_selected else "disabled")
        self.run_button.config(state="normal" if is_project_selected else "disabled")
        self.vscode_button.config(state="normal" if is_project_selected else "disabled")
        
    def refresh_project_list(self):
        self.project_list.delete(0, "end")
        if self.vault:
            self.projects_in_list = self.vault.get_projects()
            for project in self.projects_in_list:
                self.project_list.insert("end", project["name"])
        self.description_text.config(state="normal")
        self.description_text.delete("1.0", "end")
        self.description_text.config(state="disabled")
        self.populate_file_tree(None)
        self._update_ui_state()

    def on_project_select(self, event):
        selected_indices = self.project_list.curselection()
        if not selected_indices: self._update_ui_state(); return
        project = self.projects_in_list[selected_indices[0]]
        self.description_text.config(state="normal")
        self.description_text.delete("1.0", "end")
        self.description_text.insert("1.0", project.get("description", "No description."))
        self.description_text.config(state="disabled")
        self.populate_file_tree(project)
        self._update_ui_state()

    def populate_file_tree(self, project):
        for i in self.file_tree.get_children(): self.file_tree.delete(i)
        if not project or not self.vault: return
        project_name = project["name"]
        project_root_path_in_zip = project["source_path_in_zip"]
        root_node = self.file_tree.insert('', 'end', text=project_name, open=True)
        dir_nodes = {'': root_node}
        with zipfile.ZipFile(self.vault.filepath, 'r') as zf:
            project_files = sorted([item.filename for item in zf.infolist() if item.filename.startswith(project_root_path_in_zip) and item.filename != project_root_path_in_zip])
            for file_path_str in project_files:
                relative_path = Path(file_path_str).relative_to(project_root_path_in_zip)
                parent_node_id = root_node
                path_prefix = ''
                for part in relative_path.parts[:-1]:
                    path_prefix = str(Path(path_prefix) / part)
                    if path_prefix not in dir_nodes:
                        node_id = self.file_tree.insert(parent_node_id, 'end', text=part, open=False)
                        dir_nodes[path_prefix] = node_id
                        parent_node_id = node_id
                    else:
                        parent_node_id = dir_nodes[path_prefix]
                self.file_tree.insert(parent_node_id, 'end', text=relative_path.name)
    
    def _run_in_thread(self, target, args, on_complete_msg):
        def task_wrapper():
            try:
                target(*args)
                messagebox.showinfo("Success", on_complete_msg)
            except Exception as e:
                messagebox.showerror("Error", f"Operation failed:\n{e}")
        threading.Thread(target=task_wrapper, daemon=True).start()

    def export_project(self):
        if not self.vault: return
        selected_indices = self.project_list.curselection()
        if not selected_indices: return
        project = self.projects_in_list[selected_indices[0]]
        dest_dir = filedialog.askdirectory(title=f"Select folder to export '{project['name']}' into")
        if not dest_dir: return
        
        self._run_in_thread(
            target=self.vault.export_single_project,
            args=(project['id'], Path(dest_dir) / project['name']),
            on_complete_msg=f"Project '{project['name']}' exported successfully."
        )

    def export_all_projects(self):
        if not self.vault: return
        dest_dir = filedialog.askdirectory(title="Select folder to export all projects into")
        if not dest_dir: return

        self._run_in_thread(
            target=self.vault.export_all_projects,
            args=(dest_dir,),
            on_complete_msg="All projects have been exported successfully."
        )

    def new_vault(self, filepath=None):
        filepath = filedialog.asksaveasfilename(title="Create New Codex", defaultextension=FILE_EXTENSION, filetypes=[(f"{APP_NAME} File", f"*{FILE_EXTENSION}")])
        if not filepath: return
        with zipfile.ZipFile(filepath, 'w') as zf:
            zf.writestr(MANIFEST_NAME, json.dumps({"version": APP_VERSION, "projects": []}, indent=2))
        self.open_vault(filepath)
    def open_vault(self, filepath=None):
        if not filepath:
            filepath = filedialog.askopenfilename(title="Open Codex", filetypes=[(f"{APP_NAME} File", f"*{FILE_EXTENSION}")])
        if not filepath: return
        try:
            self.vault = ScriptVault(filepath)
            self.title(f"{APP_NAME} - {Path(filepath).name}")
            self.refresh_project_list()
        except Exception as e: messagebox.showerror("Error", f"Could not open codex:\n{e}")
    def add_project(self):
        if not self.vault: return
        source_dir = filedialog.askdirectory(title="Select Project Folder to Add")
        if not source_dir: return
        dialog = AddProjectDialog(self, source_dir)
        if not dialog.result or not dialog.result.get("name"): messagebox.showwarning("Warning", "Project name cannot be empty."); return
        try:
            self.vault.add_project(source_disk_path=source_dir, name=dialog.result["name"], description=dialog.result["description"], entry_point=dialog.result["entry_point"])
            self.refresh_project_list()
        except Exception as e: messagebox.showerror("Error", f"Failed to add project:\n{e}")
    def remove_project(self):
        if not self.vault: return
        selected_indices = self.project_list.curselection()
        if not selected_indices: return
        project = self.projects_in_list[selected_indices[0]]
        if messagebox.askyesno("Confirm", f"Are you sure you want to remove '{project['name']}'?"):
            try:
                self.vault.remove_project(project["id"])
                self.refresh_project_list()
            except Exception as e: messagebox.showerror("Error", f"Failed to remove project:\n{e}")
    def _run_or_open(self, mode):
        if not self.vault: return
        selected_indices = self.project_list.curselection()
        if not selected_indices: return
        project = self.projects_in_list[selected_indices[0]]
        try:
            temp_path, entry_point = self.vault.extract_project_to_temp(project["id"])
            if not temp_path: messagebox.showerror("Error", "Could not extract project."); return
            self.temp_dirs_to_clean.append(temp_path.parent)
            if mode == 'run':
                script_path = temp_path / entry_point
                if not entry_point or not script_path.exists():
                    messagebox.showerror("Error", f"Entry point '{entry_point}' not found or not specified!"); return
                subprocess.Popen(['python', str(script_path)], cwd=str(temp_path), creationflags=subprocess.CREATE_NEW_CONSOLE)
            elif mode == 'vscode':
                command = [self.vscode_path, str(temp_path)]
                try: subprocess.Popen(command)
                except FileNotFoundError: messagebox.showwarning("Warning", "Could not find VS Code. Make sure 'code' command is in your system's PATH, or VS Code is in a standard location.")
        except Exception as e: messagebox.showerror("Error", f"Operation failed:\n{e}")
    def run_project(self): self._run_or_open('run')
    def open_in_vscode(self): self._run_or_open('vscode')
    def on_closing(self):
        for temp_dir in self.temp_dirs_to_clean:
            try:
                if temp_dir.exists(): shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Could not clean up temporary directory {temp_dir}. Reason: {e}")
        self.destroy()

if __name__ == "__main__":
    app = ScriptVaultApp()
    app.mainloop()
