import aiohttp
import asyncio
import zipfile
import os
import sys
import shutil
import json
import subprocess

remote_version_url = 'https://raw.githubusercontent.com/icetea-dev/lunaris/main/remote_version.txt'
update_url = 'https://raw.githubusercontent.com/icetea-dev/lunaris/main/latest.zip'
appdata_path = os.getenv('APPDATA')
lunaris_folder = os.path.join(appdata_path, 'Lunaris Selfbot')
local_version_file = os.path.join(lunaris_folder, 'version.txt')
settings_folder = os.path.join(lunaris_folder, 'settings')
settings_file = os.path.join(settings_folder, 'settings.json')
remote_settings_file = os.path.join(settings_folder, 'remote_settings.json')

async def get_remote_version():
    async with aiohttp.ClientSession() as session:
        async with session.get(remote_version_url) as response:
            if response.status == 200:
                return await response.text()
            else:
                raise Exception(f"Failed to fetch remote version: {response.status}")

def get_local_version():
    try:
        with open(local_version_file, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

def update_local_version(new_version):
    with open(local_version_file, 'w') as file:
        file.write(new_version)

async def download_update():
    async with aiohttp.ClientSession() as session:
        async with session.get(update_url) as response:
            if response.status == 200:
                update_path = os.path.join(lunaris_folder, 'latest.zip')
                with open(update_path, 'wb') as file:
                    file.write(await response.read())
                print("Update downloaded.")
                apply_update(update_path)
            else:
                raise Exception(f"Failed to download update: {response.status}")

def apply_update(update_path):
    try:
        for item in os.listdir(lunaris_folder):
            item_path = os.path.join(lunaris_folder, item)
            if item_path not in [update_path, settings_folder, local_version_file]:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

        with zipfile.ZipFile(update_path, 'r') as zip_ref:
            zip_ref.extractall(lunaris_folder)
        
        os.remove(update_path)
        print("Update applied.")

        if os.path.exists(remote_settings_file) and not os.path.exists(settings_file):
            shutil.move(remote_settings_file, settings_file)
        elif os.path.exists(remote_settings_file):
            os.remove(remote_settings_file)

    except Exception as e:
        print(f"Failed to apply update: {e}")

async def check_for_update():
    try:
        local_version = get_local_version()
        remote_version = await get_remote_version()

        if local_version != remote_version:
            print(f"Updating from version {local_version} to {remote_version}")
            await download_update()
            update_local_version(remote_version)
            start_lunaris()
        else:
            print("Already up-to-date.")
            start_lunaris()
    except Exception as e:
        print(f"Error checking for update: {e}")

def create_and_activate_virtualenv():
    try:
        subprocess.run([sys.executable, '-m', 'venv', os.path.join(lunaris_folder, 'Lunaris')], check=True, timeout=600)
        print("Virtualenv created.")
    except subprocess.TimeoutExpired:
        print("Creation of virtualenv timed out.")
        input("Press Enter to exit.")
        sys.exit()
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtualenv: {e}")
        input("Press Enter to exit.")
        sys.exit()

def install_requirements():
    try:
        pip_executable = os.path.join(lunaris_folder, 'Lunaris', 'Scripts', 'pip.exe')
        requirements_file = os.path.join(lunaris_folder, 'requirements.txt')
        subprocess.run([pip_executable, 'install', '-r', requirements_file], check=True)
        print("Requirements installed.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements: {e}")

def start_lunaris():
    try:
        assert sys.version_info >= (3, 11)
        start = input("Start Lunaris? (y/n): ")
        if start.lower() == 'y':
            create_and_activate_virtualenv()
            install_requirements()
            python_executable = os.path.join(lunaris_folder, 'Lunaris', 'Scripts', 'python.exe')
            main_script = os.path.join(lunaris_folder, 'main.py')
            subprocess.run([python_executable, main_script], check=True)
            print("Lunaris started.")
        elif start.lower() == 'n':
            sys.exit()
    except AssertionError:
        print("Python version must be 3.11 or higher.")
        input("Please update to Python 3.11 or higher.")
        sys.exit()
    except Exception as e:
        print(f"Error during update application: {e}")

if __name__ == "__main__":
    try:
        if not os.path.exists(lunaris_folder):
            os.makedirs(lunaris_folder)
        if not os.path.exists(settings_folder):
            os.makedirs(settings_folder)
        
        asyncio.run(check_for_update())
    except Exception as e:
        print(f"Error in updater script: {e}")
