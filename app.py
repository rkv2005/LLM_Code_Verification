"""
Streamlit App: Dual-LLM Code Verification System
Self-verifying code generation with automated testing and debugging
"""

import streamlit as st
from system import DualLLMCodeVerificationSystem
import time
from typing import Dict

# Page configuration
st.set_page_config(
    page_title="Dual-LLM Code Verifier",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'system' not in st.session_state:
        st.session_state.system = None
    if 'result' not in st.session_state:
        st.session_state.result = None
    if 'running' not in st.session_state:
        st.session_state.running = False


def display_iteration(iteration_data: Dict, iteration_num: int):
    """Display details of a single iteration"""
    
    with st.expander(f"🔄 Iteration {iteration_num}/{st.session_state.result['attempts']}", 
                     expanded=(iteration_num == st.session_state.result['attempts'])):
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### 📝 Generated Code")
            st.code(iteration_data['code'], language='python')
        
        with col2:
            # Test results summary
            test_results = iteration_data['test_results']
            passed = len([t for t in test_results if t['status'] == 'PASS'])
            failed = len([t for t in test_results if t['status'] == 'FAIL'])
            errors = len([t for t in test_results if t['status'] == 'ERROR'])
            
            st.markdown("#### 📊 Test Results")
            st.metric("Passed", f"{passed}/{len(test_results)}", 
                     delta=None if iteration_data['passed'] else f"-{failed + errors}")
            
            if iteration_data['passed']:
                st.success("✅ All tests passed!")
            else:
                st.error(f"❌ {failed + errors} test(s) failed")
        
        # Detailed test results
        if not iteration_data['passed']:
            st.markdown("#### ❌ Failed Tests")
            failed_tests = [t for t in test_results if t['status'] != 'PASS']
            
            for test in failed_tests[:3]:  # Show first 3 failed tests
                with st.container():
                    st.markdown(f"""
                    <div class="error-box">
                        <strong>Test {test['test_num']}</strong>: {test.get('description', 'N/A')}<br>
                        <strong>Input:</strong> {test['input']}<br>
                        <strong>Expected:</strong> {test['expected']}<br>
                        <strong>Got:</strong> {test.get('actual', 'ERROR')}
                    </div>
                    """, unsafe_allow_html=True)
                    st.write("")
            
            if len(failed_tests) > 3:
                st.info(f"... and {len(failed_tests) - 3} more failed tests")


def main():
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">🤖 Dual-LLM Code Verification System</div>', 
                unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-powered code generation with automated testing & debugging</div>', 
                unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        api_key = st.text_input(
            "Groq API Key", 
            type="password",
            value=st.session_state.get('api_key', ''),
            help="Enter your Groq API key"
        )
        
        if api_key:
            st.session_state.api_key = api_key
        
        num_tests = st.slider(
            "Number of Test Cases",
            min_value=3,
            max_value=15,
            value=8,
            help="More tests = better coverage but slower"
        )
        
        max_attempts = st.slider(
            "Maximum Attempts",
            min_value=1,
            max_value=10,
            value=3,
            help="Number of debugging iterations"
        )
        
        st.divider()
        
        # Example problems
        st.subheader("📚 Example Problems")
        
        example_problems = {
            "Palindrome Checker": """Write a function 'is_palindrome(s)' that checks if a string is a palindrome.
- Ignore spaces, punctuation, and case
- Empty string returns True
- Handle None input (return False)
- s: string input
- Returns: boolean""",
            
            "Binary Search": """Write a function 'binary_search(arr, target)' that performs binary search.
- arr: sorted list of integers
- target: integer to find
- Returns: index of target in arr, or -1 if not found
- Handle empty arrays and None inputs""",
            
            "Fibonacci": """Write a function 'fibonacci(n)' that returns the nth Fibonacci number.
- n: non-negative integer (0-indexed)
- Returns: nth Fibonacci number
- Handle n=0 (return 0) and n=1 (return 1)
- Handle negative inputs (return None)
- Use iterative approach for efficiency""",
            
            "Two Sum": """Write a function 'two_sum(nums, target)' that finds two numbers that add up to target.
- nums: list of integers
- target: integer sum to find
- Returns: list of two indices [i, j] where nums[i] + nums[j] = target
- Return empty list if no solution exists
- Assume exactly one solution exists (except edge cases)"""
        }
        
        selected_example = st.selectbox(
            "Select Example",
            ["Custom Problem"] + list(example_problems.keys())
        )
        
        if st.button("Load Example", use_container_width=True):
            if selected_example != "Custom Problem":
                st.session_state.example_problem = example_problems[selected_example]
                st.rerun()
        
        st.divider()
        
        # System info
        st.subheader("ℹ️ System Info")
        st.info("""
        **Models Used:**
        - Generator: llama-3.1-8b-instant
        - Test Gen: llama-3.3-70b-versatile
        - Debugger: llama-3.3-70b-versatile
        
        **Features:**
        - Automated test generation
        - Iterative debugging
        - Auto-import detection
        - Comprehensive reports
        """)
    
    # Main content area
    st.markdown("---")
    
    # Problem input
    st.subheader("📋 Problem Description")
    
    default_problem = st.session_state.get('example_problem', '')
    
    problem = st.text_area(
        "Describe the coding problem you want to solve:",
        height=200,
        value=default_problem,
        placeholder="""Example:
Write a function 'add(a, b)' that returns the sum of two numbers.
- Handle integer and float inputs
- Return None if inputs are not numbers
"""
    )
    
    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        generate_button = st.button(
            "🚀 Generate & Verify Code",
            use_container_width=True,
            disabled=not (api_key and problem),
            type="primary"
        )
    
    if not api_key:
        st.warning("⚠️ Please enter your Groq API key in the sidebar")
    elif not problem:
        st.info("💡 Enter a problem description above to get started")
    
    # Run generation
    if generate_button and api_key and problem:
        st.session_state.running = True
        
        # Initialize system
        if st.session_state.system is None or st.session_state.system.api_key != api_key:
            with st.spinner("Initializing AI agents..."):
                st.session_state.system = DualLLMCodeVerificationSystem(api_key=api_key)
                st.session_state.system.max_attempts = max_attempts
        else:
            st.session_state.system.max_attempts = max_attempts
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Generate code with real-time updates
        status_text.text("🧪 Generating test cases...")
        progress_bar.progress(10)
        
        try:
            # Capture the generation process
            result = st.session_state.system.generate_verified_code(problem, num_tests=num_tests)
            st.session_state.result = result
            
            progress_bar.progress(100)
            status_text.text("✅ Complete!")
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.session_state.running = False
            return
        
        st.session_state.running = False
    
    # Display results
    if st.session_state.result is not None:
        result = st.session_state.result
        
        st.markdown("---")
        st.header("📊 Results")
        
        # Success/Failure banner
        if result['success']:
            st.markdown(f"""
            <div class="success-box">
                <h2>🎉 Success!</h2>
                <p>Code verified successfully in <strong>{result['attempts']}</strong> attempt(s)</p>
                <p>All <strong>{len(result['test_cases'])}</strong> test cases passed ✓</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            passed_count = len([t for t in result['test_results'] if t['status'] == 'PASS'])
            st.markdown(f"""
            <div class="error-box">
                <h2>❌ Verification Failed</h2>
                <p>Maximum attempts ({result['attempts']}) reached</p>
                <p><strong>{passed_count}/{len(result['test_cases'])}</strong> test cases passed</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{result['attempts']}</h3>
                <p>Iterations</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            passed = len([t for t in result.get('test_results', []) if t['status'] == 'PASS'])
            st.markdown(f"""
            <div class="metric-card">
                <h3>{passed}/{len(result.get('test_cases', []))}</h3>
                <p>Tests Passed</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            success_rate = (passed / len(result.get('test_cases', [])) * 100) if result.get('test_cases') else 0
            st.markdown(f"""
            <div class="metric-card">
                <h3>{success_rate:.0f}%</h3>
                <p>Success Rate</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            code_length = len(result.get('code', ''))
            st.markdown(f"""
            <div class="metric-card">
                <h3>{code_length}</h3>
                <p>Code Length</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        st.write("")
        
        # Final code
        if result['success']:
            st.subheader("✅ Verified Code")
            st.code(result['code'], language='python')
            
            # Download button
            st.download_button(
                label="📥 Download Code",
                data=result['code'],
                file_name="verified_code.py",
                mime="text/plain",
                use_container_width=True
            )
        
        st.write("")
        
        # Iteration history
        st.subheader("📜 Generation History")
        
        for i, iteration in enumerate(result['history'], 1):
            display_iteration(iteration, i)
        
        st.write("")
        
        # Test cases details
        with st.expander("🧪 View All Test Cases", expanded=False):
            st.markdown("#### Generated Test Cases")
            
            for i, tc in enumerate(result.get('test_cases', []), 1):
                st.markdown(f"""
                **Test {i}** ({tc.get('category', 'general')})  
                *{tc.get('description', 'N/A')}*  
                - Input: `{tc['input']}`  
                - Expected: `{tc['expected']}`
                """)
        
        # Debug report for failures
        if not result['success'] and 'debug_report' in result:
            with st.expander("🐛 Debugging Report", expanded=False):
                st.text(result['debug_report'])
        
        st.write("")
        st.write("")
        
        # Reset button
        if st.button("🔄 Start New Problem", use_container_width=True):
            st.session_state.result = None
            st.session_state.example_problem = ''
            st.rerun()


if __name__ == "__main__":
    main()
