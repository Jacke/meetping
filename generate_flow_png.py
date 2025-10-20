#!/usr/bin/env python3
"""
Generate PNG visualization of payment flow from Mermaid diagram.

This script provides multiple methods to generate PNG:
1. Using mermaid-cli (mmdc) if installed
2. Using kroki.io API service (no installation needed)
3. Manual instructions for browser-based generation

Usage:
    python3 generate_flow_png.py [--method cli|api|manual]
"""
import argparse
import base64
import requests
import zlib
import sys
from pathlib import Path


def generate_via_mmdc(mermaid_code: str, output_path: str) -> bool:
    """Generate PNG using mermaid-cli (mmdc)."""
    import subprocess
    import tempfile

    try:
        # Check if mmdc is installed
        subprocess.run(['mmdc', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ mermaid-cli (mmdc) not found!")
        print("📦 Install with: npm install -g @mermaid-js/mermaid-cli")
        return False

    # Create temporary .mmd file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
        f.write(mermaid_code)
        temp_file = f.name

    try:
        # Generate PNG
        subprocess.run([
            'mmdc',
            '-i', temp_file,
            '-o', output_path,
            '-b', 'white',
            '-t', 'default'
        ], check=True)

        print(f"✅ PNG generated successfully: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating PNG: {e}")
        return False
    finally:
        Path(temp_file).unlink(missing_ok=True)


def generate_via_kroki(mermaid_code: str, output_path: str) -> bool:
    """Generate PNG using Kroki.io API service."""
    try:
        # Encode mermaid code for Kroki
        compressed = zlib.compress(mermaid_code.encode('utf-8'), 9)
        encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')

        # Request PNG from Kroki
        url = f"https://kroki.io/mermaid/png/{encoded}"
        print(f"🌐 Requesting PNG from Kroki.io...")

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Save PNG
        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"✅ PNG generated successfully: {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error requesting from Kroki.io: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def show_manual_instructions(mermaid_code: str):
    """Show manual instructions for generating PNG."""
    print("\n" + "="*60)
    print("📝 Manual PNG Generation Instructions")
    print("="*60)
    print("\nOption 1: Using Mermaid Live Editor")
    print("1. Visit: https://mermaid.live/")
    print("2. Paste the Mermaid code from docs/payment_flow.md")
    print("3. Click 'Actions' → 'PNG'")
    print("4. Save to docs/payment_flow.png")

    print("\nOption 2: Using Kroki.io")
    print("1. Visit: https://kroki.io/")
    print("2. Select 'Mermaid' from diagram types")
    print("3. Paste the Mermaid code")
    print("4. Download PNG")

    print("\nOption 3: Install mermaid-cli")
    print("$ npm install -g @mermaid-js/mermaid-cli")
    print("$ python3 generate_flow_png.py --method cli")

    print("\n" + "="*60)


def load_mermaid_from_file(filepath: str) -> str:
    """Extract Mermaid code from markdown file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Extract code between ```mermaid and ```
    start = content.find('```mermaid')
    if start == -1:
        raise ValueError(f"No mermaid code block found in {filepath}")

    start = content.find('\n', start) + 1
    end = content.find('```', start)

    return content[start:end].strip()


def main():
    parser = argparse.ArgumentParser(
        description='Generate PNG visualization from Mermaid diagram'
    )
    parser.add_argument(
        '--method',
        choices=['cli', 'api', 'manual'],
        default='api',
        help='Generation method (default: api)'
    )
    parser.add_argument(
        '--input',
        default='docs/payment_flow.md',
        help='Input Mermaid markdown file'
    )
    parser.add_argument(
        '--output',
        default='docs/payment_flow.png',
        help='Output PNG file'
    )

    args = parser.parse_args()

    print("🎨 Payment Flow PNG Generator")
    print("="*60)

    try:
        # Load Mermaid code
        print(f"📖 Loading Mermaid code from {args.input}...")
        mermaid_code = load_mermaid_from_file(args.input)
        print(f"✅ Loaded {len(mermaid_code)} characters")

        # Generate PNG based on method
        if args.method == 'cli':
            success = generate_via_mmdc(mermaid_code, args.output)
        elif args.method == 'api':
            success = generate_via_kroki(mermaid_code, args.output)
        else:  # manual
            show_manual_instructions(mermaid_code)
            success = True

        if success and args.method != 'manual':
            print(f"\n✅ PNG saved to: {args.output}")
            print(f"📏 File size: {Path(args.output).stat().st_size // 1024} KB")

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
