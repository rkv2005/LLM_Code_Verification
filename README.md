# 🤖 Dual-LLM Code Verification System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Groq](https://img.shields.io/badge/Groq-API-orange)](https://groq.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **AI-powered code generation with automated testing, verification, and self-debugging**

A sophisticated multi-agent system that combines Large Language Models (LLMs) to generate, test, verify, and iteratively debug Python code. Unlike traditional code generators, this system creates its own test cases and automatically fixes failures through intelligent feedback loops.

## 🎯 Overview

The Dual-LLM Code Verification System uses a **multi-agent architecture** where specialized AI agents collaborate to:
1. **Generate comprehensive test cases** based on problem descriptions
2. **Write Python code** to solve the problem
3. **Verify code correctness** through automated testing
4. **Debug failures** with detailed analysis
5. **Iteratively improve** code until all tests pass

### Why This Matters

Traditional code generation tools produce code that may:
- ❌ Fail on edge cases
- ❌ Have subtle logic errors
- ❌ Lack proper error handling
- ❌ Miss requirements

This system ensures:
- ✅ **Verified correctness** through automated testing
- ✅ **Edge case handling** with comprehensive test generation
- ✅ **Self-healing** via iterative debugging
- ✅ **Production-ready** code with proper validation

---

## 🏗️ Architecture

The system consists of **6 specialized agents** working in a coordinated pipeline:

DualLLMCodeVerificationSystem (system.py)
Orchestrator that ties all agents together.

Accepts a problem description and number of tests.

Runs the loop: generate tests → generate code → verify → debug → retry (up to max_attempts).

Returns the final code, test results, iteration history, and (if it fails) a detailed debugging report.

TestCaseGenerator (test_generator.py)
LLM-based agent that reads the problem description and generates a structured list of test cases.

Produces diverse tests: happy path, edge cases (empty, None, single element), boundary conditions, invalid inputs, and special cases.

Each test includes: input, expected, category, and description.

GeneratorAgent (generator.py)
LLM-based code writer that turns the problem (plus optional debugger feedback) into Python code.

Prompts the model to output only imports + function definition (no extra text).

Cleans markdown backticks and strips out example/test code from the model’s reply.

Automatically injects missing imports by scanning for known module usages (re., math., json., etc.).

Uses a robust response parser so it works across different Groq SDK response shapes.

CodeVerifier (verifier.py)
Pure-Python verifier that does not use an LLM.

Parses code with ast to check syntax.

Executes code in a controlled namespace and locates the target function.

Runs all generated test cases, capturing PASS/FAIL/ERROR status plus actual outputs or exceptions.

Returns a boolean passed, the list of test_results, and an overall error_msg summarizing failures.

DebuggerAgent (debugger.py)
LLM-based debugging specialist that analyzes failing code.

Takes: the code, the original problem, failing tests, the verifier’s error message, and the current iteration number.

Produces structured feedback with:

Root cause analysis

List of specific bugs

Concrete fix recommendations

Edge cases that are not handled

This feedback is then fed back to GeneratorAgent to produce an improved version of the function.

FailureReportGenerator (failure_report.py)
Human-facing reporting utility.

Builds a text report when max_attempts is reached without success.

Summarizes attempts, errors, and test statistics.

Highlights possible missing modules and suggests pip install ... commands.

Prints last generated code (optionally truncated) and a list of things the user can do next.

CLI Test Harness (main.py)
Simple command-line interface to try the system before using the Streamlit app.

Mode 1: run on predefined problems (e.g., Two Sum, Palindrome, Fibonacci, Add).

Mode 2: run on an arbitrary custom problem you type in.

Shows attempts, test results, final code, and optionally saves the verified code to a file.

Streamlit App (app.py)
Web UI around the orchestrator.

Sidebar: enter Groq API key, choose number of tests and max attempts, pick example problem or enter a custom one.

Main area:

Shows progress (generating tests, iterations, success/failure banner).

Displays metrics (attempts, tests passed, success rate, code length).

Shows final verified code with a download button if successful.

Shows iteration history: each iteration’s code and test summary.

Provides an expander with all generated test cases.

On failure, shows the full debugging report in an expander.

How to Run It
1. Install Dependencies
Create a virtual environment (optional but recommended), then install:

bash
pip install groq streamlit
If you use a requirements.txt:

bash
pip install -r requirements.txt
2. Set Your Groq API Key
Either export it in your shell:

bash
export GROQ_API_KEY="your_groq_api_key_here"
On Windows PowerShell:

powershell
$env:GROQ_API_KEY="your_groq_api_key_here"
Or just be ready to paste it when the CLI or app asks.

3. Run from the Command Line (CLI)
From the project root (where main.py and system.py live):

bash
python main.py
You’ll see a menu like:

1 – Test with predefined problems (Two Sum, Palindrome, Fibonacci, Simple Add)

2 – Test with a custom problem (you type your own prompt)

3 – Quit

Typical flow:

Choose 1.

Pick a problem (e.g., 1 for Two Sum).

The system prints each iteration, generated code, test results, and debugger analysis.

If all tests pass, it prints the final code and optionally saves it to a file.

4. Run the Streamlit App
From the same project root:

bash
streamlit run app.py
Then open the URL shown in the terminal (usually http://localhost:8501).

In the app:

Enter your Groq API key in the sidebar.

Choose the number of test cases (e.g., 8–10) and maximum attempts.

Pick an example problem from the sidebar or type your own problem description in the main text area.

Click “Generate & Verify Code”.

Watch iterations, inspect code and tests, and download the verified solution when it succeeds.

If it fails after all attempts, open the Debugging Report expander to see what went wrong and suggested fixes.
