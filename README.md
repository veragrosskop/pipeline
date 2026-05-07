# 🎬 Pipeline Management Framework

A modular Python-based pipeline framework for managing DCC (Digital Content Creation) workflows, project structures, software compatibility, and production tooling.

This project focuses on building scalable and maintainable pipeline infrastructure for CGI and content production environments. The framework is designed with extensibility in mind and aims to support project management, software validation, launcher systems, asset workflows, and USD-based interoperability.

> ⚠️ This project is currently in active development.

---

# 🏗️ Tech Stack

- Python
- Pydantic
- JSON Config Systems
- PySide
- USD (planned)

---

# 🚀 Core Features

Features include:
- Project, shot and asset management
- Plugin, tool and script management
- Config-driven pipeline architecture
- DCC/render compatibility validation
- Pydantic schema validation
- Structured logging & tooling
- Extensible modular design
- Planned USD workflow support

The framework is built around modular and extensible architecture principles, separating configuration management, 
validation, schemas, project orchestration, and software compatibility into independent systems. 
This structure allows new DCC applications, renderers, validation rules, and workflow tools to be integrated 
without major changes to the core pipeline. 

**Currently supports the following DCCs:** Houdini, Maya, Blender

---

# 💻 Pipeline Components

## 📁 Project & Shot Management

- Automated project folder generation
- Shot creation and production directory setup
- Config-driven project structure
- Support for production and preproduction stages

## 📋 Configuration System

- JSON-based configuration management
- Modular config loading and merging
- DCC and renderer compatibility validation
- Hierarchical override system:
  - Global defaults
  - Project configs
  - Shot configs

## 📏 Validation & Schemas

- Pydantic-based schema validation
- Strict typing using Python Enums
- Validation for:
  - project settings
  - shot naming
  - frame ranges
  - software compatibility

## 📈 Logging System

- Structured logging with:
  - file logging
  - stdout/stderr separation
  - timestamped pipeline logs
  - Custom exception handling
  - automated testing with PyTest

---

> # 📌 Current Development
>The following systems are currently in development:
>- Launcher UI (Current UI is simplified for testing purposes.)
>- Scene launchers (Looking to include launchers for Nuke, Maya, Nuke for now.)
>- Scene validation
>- Naming convention validation
>- Render and Publishing workflows / visualization
>- Plugin management
>- Asset library systems
>- Test scenes and production examples

---

# 🧠 Planned USD Support

The long-term goal of the project is to support USD-centric workflows for asset interchange and scalable scene assembly between DCC applications.

Planned features include:

- USD asset publishing
- Asset import/export pipelines
- Cross-DCC interoperability
- Scene composition workflows
---

# 📬 Contact

Feel free to reach out or connect:

- GitHub: https://github.com/veragrosskop
- Linkedin: www.linkedin.com/in/vera-grosskop
---
# ⭐️ Show Your Support

If you like this project, consider giving it a star!
