# Project Documentation

This directory contains documentation for the **BMAI** project.

## Structure

- **src/** – Core source code for the application.
- **tests/** – Automated test suite.
- **docs/** – Project documentation, design notes, and usage guides.

## Getting Started

1. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # On Windows use `.venv\Scripts\activate`
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**

   ```bash
   uvicorn app.main:app --reload
   ```

4. **Run tests**

   ```bash
   pytest -q
   ```

Feel free to add more documentation files in this folder as the project evolves.