from groq import Groq
from typing import List, Dict
import json
import re
import ast
import importlib.util
from generator import GeneratorAgent
from test_generator import TestCaseGenerator
from verifier import CodeVerifier
from debugger import DebuggerAgent
from failure_report import FailureReportGenerator


class DualLLMCodeVerificationSystem:
    """
    Complete self-verifying code generation system
    Workflow: Generate Tests → Generate Code → Verify → Debug → Fix → Repeat
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
        # Initialize all agents
        self.test_generator = TestCaseGenerator(api_key)
        self.code_generator = GeneratorAgent(api_key)
        self.verifier = CodeVerifier()
        self.debugger = DebuggerAgent(api_key)
        self.report_generator = FailureReportGenerator()
        
        self.max_attempts = 8
    
    def generate_verified_code(self, problem: str, num_tests: int = 8) -> Dict:
        """
        Complete workflow: Generate verified, tested code
        
        Args:
            problem: Problem description
            num_tests: Number of test cases to generate
            
        Returns:
            Dict with results
        """
        
        # FIXED: Clear history at start of each run
        history = []
        
        print("\n" + "="*70)
        print("🚀 DUAL-LLM CODE VERIFICATION SYSTEM")
        print("="*70)
        print(f"\n📋 Problem:\n{problem}")
        print("="*70)
        
        # STEP 1: Generate comprehensive test cases
        print("\n" + "#"*70)
        print("# STEP 1: GENERATE TEST CASES")
        print("#"*70)
        
        test_cases = self.test_generator.generate_test_cases(problem, num_tests)
        
        if not test_cases or len(test_cases) == 0:
            return {
                "success": False,
                "message": "Failed to generate test cases",
                "code": None,
                "history": history
            }
        
        # STEP 2: Iterative code generation with debugging
        # FIXED: Initialize variables before loop
        code = None
        test_results = []
        error_msg = "Unknown error"
        debugger_feedback = None
        previous_feedback = None
        
        for attempt in range(1, self.max_attempts + 1):
            print("\n" + "#"*70)
            print(f"# ITERATION {attempt}/{self.max_attempts}")
            print("#"*70)
            
            # Generate code
            print("\n## Phase 1: Code Generation")
            code = self.code_generator.generate(problem, feedback=debugger_feedback)
            
            print("\n📝 Generated Code:")
            print("-" * 60)
            print(code)
            print("-" * 60)
            
            # Verify code
            print("\n## Phase 2: Code Verification")
            passed, test_results, error_msg = self.verifier.verify(code, test_cases)
            
            # Record attempt
            history.append({
                'attempt': attempt,
                'code': code,
                'passed': passed,
                'test_results': test_results,
                'error': error_msg if not passed else None
            })
            
            if passed:
                print("\n" + "="*70)
                print(f"🎉 SUCCESS IN {attempt} ATTEMPT(S)!")
                print("="*70)
                
                return {
                    "success": True,
                    "code": code,
                    "attempts": attempt,
                    "test_cases": test_cases,
                    "test_results": test_results,
                    "message": f"All {len(test_cases)} tests passed",
                    "history": history
                }
            
            # Debug failures
            print("\n## Phase 3: Debugging Failed Code")
            
            if attempt < self.max_attempts:
                failed_tests = [t for t in test_results if t['status'] != 'PASS']
                
                # FIXED: Pass iteration and previous feedback
                debugger_feedback = self.debugger.analyze(
                    code=code,
                    problem=problem,
                    test_failures=failed_tests,
                    error_msg=error_msg,
                    iteration=attempt,
                    previous_feedback=previous_feedback if attempt > 1 else None
                )
                
                # Save for next iteration
                previous_feedback = debugger_feedback
                
                print("\n🔄 Attempting to fix based on debugger feedback...")
        
        # Max attempts reached - generate debugging report
        print("\n" + "="*70)
        print(f"❌ FAILED AFTER {self.max_attempts} ATTEMPTS")
        print("="*70)

        result = {
            "success": False,
            "code": code,
            "attempts": self.max_attempts,
            "max_attempts": self.max_attempts,
            "test_cases": test_cases,
            "test_results": test_results,
            "message": f"Failed after {self.max_attempts} attempts",
            "error": error_msg,
            "history": history
        }

        # Generate debugging report for user
        debug_report = self.report_generator.generate_report(result)
        result['debug_report'] = debug_report

        return result
    
    def save_result(self, result: Dict, filename: str = "verified_code.py"):
        """Save verified code to file"""
        if result['success']:
            print("\n" + "="*70)
            print("✅ VERIFIED CODE:")
            print("="*70)
            print(result['code'])
            print("="*70)
            
            # Save to file
            try:
                with open(filename, 'w') as f:
                    f.write(result['code'])
                print(f"\n💾 Code saved to: {filename}")
            except Exception as e:
                print(f"\n❌ Failed to save file: {e}")
        else:
            # Print debugging report
            if 'debug_report' in result:
                print(result['debug_report'])
