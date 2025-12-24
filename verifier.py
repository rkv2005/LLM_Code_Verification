import ast
import inspect  # ADD THIS
from typing import Dict, List, Tuple


class CodeVerifier:
    """
    Automated code execution and verification
    Tests generated code against provided test cases
    """
    
    def __init__(self):
        self.last_verification = None
    
    def verify(self, code: str, test_cases: List[Dict]) -> Tuple[bool, List[Dict], str]:
        """
        Execute code with test cases and verify correctness
        
        Args:
            code: Python function code to test
            test_cases: List of dicts with 'input' and 'expected' keys
            
        Returns:
            Tuple of (all_passed, test_results, error_message)
        """
        
        print(f"\n{'='*60}")
        print("✅ VERIFIER: Running verification...")
        print(f"{'='*60}")
        
        # Step 1: Syntax check
        try:
            ast.parse(code)
            print("✓ Syntax valid")
        except SyntaxError as e:
            error_msg = f"Syntax Error: {str(e)}"
            print(f"✗ {error_msg}")
            return False, [], error_msg
        
        # Step 2: Execute code
        try:
            namespace = {}
            exec(code, namespace)
            print("✓ Code executed without errors")
        except Exception as e:
            error_msg = f"Execution Error: {str(e)}"
            print(f"✗ {error_msg}")
            return False, [], error_msg
        
        # Step 3: Find the function
        func_name = self._find_function(namespace)
        if not func_name:
            error_msg = "No function found in generated code"
            print(f"✗ {error_msg}")
            return False, [], error_msg
        
        func = namespace[func_name]
        print(f"✓ Found function: {func_name}()")
        
        # Step 4: Run test cases
        test_results = []
        all_passed = True
        
        print(f"\n{'='*60}")
        print(f"Running {len(test_cases)} test cases...")
        print(f"{'='*60}")
        
        for i, test in enumerate(test_cases, 1):
            result = self._run_single_test(func, test, i)
            test_results.append(result)
            
            if result['status'] != 'PASS':
                all_passed = False
        
        # Step 5: Compile results
        if all_passed:
            success_msg = f"All {len(test_cases)} tests passed"
            print(f"\n✅ {success_msg}")
            self.last_verification = {
                'passed': True,
                'results': test_results
            }
            return True, test_results, success_msg
        else:
            failed_count = len([r for r in test_results if r['status'] != 'PASS'])
            error_msg = f"{failed_count}/{len(test_cases)} tests failed"
            print(f"\n❌ {error_msg}")
            self.last_verification = {
                'passed': False,
                'results': test_results
            }
            return False, test_results, error_msg
    
    def _find_function(self, namespace: dict) -> str:
        """Find the main function in namespace"""
        for name, obj in namespace.items():
            if callable(obj) and not name.startswith('_'):
                return name
        return None
    
    def _run_single_test(self, func, test: Dict, test_num: int) -> Dict:
        """Execute a single test case"""
        inputs = test['input']
        expected = test['expected']
        
        try:
            # FIXED: Use function signature to determine how to call
            sig = inspect.signature(func)
            num_params = len(sig.parameters)
            
            # Call function based on signature and input type
            if isinstance(inputs, list):
                # Empty list case
                if len(inputs) == 0:
                    if num_params == 1:
                        actual = func(inputs)  # Pass empty list
                    else:
                        actual = func()  # No args
                
                # Non-empty list
                elif num_params == 1:
                    # Function takes 1 parameter → pass list as single arg
                    actual = func(inputs)
                
                elif num_params == len(inputs):
                    # Function takes N parameters → unpack N inputs
                    actual = func(*inputs)
                
                else:
                    # Ambiguous case, try unpacking first
                    try:
                        actual = func(*inputs)
                    except TypeError:
                        # If that fails, try passing as single arg
                        actual = func(inputs)
            
            elif isinstance(inputs, tuple):
                # Tuples always unpack
                actual = func(*inputs)
            
            else:
                # Single non-list argument
                actual = func(inputs)
            
            # Check result with float tolerance
            if self._values_match(actual, expected):
                print(f"  ✓ Test {test_num}: PASS")
                return {
                    'test_num': test_num,
                    'input': inputs,
                    'expected': expected,
                    'actual': actual,
                    'status': 'PASS',
                    'description': test.get('description', '')
                }
            else:
                print(f"  ✗ Test {test_num}: FAIL")
                print(f"    Input: {inputs}")
                print(f"    Expected: {expected}")
                print(f"    Got: {actual}")
                return {
                    'test_num': test_num,
                    'input': inputs,
                    'expected': expected,
                    'actual': actual,
                    'status': 'FAIL',
                    'description': test.get('description', '')
                }
        
        except Exception as e:
            print(f"  ✗ Test {test_num}: ERROR - {str(e)}")
            print(f"    Input: {inputs}")
            return {
                'test_num': test_num,
                'input': inputs,
                'expected': expected,
                'actual': f"ERROR: {str(e)}",
                'status': 'ERROR',
                'description': test.get('description', '')
            }
    
    def _values_match(self, actual, expected) -> bool:
        """Check if actual matches expected with float tolerance"""
        
        # Handle float comparison with tolerance
        if isinstance(expected, float) and isinstance(actual, (int, float)):
            return abs(float(actual) - expected) < 1e-9
        
        # Handle lists of floats
        if isinstance(expected, list) and isinstance(actual, list):
            if len(expected) != len(actual):
                return False
            return all(
                abs(float(a) - float(e)) < 1e-9 if isinstance(e, float) else a == e
                for a, e in zip(actual, expected)
            )
        
        # Default exact comparison
        return actual == expected
    
    def get_last_verification(self) -> Dict:
        """Get results of last verification"""
        return self.last_verification
