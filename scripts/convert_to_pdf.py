#!/usr/bin/env python3
"""
Convert markdown review documents to PDF format.
"""

import markdown
from weasyprint import HTML
from pathlib import Path

project_root = Path(__file__).parent.parent
input_dir = project_root / "docs" / "medical_review"
output_dir = input_dir  # Save PDFs in same directory

# CSS for better formatting
css_style = """
<style>
    @page {
        size: letter;
        margin: 0.75in;
        @bottom-right {
            content: counter(page) " / " counter(pages);
        }
    }
    body {
        font-family: "Times New Roman", serif;
        font-size: 11pt;
        line-height: 1.4;
    }
    h1 {
        font-size: 20pt;
        margin-top: 0;
        border-bottom: 2px solid #333;
        padding-bottom: 10px;
    }
    h2 {
        font-size: 16pt;
        margin-top: 24pt;
        border-bottom: 1px solid #666;
        padding-bottom: 5px;
        page-break-after: avoid;
    }
    h3 {
        font-size: 13pt;
        margin-top: 18pt;
        page-break-after: avoid;
    }
    hr {
        border: none;
        border-top: 1px solid #ccc;
        margin: 12pt 0;
    }
    strong {
        font-weight: bold;
    }
    p {
        margin: 6pt 0;
    }
    ul, ol {
        margin: 6pt 0;
        padding-left: 20pt;
    }
    li {
        margin: 3pt 0;
    }
    .question-scenario {
        background-color: #f9f9f9;
        padding: 10pt;
        margin: 10pt 0;
        border-left: 3px solid #333;
    }
</style>
"""

def convert_md_to_pdf(md_file):
    """Convert a markdown file to PDF."""
    print(f"Converting {md_file.name}...")

    # Read markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # Convert markdown to HTML
    html_content = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])

    # Wrap in HTML structure with CSS
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        {css_style}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Convert to PDF
    pdf_file = md_file.with_suffix('.pdf')
    HTML(string=full_html).write_pdf(pdf_file)

    print(f"  ✓ Created: {pdf_file.name}")
    return pdf_file

# Convert all markdown files
md_files = [
    'CATEGORIZATION_EXPLAINED.md',
    'Clinical_Findings_Questions.md',
    'Diagnosis_Questions.md',
    'Mechanism_Pathophysiology_Questions.md',
    'Next_Step_Workup_Questions.md',
    'Treatment_Management_Questions.md'
]

print("Converting markdown files to PDF...")
print()

for md_filename in md_files:
    md_path = input_dir / md_filename
    if md_path.exists():
        convert_md_to_pdf(md_path)
    else:
        print(f"  ✗ Not found: {md_filename}")

print()
print("✓ PDF conversion complete!")
print(f"PDFs saved to: {output_dir}")
