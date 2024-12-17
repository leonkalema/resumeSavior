# README.md

This guide provides the steps to set up a Python virtual environment and run the `main.py` script.

## Prerequisites

- Ensure you have Python 3.12 installed on your system.
- Verify the Python installation by running:
  ```bash
  python3.12 --version
  ```

## Steps to Set Up and Run the Script

1. **Create a Virtual Environment**

   Use the following command to create a virtual environment named `myenv`:
   ```bash
   python3.12 -m venv myenv
   ```

2. **Activate the Virtual Environment**

   Activate the virtual environment using this command:
   ```bash
   source myenv/bin/activate
   ```

   Once activated, you should see the virtual environment name (e.g., `(myenv)`) in your terminal prompt.

3. **Run the `main.py` Script**

   With the virtual environment activated, run the `main.py` script:
   ```bash
   python main.py
   ```

## Notes

- Ensure all dependencies required by `main.py` are installed within the virtual environment. If the script has dependencies listed in a `requirements.txt` file, install them with:
  ```bash
  pip install -r requirements.txt
  ```

- To deactivate the virtual environment after use, simply run:
  ```bash
  deactivate
  ```

- If you encounter any issues, ensure you are using the virtual environment by checking that `(myenv)` appears in the terminal prompt.

## Additional Information

- Virtual environments are essential for isolating dependencies and preventing conflicts with system-wide Python packages.
- For further details on Python virtual environments, refer to the [official documentation](https://docs.python.org/3/library/venv.html).

