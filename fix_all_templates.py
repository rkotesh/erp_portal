import os
import re

def fix_templates(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 1. Join split tags (tags containing \n)
                def join_tag(match):
                    return match.group(0).replace('\n', ' ').replace('  ', ' ')
                
                content = re.sub(r'\{%.*?%\}', join_tag, content, flags=re.DOTALL)

                # 2. Fix spaces around ==
                def replace_tag_spaces(match):
                    tag_inner = match.group(1)
                    # Add spaces around ==
                    tag_inner = re.sub(r'([^\s=])==([^\s=])', r'\1 == \2', tag_inner)
                    tag_inner = re.sub(r'([^\s=])==(\s)', r'\1 ==\2', tag_inner)
                    tag_inner = re.sub(r'(\s)==([^\s=])', r'\1== \2', tag_inner)
                    # Handle multiple passes or existing partial spaces
                    tag_inner = re.sub(r'\s*==\s*', ' == ', tag_inner)
                    return '{%' + tag_inner + '%}'

                content = re.sub(r'\{%(.*?)%\}', replace_tag_spaces, content, flags=re.DOTALL)
                
                with open(path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(content)
                print(f"Processed {path}")

fix_templates(r'c:\Users\srkot\OneDrive\Desktop\my-projects\college_website\templates')
