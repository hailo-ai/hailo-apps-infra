import os
import argparse
import sys
from pathlib import Path
import tempfile
import subprocess
import shutil
import re


def create_directory_structure(directory):
    """Create a formatted string showing the directory structure."""
    result = []
    
    def _list_dir(dir_path, prefix=""):
        try:
            paths = sorted(Path(dir_path).iterdir(), key=lambda p: (p.is_file(), p.name))
            
            for i, path in enumerate(paths):
                is_last = i == len(paths) - 1
                curr_prefix = "└── " if is_last else "├── "
                result.append(f"{prefix}{curr_prefix}{path.name}")
                
                if path.is_dir():
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    _list_dir(path, new_prefix)
        except PermissionError:
            result.append(f"{prefix}[Permission denied]")
        except Exception as e:
            result.append(f"{prefix}[Error: {str(e)}]")
    
    result.append(directory)
    _list_dir(directory)
    return "\n".join(result)


def is_text_file(file_path):
    """Check if a file is likely a text file based on extension and content."""
    # Common binary file extensions
    binary_extensions = {
        '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.mp3', '.mp4', '.zip', 
        '.tar', '.gz', '.exe', '.dll', '.obj', '.bin', '.pyc', '.pyd',
        '.so', '.o', '.class', '.jar', '.war', '.ear', '.iso', '.img',
        '.db', '.sqlite', '.bak', '.dat', '.docx', '.xlsx', '.pptx',
    }
    
    # Check extension
    ext = os.path.splitext(file_path)[1].lower()
    if ext in binary_extensions:
        return False
    
    # Try to read a small portion of the file
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            # Count null bytes - binary files often have many
            if chunk.count(b'\x00') > 0:
                return False
            
            # If it's too weird (too many non-printable chars), probably binary
            printable = sum(1 for b in chunk if 32 <= b <= 126 or b in (9, 10, 13))
            if len(chunk) > 0 and printable / len(chunk) < 0.75:
                return False
    except:
        return False
        
    return True


def extract_text_safely(file_path):
    """Extract text from a file in a safe manner, handling encoding issues."""
    try:
        # First try with utf-8
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(100000)  # Limit to 100K characters
        return content
    except Exception as e:
        try:
            # Then try with latin-1 which can read any byte
            with open(file_path, 'r', encoding='latin-1', errors='replace') as f:
                content = f.read(100000)
            return content
        except Exception as e:
            return f"[Error reading file: {str(e)}]"


def create_markdown_file(directory, output_path):
    """Create a markdown file with directory structure and file contents."""
    with open(output_path, 'w', encoding='utf-8') as md_file:
        # Add title
        md_file.write(f"# Directory Content: {directory}\n\n")
        
        # Add directory structure
        md_file.write("## Directory Structure\n\n```\n")
        dir_structure = create_directory_structure(directory)
        md_file.write(dir_structure)
        md_file.write("\n```\n\n")
        
        # Process files
        md_file.write("## File Contents\n\n")
        file_count = 0
        max_files = 100
        
        for root, dirs, files in os.walk(directory):
            if file_count >= max_files:
                md_file.write("### Maximum file limit reached\n\n")
                break
                
            for file in sorted(files):
                file_path = os.path.join(root, file)
                
                # Skip binary files
                if not is_text_file(file_path):
                    continue
                    
                # Skip large files
                try:
                    if os.path.getsize(file_path) > 1_000_000:  # Skip files larger than 1MB
                        continue
                except:
                    continue
                
                # Extract text
                try:
                    text = extract_text_safely(file_path)
                    
                    # Add file path as header
                    rel_path = os.path.relpath(file_path, directory)
                    md_file.write(f"### {rel_path}\n\n")
                    
                    # Add content in code block
                    md_file.write("```\n")
                    
                    # Limit output to 1000 lines to avoid overwhelming the file
                    lines = text.splitlines()[:1000]
                    md_file.write("\n".join(lines))
                    
                    if len(lines) == 1000 and len(text.splitlines()) > 1000:
                        md_file.write("\n... (content truncated) ...")
                        
                    md_file.write("\n```\n\n")
                    
                    file_count += 1
                    if file_count >= max_files:
                        break
                except Exception as e:
                    md_file.write(f"Error processing file: {str(e)}\n\n")
        
        return output_path


def markdown_to_pdf(markdown_path, pdf_path):
    """Convert markdown to PDF using pandoc if available."""
    try:
        # Check if pandoc is installed
        if shutil.which('pandoc') is None:
            print("Pandoc not found. Using alternative method...")
            return False
        
        # Try to convert with pandoc
        cmd = ['pandoc', markdown_path, '-o', pdf_path]
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"Error converting with pandoc: {e}")
        return False


def create_html_file(markdown_path, html_path):
    """Convert markdown to HTML."""
    try:
        with open(markdown_path, 'r', encoding='utf-8') as md_file:
            md_content = md_file.read()
        
        # Very simple markdown to HTML conversion
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Directory Content</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                pre {{ background-color: #f5f5f5; padding: 10px; overflow-x: auto; }}
                code {{ font-family: 'Courier New', monospace; }}
            </style>
        </head>
        <body>
        """
        
        # Very simple markdown conversion
        # Headers
        md_content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', md_content, flags=re.MULTILINE)
        md_content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', md_content, flags=re.MULTILINE)
        md_content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', md_content, flags=re.MULTILINE)
        
        # Code blocks
        code_blocks = []
        
        def replace_code_block(match):
            code = match.group(1)
            code_blocks.append(f'<pre><code>{code}</code></pre>')
            return f'[CODE_BLOCK_{len(code_blocks)-1}]'
        
        # Replace code blocks with placeholders
        md_content = re.sub(r'```\n(.*?)\n```', replace_code_block, md_content, flags=re.DOTALL)
        
        # Replace placeholders with HTML
        for i, block in enumerate(code_blocks):
            md_content = md_content.replace(f'[CODE_BLOCK_{i}]', block)
        
        html_content += md_content + "</body></html>"
        
        with open(html_path, 'w', encoding='utf-8') as html_file:
            html_file.write(html_content)
            
        return True
    except Exception as e:
        print(f"Error creating HTML: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert directory contents to PDF")
    parser.add_argument("directory", help="Directory to process")
    parser.add_argument("--output", "-o", default="directory_content.pdf", 
                        help="Output PDF file path (default: directory_content.pdf)")
    parser.add_argument("--max-files", type=int, default=100,
                        help="Maximum number of files to process (default: 100)")
    parser.add_argument("--format", choices=['pdf', 'markdown', 'html'], default='pdf',
                        help="Output format (default: pdf)")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        return
    
    try:
        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as temp_md:
            md_path = temp_md.name
        
        print(f"Creating markdown file...")
        create_markdown_file(args.directory, md_path)
        
        if args.format == 'markdown':
            # Just copy the markdown file to the output
            shutil.copy(md_path, args.output)
            print(f"Markdown file created: {args.output}")
        elif args.format == 'html':
            # Create HTML
            html_path = args.output if args.output.endswith('.html') else args.output.replace('.pdf', '.html')
            if create_html_file(md_path, html_path):
                print(f"HTML file created: {html_path}")
            else:
                print("Failed to create HTML file")
        else:
            # Try to convert to PDF
            if markdown_to_pdf(md_path, args.output):
                print(f"PDF created successfully: {args.output}")
            else:
                # Fallback: save the markdown file
                fallback_path = args.output.replace('.pdf', '.md')
                shutil.copy(md_path, fallback_path)
                print(f"Could not create PDF. Markdown file saved instead: {fallback_path}")
        
        # Clean up
        os.unlink(md_path)
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()