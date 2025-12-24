from groq import Groq
from typing import List, Dict
import json
import re


class TestCaseGenerator:
    """
    LLM-powered test case generation
    Creates comprehensive test suites from problem descriptions
    """
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = 0.4
        self.max_tokens = 1000
        
        self.system_prompt = """You are an expert software tester specializing in comprehensive test case design.

Your job is to generate thorough test cases that cover:
1. Happy path (typical valid inputs)
2. Edge cases (empty, single element, boundaries)
3. Boundary values (min/max, zero, negative)
4. Invalid inputs (None, wrong types, invalid values)
5. Special cases specific to the problem

Output format: JSON array of test cases
Each test case must have:
- "description": what this test checks
- "input": the input value(s)
- "expected": the expected output
- "category": one of [happy_path, edge_case, boundary, invalid, special]

Be specific with actual values, not placeholders."""
    
    def generate_test_cases(self, problem: str, num_tests: int = 10) -> List[Dict]:
        """
        Generate test cases from problem description
        
        Args:
            problem: Problem description
            num_tests: Number of test cases to generate
            
        Returns:
            List of test case dictionaries
        """
        
        print(f"\n{'='*60}")
        print(f"🧪 TEST GENERATOR: Creating {num_tests} test cases...")
        print(f"{'='*60}")
        
        prompt = self._create_prompt(problem, num_tests)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            raw_output = response.choices[0].message.content
            test_cases = self._parse_test_cases(raw_output)
            
            # ADDED: Validate output types match problem
            test_cases = self._validate_output_types(test_cases, problem)
            
            print(f"✓ Generated {len(test_cases)} test cases")
            self._print_test_summary(test_cases)
            
            return test_cases
            
        except Exception as e:
            print(f"✗ Test generation failed: {str(e)}")
            return self._create_fallback_tests(problem)
    
    def _create_prompt(self, problem: str, num_tests: int) -> str:
        """Create prompt for test case generation"""
        
        # ADDED: Infer expected output type from problem
        output_type_guidance = self._get_output_type_guidance(problem)
        
        return f"""Generate {num_tests} comprehensive test cases for this problem:

{problem}

{output_type_guidance}

⚠️ CRITICAL REQUIREMENTS:
1. Read the problem statement VERY CAREFULLY
2. Understand what the function should RETURN (the output type)
3. Generate "expected" values that match the correct OUTPUT TYPE
4. If problem says "ignore spaces/punctuation", ONLY letters count
5. Cover ALL categories: happy_path, edge_case, boundary, invalid, special

Input format rules:
- For functions with multiple parameters: provide input as a list/tuple
- For single parameter functions: provide input directly

Output ONLY a JSON array in this exact format:

[
  {{
    "description": "Describe what this test checks",
    "input": <value_or_list>,
    "expected": <correct_output_value>,
    "category": "happy_path"
  }},
  {{
    "description": "Another test case",
    "input": <value_or_list>,
    "expected": <correct_output_value>,
    "category": "edge_case"
  }}
]

Generate the JSON array now:"""
    
    def _get_output_type_guidance(self, problem: str) -> str:
        """Generate output type guidance based on problem description"""
        
        problem_lower = problem.lower()
        
        # Sorting problems
        if any(word in problem_lower for word in ['sort', 'arrange', 'order']):
            return """
🎯 OUTPUT TYPE: This is a SORTING problem
- Input: An array/list of elements
- Expected output: A SORTED ARRAY/LIST (same type as input)
- Example: input=[3,1,2] → expected=[1,2,3] ✅
- Example: input=[3,1,2] → expected=6 ❌ WRONG (that's a sum!)
"""
        
        # Sum/count problems
        elif any(word in problem_lower for word in ['sum', 'total', 'count', 'add']):
            return """
🎯 OUTPUT TYPE: This is a SUM/COUNT problem
- Input: An array/list of elements
- Expected output: A NUMBER (int or float)
- Example: input=[1,2,3] → expected=6 ✅
- Example: input=[1,2,3] → expected=[1,2,3] ❌ WRONG (that's the same array!)
"""
        
        # Search/find problems
        elif any(word in problem_lower for word in ['search', 'find', 'index', 'position']):
            return """
🎯 OUTPUT TYPE: This is a SEARCH problem
- Input: An array and a target value
- Expected output: An INDEX (integer) or -1 if not found
- Example: input=[[1,2,3], 2] → expected=1 ✅
- Example: input=[[1,2,3], 5] → expected=-1 ✅
"""
        
        # Boolean problems
        elif any(word in problem_lower for word in ['is_', 'check', 'valid', 'palindrome', 'verify']):
            return """
🎯 OUTPUT TYPE: This is a BOOLEAN problem
- Input: Value to check
- Expected output: True or False
- Example: input="racecar" → expected=True ✅
- Example: input="hello" → expected=False ✅
"""
        
        # Generic guidance
        else:
            return """
⚠️ IMPORTANT: Determine the OUTPUT TYPE from the problem description
- What should the function RETURN?
- Match the "expected" values to that type
"""
    
    def _validate_output_types(self, test_cases: List[Dict], problem: str) -> List[Dict]:
        """Validate that test case outputs match expected type for problem"""
        
        problem_lower = problem.lower()
        valid_cases = []
        
        # Determine expected output type
        if any(word in problem_lower for word in ['sort', 'arrange', 'order']):
            expected_type = list
            type_name = "list/array"
        elif any(word in problem_lower for word in ['sum', 'total', 'count', 'add']):
            expected_type = (int, float)
            type_name = "number"
        elif any(word in problem_lower for word in ['search', 'find', 'index']):
            expected_type = int
            type_name = "integer (index)"
        elif any(word in problem_lower for word in ['is_', 'check', 'valid', 'palindrome']):
            expected_type = bool
            type_name = "boolean"
        else:
            # Can't determine, accept all
            return test_cases
        
        # Filter test cases
        for tc in test_cases:
            if isinstance(tc['expected'], expected_type):
                valid_cases.append(tc)
            else:
                print(f"⚠️  Skipping invalid test: expected {type_name}, got {type(tc['expected']).__name__}")
                print(f"    Input: {tc['input']}, Expected: {tc['expected']}")
        
        # If all tests were invalid, return original (better than nothing)
        if not valid_cases:
            print("⚠️  All tests invalid, using original set")
            return test_cases
        
        return valid_cases
    
    def _parse_test_cases(self, raw_output: str) -> List[Dict]:
        """Parse LLM output to extract test cases"""
        
        # Try to find JSON array in output
        json_match = re.search(r'\[.*\]', raw_output, re.DOTALL)
        
        if json_match:
            try:
                test_cases = json.loads(json_match.group(0))
                
                # Validate structure
                validated = []
                for tc in test_cases:
                    if all(key in tc for key in ['input', 'expected']):
                        validated.append({
                            'description': tc.get('description', 'Test case'),
                            'input': tc['input'],
                            'expected': tc['expected'],
                            'category': tc.get('category', 'general')
                        })
                
                return validated
                
            except json.JSONDecodeError as e:
                print(f"✗ JSON parsing failed: {e}")
                return self._create_fallback_tests("")
        
        print("✗ No valid JSON found in output")
        return self._create_fallback_tests("")
    
    def _create_fallback_tests(self, problem: str = "") -> List[Dict]:
        """Create basic fallback tests based on problem type"""
        
        problem_lower = problem.lower()
        
        # Generate appropriate fallback based on problem type
        if 'sort' in problem_lower:
            return [{
                "description": "Basic sort test",
                "input": [3, 1, 2],
                "expected": [1, 2, 3],
                "category": "happy_path"
            }]
        elif 'sum' in problem_lower or 'add' in problem_lower:
            return [{
                "description": "Basic sum test",
                "input": [1, 2, 3],
                "expected": 6,
                "category": "happy_path"
            }]
        elif 'search' in problem_lower or 'find' in problem_lower:
            return [{
                "description": "Basic search test",
                "input": [[1, 2, 3], 2],
                "expected": 1,
                "category": "happy_path"
            }]
        else:
            # Generic fallback
            return [{
                "description": "Basic test",
                "input": "test",
                "expected": True,
                "category": "happy_path"
            }]
    
    def _print_test_summary(self, test_cases: List[Dict]):
        """Print summary of generated tests"""
        categories = {}
        for tc in test_cases:
            cat = tc.get('category', 'general')
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\n📊 Test Coverage:")
        for cat, count in categories.items():
            print(f"  {cat}: {count} tests")
