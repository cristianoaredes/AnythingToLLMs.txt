import re
import sys

def extract_mermaid_diagrams(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find all mermaid code blocks
    pattern = r'```mermaid\n(.*?)```'
    diagrams = re.findall(pattern, content, re.DOTALL)
    
    return diagrams

def validate_mermaid_diagram(diagram, index):
    # Basic validation checks
    issues = []
    
    # Check for unmatched brackets
    open_brackets = diagram.count('[')
    close_brackets = diagram.count(']')
    if open_brackets != close_brackets:
        issues.append(f"Unmatched square brackets: {open_brackets} opening vs {close_brackets} closing")
    
    open_parens = diagram.count('(')
    close_parens = diagram.count(')')
    if open_parens != close_parens:
        issues.append(f"Unmatched parentheses: {open_parens} opening vs {close_parens} closing")
    
    # Check for common Mermaid syntax errors
    if 'flowchart' in diagram and '-->' in diagram and not re.search(r'\w+\s*-->\s*\w+', diagram):
        issues.append("Flowchart arrows (-->) may be malformed")
    
    # Check for quotes in node text
    if re.search(r'\[\s*[^"\]]*"[^"\]]*\]', diagram):
        issues.append("Node text with quotes should be wrapped in double quotes")
    
    return issues

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_mermaid.py <markdown_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    diagrams = extract_mermaid_diagrams(file_path)
    
    print(f"Found {len(diagrams)} Mermaid diagrams in {file_path}")
    
    all_valid = True
    for i, diagram in enumerate(diagrams):
        issues = validate_mermaid_diagram(diagram, i)
        if issues:
            all_valid = False
            print(f"\nDiagram #{i+1} has issues:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"Diagram #{i+1} looks valid")
    
    if all_valid:
        print("\nAll diagrams appear to be valid!")
    else:
        print("\nSome diagrams have issues that need to be fixed.")
