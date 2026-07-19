#!/usr/bin/env python3
"""
スタンドアロン実行ファイル作成用スクリプト
PyInstallerを使用してcodexrayの実行ファイルを作成します。
"""

import subprocess
import sys


def install_pyinstaller() -> None:
    """PyInstallerをインストール"""
    try:
        import importlib.util

        if importlib.util.find_spec("PyInstaller") is not None:
            print("PyInstaller is already installed")
        else:
            raise ImportError("PyInstaller not found")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def create_spec_file() -> None:
    """PyInstaller用の.specファイルを作成"""
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['codexray/cli_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('codexray/queries', 'codexray/queries'),
    ],
    hiddenimports=[
        'codexray',
        'codexray.cli',
        'codexray.core',
        'codexray.languages',
        'codexray.plugins',
        'codexray.formatters',
        'codexray.interfaces',
        'tree_sitter',
        'tree_sitter_java',
        'chardet',
        'cachetools',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='codexray',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""

    with open("codexray.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    print("Created codexray.spec")


def build_executable() -> bool:
    """実行ファイルをビルド"""
    print("Building standalone executable...")
    try:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--clean",
                "codexray.spec",
            ]
        )
        print("Build completed successfully!")
        print("Executable location: dist/codexray.exe")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False
    return True


def main() -> None:
    """メイン処理"""
    print("=== CodeXray Standalone Builder ===")

    # 必要な依存関係をインストール
    install_pyinstaller()

    # .specファイルを作成
    create_spec_file()

    # 実行ファイルをビルド
    if build_executable():
        print("\n=== Build Summary ===")
        print("✓ Standalone executable created successfully")
        print("✓ Location: dist/codexray.exe")
        print("✓ This executable can run without Python installation")
        print("\nUsage:")
        print("  ./dist/codexray.exe examples/Sample.java --advanced")
    else:
        print("\n❌ Build failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
