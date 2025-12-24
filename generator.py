from groq import Groq


class GeneratorAgent:
    """Code generation specialist"""
    
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = 0.6
        self.max_tokens = 800
        
        self.system_prompt = """You are a senior Python developer specializing in writing correct, efficient code.

Your responsibilities:
- Write clean, readable Python functions
- Handle edge cases (empty input, None, single elements, large inputs)
- Include proper error handling and assertions
- Add docstrings explaining functionality
- ALWAYS include necessary import statements at the TOP

Output rules:
- Provide ONLY the Python function code with imports
- No markdown formatting (no backticks)
- No explanations outside the code
- Format: imports first, then function definition"""
    
    def generate(self, problem: str, feedback: str = None) -> str:
        if feedback:
            user_prompt = self._create_fix_prompt(problem, feedback)
            print(f"\n{'='*60}")
            print("🔄 GENERATOR: Fixing code based on feedback...")
            print(f"{'='*60}")
        else:
            user_prompt = self._create_initial_prompt(problem)
            print(f"\n{'='*60}")
            print("🤖 GENERATOR: Writing initial code...")
            print(f"{'='*60}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # FIXED: Robust response parsing
            raw_code = self._extract_chat_content(response)
            cleaned_code = self._clean_code(raw_code)
            
            # Auto-fix missing imports
            fixed_code = self._auto_add_imports(cleaned_code)
            
            print("✓ Code generated successfully")
            print(f"Length: {len(fixed_code)} characters")
            return fixed_code
            
        except Exception as e:
            print(f"✗ Generation failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"# Error: {str(e)}"
    
    def _extract_chat_content(self, response) -> str:
        """
        Robustly extract content from Groq API response.
        Works across different SDK versions and response formats.
        """
        if response is None:
            raise ValueError("Empty response from API")
        
        # Try object-style access first (most common)
        try:
            if hasattr(response, 'choices'):
                choices = response.choices
                
                if not choices or len(choices) == 0:
                    raise ValueError("Empty choices in response")
                
                first_choice = choices[0]
                
                # Check if first_choice is dict-like
                if isinstance(first_choice, dict):
                    message = first_choice.get('message', {})
                    if isinstance(message, dict):
                        content = message.get('content', '')
                        if content:
                            return content
                        raise ValueError("Empty content in dict-style response")
                
                # Check if first_choice is object-like
                if hasattr(first_choice, 'message'):
                    message = first_choice.message
                    
                    if isinstance(message, dict):
                        content = message.get('content', '')
                    elif hasattr(message, 'content'):
                        content = message.content
                    else:
                        raise ValueError(f"Message has no content attribute: {type(message)}")
                    
                    if content:
                        return content
                    raise ValueError("Empty content in response")
                
                # If we get here, first_choice structure is unexpected
                raise ValueError(f"Unexpected choice structure: {type(first_choice)}")
        
        except AttributeError:
            pass  # Fall through to dict-style access
        
        # Try dict-style access
        if isinstance(response, dict):
            choices = response.get('choices', [])
            if not choices:
                raise ValueError("Empty choices in dict response")
            
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                message = first_choice.get('message', {})
                if isinstance(message, dict):
                    content = message.get('content', '')
                    if content:
                        return content
        
        # If nothing worked, raise detailed error
        raise ValueError(f"Could not extract content from response. Response type: {type(response)}")
    
    def _create_initial_prompt(self, problem: str) -> str:
        return f"""Write a Python function to solve this problem:

{problem}

⚠️ CRITICAL REQUIREMENTS:
1. Include ALL necessary import statements at the VERY TOP (import re, import math, etc.)
2. Handle ALL edge cases (empty, None, single element)
3. Add input validation
4. Add docstring

MANDATORY FORMAT:
import module_name  # If you use any module, import it HERE at the TOP

def function_name(param):
    # Implementation
    pass

Write complete code with imports FIRST."""
    
    def _create_fix_prompt(self, problem: str, feedback: str) -> str:
        return f"""Your previous code failed.

PROBLEM:
{problem}

FEEDBACK:
{feedback}

⚠️ CRITICAL: If you use any modules (re, math, json, etc.), you MUST add the import statement at the VERY TOP of your code.

Fix the code. Write ONLY the corrected function WITH all necessary imports at the top."""
    
    def _clean_code(self, raw_code: str) -> str:
        """Clean LLM output and preserve imports"""
        code = raw_code.strip()
        
        # Remove markdown backticks
        if code.startswith('```'):
            code = code[9:].strip()
        elif code.startswith('```'):
            code = code[3:].strip()
        if code.endswith('```'):
            code = code[:-3].strip()
        
        lines = code.split('\n')
        
        # Collect imports AND functions separately
        imports = []
        function_lines = []
        in_func = False
        
        for line in lines:
            stripped = line.strip()
            
            # Collect import statements
            if stripped.startswith(('import ', 'from ')):
                if line not in imports:  # Avoid duplicates
                    imports.append(line)
                continue
            
            # Skip empty lines before function starts
            if not in_func and not stripped:
                continue
            
            # Collect function/class definitions and their bodies
            if stripped.startswith(('def ', 'class ')):
                in_func = True
                function_lines.append(line)
            elif in_func:
                # Check if this is test/example code
                if stripped and not any(line.startswith(indent) for indent in ['    ', '\t']):
                    # Unindented line outside function
                    if stripped.startswith(('def ', 'class ')):
                        # New function, include it
                        function_lines.append(line)
                    elif any(x in stripped.lower() for x in ['if __name__', 'print(', '# test', '# example']):
                        # Test code, stop here
                        break
                    else:
                        # Unknown unindented code, might be continuation
                        break
                else:
                    # Indented line or empty line, part of function
                    function_lines.append(line)
        
        # Combine imports + functions
        result_lines = imports + ([''] if imports and function_lines else []) + function_lines
        return '\n'.join(result_lines).strip()
    
    def _auto_add_imports(self, code: str) -> str:
        """Automatically detect and add missing imports"""
        
        # Ensure code is a string
        if not isinstance(code, str):
            return code
        
        # Comprehensive import patterns
        import_patterns = {
            're.': 'import re',
            'math.': 'import math',
            'json.': 'import json',
            'os.': 'import os',
            'sys.': 'import sys',
            'random.': 'import random',
            'datetime.': 'import datetime',
            'collections.': 'import collections',
            'itertools.': 'import itertools',
            'heapq.': 'import heapq',
            'functools.': 'import functools',
            'typing.': 'import typing',
            'defaultdict': 'from collections import defaultdict',
            'Counter': 'from collections import Counter',
            'deque': 'from collections import deque',
        }
        
        missing_imports = []
        
        # Check which modules are used but not imported
        for pattern, import_stmt in import_patterns.items():
            if pattern in code and import_stmt not in code:
                missing_imports.append(import_stmt)
                print(f"🔧 AUTO-FIX: Adding missing import: {import_stmt}")
        
        # Prepend missing imports
        if missing_imports:
            imports_block = '\n'.join(missing_imports)
            code = imports_block + '\n\n' + code
        
        return code
