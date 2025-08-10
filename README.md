# The Python Codex

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

**Your personal, portable library of Python scripts and projects, elegantly managed in a single file.**

Tired of scattered Python scripts across countless directories? The Python Codex is a sophisticated project manager and launcher that consolidates your entire script collection into a single, portable vault file (`.codex`). It provides a robust GUI to manage, inspect, and execute your projects without losing their original file structure or dependencies.

This is more than just an archiver; it's a portable development environment for your entire scripting workshop.

![Main Interface of The Python Codex](https://github.com/zbirow/Python-Codex/blob/main/codex0.png)
_The main application interface, showing the project list and info panel._

---

## ✨ Key Features

*   **Single-File Vault:** Archives entire Python projects, including subdirectories and dependency files, into one `.codex` file for ultimate portability and organization.
*   **Full Project Integrity:** Perfectly preserves the internal directory structure of each project, ensuring that local imports and file access work flawlessly.
*   **Rich Metadata:** Each project is stored with a user-friendly name, a detailed description, and a designated entry point script.
*   **Intuitive GUI:** A clean and powerful graphical interface built with Tkinter for managing your codex files and the projects within them.
*   **On-Demand Execution & Editing:**
    *   **Run:** Executes any project in an isolated, temporary environment with a single click.
    *   **Open in VS Code:** Instantly opens the complete project structure in Visual Studio Code for editing.
*   **Deep Inspection:** An integrated file tree viewer allows you to inspect the full directory structure of any project directly within the application.
*   **Robust Export Functionality:** Export a single project or all projects from the vault back to your filesystem with their original structure intact.

## 🚀 Getting Started

### Prerequisites
*   Python 3.x installed on your system.
*   (Optional) Visual Studio Code installed for the "Open in VS Code" feature.

### How to Use

1.  **Launch the Application:** Run the `python_codex.py` file.
2.  **Create or Open a Codex:**
    *   Go to `File > New Vault...` to create a new, empty `.codex` file.
    *   Go to `File > Open Vault...` to open an existing `.codex` file.
3.  **Add a Project:**
    *   Click the **"Add Project..."** button.
    *   Select the **root folder** of the Python project you want to add.
    *   In the dialog, confirm the project name, add a description, and select the main executable script as the "Entry Point".
4.  **Manage Your Projects:**
    *   Select a project from the list on the left.
    *   View its description and file structure in the panel on the right.
    *   Use the action buttons (**Run**, **Open in VS Code**, **Export**, **Remove**) to manage the selected project.

## ⚙️ The `.codex` File Format

For maximum reliability and compatibility, a `.codex` file is a standard **ZIP archive** with a specific, enforced internal structure. This approach combines the robustness of the ZIP format with the intelligence of a custom manifest file.

### Component Details

1.  **The Container (`.codex` file)**
    *   The root file itself is a standard ZIP archive. You can rename it to `.zip` and open it with any standard archive manager.

2.  **`manifest.json`**
    *   This is the "brain" of the codex. It's a JSON file that acts as a database, holding all the metadata about the projects stored inside.
    *   **Example Manifest:**
        ```json
        {
          "version": 1.3,
          "projects": [
            {
              "id": "e7b2c2a0-a1b1-4c3d-8e4f-1234567890ab",
              "name": "My Super Web Scraper",
              "description": "A script to fetch weather data.",
              "entry_point": "main.py",
              "source_path_in_zip": "e7b2c2a0-a1b1-4c3d-8e4f-1234567890ab/"
            }
          ]
        }
        ```

3.  **Project Folders (e.g., `e7b2c2a0-.../`)**
    *   Each project is stored in its own dedicated folder within the ZIP archive, named with its **Universally Unique Identifier (UUID)**. This guarantees no name conflicts and provides a stable, unique reference for each project.
    *   Inside this folder, the project's **original directory structure is perfectly preserved**.

## 💻 Technology Stack

*   **Core Application:** Python
*   **GUI:** Tkinter (standard library)
*   **Archive Format:** ZIP (via `zipfile` standard library)

## 🗺️ Future Development (Roadmap)

*   **Codex-Vault:** Add an option to encrypt the entire `.codex` file or individual projects with a password.
*   **Codex-Sync:** Implement a feature to synchronize a project in the vault with its external folder on the filesystem.
*   **Plugin System:** Allow users to define custom actions for projects (e.g., "Run with args...", "Run tests...").

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/zbirow/Python-Codex/issues).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
