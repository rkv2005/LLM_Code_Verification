from groq import Groq
from typing import List, Dict


class DebuggerAgent:
    """
    Code analysis and debugging specialist
    Provides detailed feedback on failed code
    """
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = 0.3  # Low temp for analytical reasoning
        self.max_tokens = 1200
        
        self.system_prompt = """You are an expert code reviewer and debugger with deep knowledge of Python.

Your job is to analyze failed code and provide specific, actionable debugging feedback.

Your analysis must include:
1. ROOT CAUSE: The fundamental reason the code failed (be specific)
2. BUGS IDENTIFIED: Exact issues with line references
3. FIX RECOMMENDATIONS: Concrete steps to fix each bug
4. EDGE CASES: What scenarios weren't handled properly

Rules:
- Be specific: reference exact lines, variables, logic errors
- Explain WHY it failed, not just WHAT failed
- Provide concrete code suggestions
- Think step-by-step through the logic
- Consider all test failures together to find patterns
- Format your response with clear section headers"""
    
    def analyze(self, code: str, problem: str, test_failures: List[Dict], 
                error_msg: str, iteration: int = 1, previous_feedback: str = None) -> str:
        """
        Analyze failed code and provide debugging feedback
        
        Args:
            code: The generated code that failed
            problem: Original problem description
            test_failures: List of failed test results
            error_msg: Overall error message
            iteration: Current iteration number
            previous_feedback: Feedback from previous iteration (if any)
            
        Returns:
            str: Detailed debugging feedback
        """
        
        print(f"\n{'='*60}")
        print(f"🔍 DEBUGGER: Analyzing failures (Iteration {iteration})...")
        print(f"{'='*60}")
        
        prompt = self._create_analysis_prompt(
            code, problem, test_failures, error_msg, iteration, previous_feedback
        )
        
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
            
            # FIXED: Robust error handling for API response
            if not response or not hasattr(response, 'choices'):
                print("✗ Invalid API response - no choices attribute")
                return self._create_fallback_feedback(code, problem, test_failures, error_msg)
            
            if not response.choices or len(response.choices) == 0:
                print("✗ API returned empty choices")
                return self._create_fallback_feedback(code, problem, test_failures, error_msg)
            
            # FIXED: Check if choices[0] has message attribute
            first_choice = response.choices[0]
            if not hasattr(first_choice, 'message'):
                print(f"✗ Invalid choice structure: {type(first_choice)}")
                return self._create_fallback_feedback(code, problem, test_failures, error_msg)
            
            # FIXED: Check if message has content attribute
            if not hasattr(first_choice.message, 'content'):
                print(f"✗ Invalid message structure: {type(first_choice.message)}")
                return self._create_fallback_feedback(code, problem, test_failures, error_msg)
            
            feedback = first_choice.message.content
            
            if not feedback or len(feedback.strip()) == 0:
                print("✗ API returned empty feedback")
                return self._create_fallback_feedback(code, problem, test_failures, error_msg)
            
            print("✓ Analysis complete")
            print(f"\n{'='*60}")
            print("🔍 DEBUGGER'S ANALYSIS:")
            print(f"{'='*60}")
            print(feedback)
            print(f"{'='*60}")
            
            return feedback
            
        except AttributeError as e:
            print(f"✗ API Response Structure Error: {str(e)}")
            print(f"   This usually means the Groq SDK version is outdated")
            print(f"   Try: pip install --upgrade groq")
            return self._create_fallback_feedback(code, problem, test_failures, error_msg)
            
        except Exception as e:
            print(f"✗ Analysis failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            return self._create_fallback_feedback(code, problem, test_failures, error_msg)
    
    def _create_analysis_prompt(self, code: str, problem: str, test_failures: List[Dict], 
                               error_msg: str, iteration: int = 1, previous_feedback: str = None) -> str:
        """Create detailed analysis prompt"""
        
        # Format test failures with clear emphasis
        failures_text = ""
        for failure in test_failures[:10]:  # Limit to first 10 to avoid token overflow
            status_emoji = "❌" if failure['status'] == 'FAIL' else "⚠️"
            failures_text += f"\n{status_emoji} Test {failure['test_num']}: {failure['status']} - {failure.get('description', 'N/A')}\n"
            failures_text += f"  Input:    {failure['input']}\n"
            failures_text += f"  Expected: {failure['expected']}\n"
            failures_text += f"  Actual:   {failure.get('actual', 'ERROR')}\n"
        
        # Add iteration context if not first attempt
        iteration_context = ""
        if iteration > 1:
            iteration_context = f"""
⚠️ ITERATION CONTEXT:
This is attempt #{iteration} to fix this code.
Previous attempts failed. 
"""
            if previous_feedback:
                iteration_context += f"""
Previous feedback was:
{previous_feedback[:500]}...
(Avoid repeating the same suggestions)
"""
        
        return f"""Analyze this code that failed verification.

ORIGINAL PROBLEM:
{problem}

{iteration_context}

GENERATED CODE:
{code}

OVERALL ERROR:
{error_msg}

FAILED TEST CASES (showing first 10):
{failures_text}

Provide detailed debugging analysis with these EXACT section headers:

**ROOT CAUSE ANALYSIS:**
What is the fundamental issue causing failures? Be specific about the logic error.

**BUGS IDENTIFIED:**
List each bug with exact details:
- Bug 1: [Describe the specific issue]
- Bug 2: [Describe the specific issue]

**FIX RECOMMENDATIONS:**
For each bug, provide specific fixes:
- Fix 1: [Explain what code to change and why]
- Fix 2: [Explain what code to change and why]

**EDGE CASES NOT HANDLED:**
What scenarios does the code miss? What assumptions are incorrect?

Be thorough and specific. The Generator will use your feedback to rewrite the code."""
    
    def _create_fallback_feedback(self, code: str, problem: str, 
                                  test_failures: List[Dict], error_msg: str) -> str:
        """Create basic feedback when LLM analysis fails"""
        
        print("⚠️  Using fallback feedback generation")
        
        # Analyze common issues
        feedback_parts = []
        
        feedback_parts.append("**ROOT CAUSE ANALYSIS:**")
        
        # Check for no function
        if "No function found" in error_msg:
            feedback_parts.append("The code generation failed completely. No valid Python function was created.")
            feedback_parts.append("\n**FIX RECOMMENDATIONS:**")
            feedback_parts.append("- Start fresh with a simple function definition")
            feedback_parts.append("- Ensure the function name matches the problem requirements")
            feedback_parts.append(f"- Based on the problem, create a basic function structure")
        
        # Check for syntax errors
        elif "Syntax Error" in error_msg or "SyntaxError" in error_msg:
            feedback_parts.append("The code has syntax errors preventing execution.")
            feedback_parts.append("\n**FIX RECOMMENDATIONS:**")
            feedback_parts.append("- Check for missing colons, parentheses, or brackets")
            feedback_parts.append("- Verify proper indentation")
            feedback_parts.append("- Ensure all strings are properly quoted")
        
        # Check for import errors
        elif "not defined" in error_msg or "ImportError" in error_msg:
            feedback_parts.append("The code uses undefined variables or missing imports.")
            feedback_parts.append("\n**FIX RECOMMENDATIONS:**")
            feedback_parts.append("- Add necessary import statements at the top")
            feedback_parts.append("- Check for typos in variable names")
            feedback_parts.append("- Ensure all used functions/modules are imported")
        
        # Test failures
        else:
            failed_count = len(test_failures)
            feedback_parts.append(f"The code executed but {failed_count} test case(s) failed.")
            feedback_parts.append("\n**FAILED TESTS:**")
            
            for failure in test_failures[:3]:
                feedback_parts.append(f"\nTest {failure['test_num']}:")
                feedback_parts.append(f"  Input: {failure['input']}")
                feedback_parts.append(f"  Expected: {failure['expected']}")
                feedback_parts.append(f"  Got: {failure.get('actual', 'ERROR')}")
            
            feedback_parts.append("\n**FIX RECOMMENDATIONS:**")
            feedback_parts.append("- Review the function logic carefully")
            feedback_parts.append("- Check if all edge cases are handled")
            feedback_parts.append("- Verify the return value matches expected format")
            feedback_parts.append("- Test with the failing inputs manually")
        
        return "\n".join(feedback_parts)
    
    def get_stats(self) -> dict:
        """Get debugger statistics"""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
