from cx_Freeze import setup, Executable
import os
import sys

# Caminho do PyQt5 dentro do ambiente virtual
pyqt5_path = os.path.join(sys.prefix, 'Lib', 'site-packages', 'PyQt5')
qt5_plugins_path = os.path.join(pyqt5_path, 'Qt5', 'plugins')
qt5_bin_path = os.path.join(pyqt5_path, 'Qt5', 'bin')

# Verifica se os diretórios existem
if not os.path.isdir(qt5_plugins_path):
    raise RuntimeError("Qt5 plugins path not found: " + qt5_plugins_path)
if not os.path.isdir(qt5_bin_path):
    raise RuntimeError("Qt5 bin path not found: " + qt5_bin_path)

# Base correta para GUI no Windows
base = "Win32GUI" if sys.platform == "win32" else None

# Configurações do executável
executables = [
    Executable('gui_sped.py', base=base, target_name='gui_sped.exe', icon='icon.ico')
]



# Configurações de build
build_options = {
    'packages': ['PyQt5'],
    'excludes': ['PyQt5.QtQml'],
    'include_files': [
        (os.path.join(qt5_bin_path, 'Qt5Core.dll'), 'Qt/bin/Qt5Core.dll'),
        (os.path.join(qt5_bin_path, 'Qt5Gui.dll'), 'Qt/bin/Qt5Gui.dll'),
        (os.path.join(qt5_bin_path, 'Qt5Widgets.dll'), 'Qt/bin/Qt5Widgets.dll'),
        (qt5_plugins_path, 'Qt/plugins')
    ],
}

# Configurações do setup
setup(
    name='SPED Application',
    version='1.12',
    description='SPED Application by Rafael Araujo',
    options={'build_exe': build_options},
    executables=executables
)