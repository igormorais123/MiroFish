"""Fix 3 bugs in report_agent.py: Helena system_prompt, tool_call sanitization"""
import re
import sys

filepath = sys.argv[1] if len(sys.argv) > 1 else "/app/backend/app/services/report_agent.py"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

# FIX 1: Helena Strategos - system_prompt/user_message -> messages format
old_helena = """                helena_llm = LLMClient(model=model_name)
                result = helena_llm.chat(
                    system_prompt=HELENA_SYSTEM_PROMPT,
                    user_message=user_prompt,
                )"""

new_helena = """                helena_llm = LLMClient(model=model_name)
                result = helena_llm.chat(
                    messages=[
                        {"role": "system", "content": HELENA_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.4,
                    max_tokens=8192,
                )"""

if old_helena in content:
    content = content.replace(old_helena, new_helena)
    changes += 1
    print("FIX 1: Helena Strategos system_prompt -> messages format")
else:
    print("FIX 1: SKIP - pattern not found")

# FIX 2: Add sanitization function near the top (after imports)
sanitize_func = '''

def _sanitize_section_content(text: str) -> str:
    """Remove tool_call XML, thinking tags and agent artifacts from section content."""
    if not text:
        return text
    # Remove <tool_call>...</tool_call> blocks
    text = re.sub(r'<tool_call>[\\s\\S]*?</tool_call>', '', text)
    # Remove <think>...</think> blocks
    text = re.sub(r'<think>[\\s\\S]*?</think>', '', text)
    # Remove <function>...</function> blocks
    text = re.sub(r'<function[^>]*>[\\s\\S]*?</function>', '', text)
    # Remove <parameters>...</parameters> blocks
    text = re.sub(r'<parameters>[\\s\\S]*?</parameters>', '', text)
    # Remove lines that are clearly agent reasoning (not report content)
    lines = text.split('\\n')
    clean_lines = []
    skip_patterns = [
        'insight_forge', 'Preciso tentar', 'Vou entrevistar',
        'Isso sugere que os dados', 'talvez estejam em um formato',
        'ferramentas de busca de forma direta',
    ]
    for line in lines:
        if any(p in line for p in skip_patterns):
            continue
        clean_lines.append(line)
    text = '\\n'.join(clean_lines)
    # Clean consecutive blank lines
    text = re.sub(r'\\n{3,}', '\\n\\n', text)
    return text.strip()

'''

# Insert after the last import line
if '_sanitize_section_content' not in content:
    # Find position after imports
    marker = "from ..utils.llm_client import LLMClient"
    if marker in content:
        content = content.replace(marker, marker + sanitize_func)
        changes += 1
        print("FIX 2a: Added _sanitize_section_content function")

# FIX 2b: Apply sanitization in forced generation path
old_forced_else = '''        else:
            final_answer = response

        # Registra log de conclusao da geracao do conteudo da secao'''

new_forced_else = '''        else:
            final_answer = response

        # Sanitizar conteudo final (remover tool_calls, thinking, etc.)
        final_answer = _sanitize_section_content(final_answer)

        # Registra log de conclusao da geracao do conteudo da secao'''

if old_forced_else in content:
    content = content.replace(old_forced_else, new_forced_else)
    changes += 1
    print("FIX 2b: Added sanitization in forced generation path")

# FIX 2c: Apply sanitization in normal Final Answer path
old_normal = '''            if "Final Answer:" in assistant_content:
                final_answer = assistant_content.split("Final Answer:")[-1].strip()'''

new_normal = '''            if "Final Answer:" in assistant_content:
                final_answer = assistant_content.split("Final Answer:")[-1].strip()
                final_answer = _sanitize_section_content(final_answer)'''

if old_normal in content:
    content = content.replace(old_normal, new_normal, 1)
    changes += 1
    print("FIX 2c: Added sanitization in normal Final Answer path")

with open(filepath, "w") as f:
    f.write(content)

print(f"\nTotal: {changes} fixes applied")
