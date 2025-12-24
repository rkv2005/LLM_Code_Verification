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

## Components

**DualLLMCodeVerificationSystem (`system.py`)**  
This is the main orchestrator that ties all agents together. It accepts a problem description and a desired number of tests, then runs the full loop: generate tests → generate code → verify → debug → retry (up to `max_attempts`). It returns the final verified code, detailed test results, an iteration history, and, if it ultimately fails, a comprehensive debugging report for the user.

**TestCaseGenerator (`test_generator.py`)**  
This is an LLM-based agent that reads the problem description and generates a structured list of test cases. It produces diverse tests including happy path cases, edge cases (empty input, `None`, single element), boundary conditions, invalid inputs, and special scenarios. Each test case includes `input`, `expected`, `category`, and a human-readable `description`.

**GeneratorAgent (`generator.py`)**  
This LLM-based code writer turns the problem statement (plus optional debugger feedback) into Python code. It prompts the model to output only imports plus a function definition, without extra prose. The agent then cleans markdown backticks and strips out any example or test harness code from the model’s reply. It also automatically injects missing imports by scanning for known module usages (such as `re.`, `math.`, `json.`, etc.) and uses a robust response parser so it works across different Groq SDK response shapes.

**CodeVerifier (`verifier.py`)**  
This is a pure-Python verifier that does not use an LLM. It parses the generated code with `ast` to check syntax, then executes it in a controlled namespace and locates the target function. It runs all generated test cases, capturing PASS/FAIL/ERROR status along with actual outputs or exception messages. The verifier returns a boolean `passed`, the list of `test_results`, and an overall `error_msg` summarizing the failures.

**DebuggerAgent (`debugger.py`)**  
This LLM-based debugging specialist analyzes failing code. It takes the current code, the original problem description, all failing tests, the verifier’s error message, and the current iteration number. It produces structured feedback that includes root cause analysis, a list of specific bugs, concrete fix recommendations, and a discussion of edge cases that are not handled. This feedback is then fed back to the `GeneratorAgent` to produce an improved version of the function in the next iteration.

**FailureReportGenerator (`failure_report.py`)**  
This is a human-facing reporting utility. It builds a text report when `max_attempts` is reached without success. The report summarizes the number of attempts, the last error, and test statistics. It highlights possible missing modules and suggests `pip install ...` commands, prints the last generated code (optionally truncated), and provides a concise list of recommended next steps for the user.

**CLI Test Harness (`main.py`)**  
This is a simple command-line interface to try the system before using the Streamlit app. It supports two modes:  
- Mode 1: run on predefined problems (e.g., Two Sum, Palindrome, Fibonacci, Add).  
- Mode 2: run on an arbitrary custom problem you type in.  
The CLI shows iteration logs, test results, final code, and can optionally save the verified code to a file.

**Streamlit App (`app.py`)**  
This is a web UI around the orchestrator. The sidebar lets you enter the Groq API key, choose the number of tests and maximum attempts, and either pick an example problem or enter a custom one. The main area shows progress (test generation, iterations, success/failure banner), displays metrics (attempts, tests passed, success rate, code length), and shows the final verified code with a download button when successful. It also shows iteration history (each iteration’s code and test summary), provides an expander with all generated test cases, and, on failure, displays the full debugging report inside an expander.

***

## How to Run It

### 1. Install Dependencies

Create a virtual environment (optional but recommended), then install dependencies:

```bash
pip install groq streamlit
```

If you use a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 2. Set Your Groq API Key

You can either export it in your shell:

```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

On Windows PowerShell:

```powershell
$env:GROQ_API_KEY="your_groq_api_key_here"
```

Or simply be ready to paste it when the CLI or app prompts you.

### 3. Run from the Command Line (CLI)

From the project root (where `main.py` and `system.py` live):

```bash
python main.py
```

You’ll see a menu like:

- `1` – Test with predefined problems (Two Sum, Palindrome, Fibonacci, Simple Add)  
- `2` – Test with a custom problem (you type your own prompt)  
- `3` – Quit  

Typical flow:

1. Choose `1`.  
2. Pick a problem (for example, `1` for Two Sum).  
3. The system prints each iteration, generated code, test results, and debugger analysis.  
4. If all tests pass, it prints the final code and optionally saves it to a file.

### 4. Run the Streamlit App

From the same project root:

```bash
streamlit run app.py
```

Then open the URL shown in the terminal (usually `http://localhost:8501`).

In the app:

- Enter your Groq API key in the sidebar.  
- Choose the number of test cases (for example, 8–10) and the maximum attempts.  
- Pick an example problem from the sidebar or type your own problem description in the main text area.  
- Click **“Generate & Verify Code”**.  
- Watch the iterations, inspect code and test results, and download the verified solution when it succeeds.  
- If it fails after all attempts, open the **Debugging Report** expander to see what went wrong and the suggested fixes.

***

!image[st_image_1.png]
!image[image_2.png]


