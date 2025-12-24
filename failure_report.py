from groq import Groq
from typing import List, Dict
import json
import re
import ast
import importlib.util


class FailureReportGenerator:
    """Generates detailed debugging reports for users"""
    
    def check_module_availability(self, module_name: str) -> Dict:
        """Check if a module is available in environment"""
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                return {"available": True, "message": f"✓ Module '{module_name}' is installed"}
            else:
                return {
                    "available": False, 
                    "message": f"✗ Module '{module_name}' is NOT installed", 
                    "install_cmd": f"pip install {module_name}"
                }
        except Exception:
            return {"available": False, "message": f"✗ Could not check module '{module_name}'"}
    
    def extract_imports_from_code(self, code: str) -> List[str]:
        """Extract all imported modules from code"""
        imports = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split('.')[0])
        except:
            pass
        return imports
    
    def extract_missing_modules(self, error_msg: str, test_results: List[Dict], code: str = "") -> List[str]:
        """Extract missing module names from errors and code"""
        missing = set()
        
        # IMPROVED: Multiple error patterns
        patterns = [
            r"name '(\w+)' is not defined",
            r"No module named '(\w+)'",
            r"ModuleNotFoundError: No module named '(\w+)'",
            r"ImportError: cannot import name '(\w+)' from '(\w+)'",
        ]
        
        # Check main error message
        for pattern in patterns:
            matches = re.findall(pattern, error_msg)
            if isinstance(matches[0], tuple) if matches else False:
                # For patterns with multiple groups, take all groups
                for match in matches:
                    missing.update(match)
            else:
                missing.update(matches)
        
        # Check test results
        for result in test_results:
            if result['status'] == 'ERROR':
                actual = str(result.get('actual', ''))
                for pattern in patterns:
                    matches = re.findall(pattern, actual)
                    if isinstance(matches[0], tuple) if matches else False:
                        for match in matches:
                            missing.update(match)
                    else:
                        missing.update(matches)
        
        # ADDED: Check imports in code
        if code:
            code_imports = self.extract_imports_from_code(code)
            for module in code_imports:
                # Only add if not available
                if not self.check_module_availability(module)['available']:
                    missing.add(module)
        
        return list(missing)
    
    def generate_report(self, result: Dict) -> str:
        """Generate comprehensive failure report"""
        report = []
        report.append("\n" + "="*70)
        report.append("📋 DEBUGGING REPORT FOR USER")
        report.append("="*70)
        
        report.append(f"\n🔄 Attempts Made: {result['attempts']}/{result.get('max_attempts', 3)}")
        report.append(f"❌ Final Status: FAILED")
        report.append(f"💬 Error: {result.get('error', 'Unknown error')}\n")
        
        # Check for missing modules
        missing_modules = self.extract_missing_modules(
            result.get('error', ''),
            result.get('test_results', []),
            result.get('code', '')  # ADDED: Pass code for import checking
        )
        
        if missing_modules:
            report.append("="*70)
            report.append("🔍 ISSUE DETECTED: Missing Python Modules")
            report.append("="*70)
            report.append("The generated code requires modules that may not be installed:\n")
            
            for module in missing_modules:
                availability = self.check_module_availability(module)
                report.append(f"📦 Module: {module}")
                report.append(f"   {availability['message']}")
                if not availability['available'] and 'install_cmd' in availability:
                    report.append(f"   💡 Fix: {availability['install_cmd']}")
                report.append("")
        
        # Test results summary
        report.append("="*70)
        report.append("📊 TEST RESULTS SUMMARY")
        report.append("="*70)
        
        test_results = result.get('test_results', [])
        if test_results:
            passed = len([t for t in test_results if t['status'] == 'PASS'])
            failed = len([t for t in test_results if t['status'] == 'FAIL'])
            errors = len([t for t in test_results if t['status'] == 'ERROR'])
            
            report.append(f"✓ Passed: {passed}/{len(test_results)}")
            report.append(f"✗ Failed: {failed}/{len(test_results)}")
            report.append(f"⚠️  Errors: {errors}/{len(test_results)}\n")
            
            # Show failed/error tests (FIXED: Actually limit to 5)
            failures = [t for t in test_results if t['status'] != 'PASS']
            if failures:
                report.append("Failed/Error Test Details:")
                report.append("-" * 70)
                for t in failures[:5]:  # FIXED: Actually limit to 5
                    report.append(f"\n❌ Test {t['test_num']}: {t.get('description', 'N/A')}")
                    report.append(f"   Input: {t['input']}")
                    report.append(f"   Expected: {t['expected']}")
                    report.append(f"   Got: {t.get('actual', 'ERROR')}")
                
                # ADDED: Show count if more failures
                if len(failures) > 5:
                    report.append(f"\n... and {len(failures)-5} more failures")
        
        # Last generated code
        report.append("\n" + "="*70)
        report.append("📝 LAST GENERATED CODE")
        report.append("="*70)
        
        # IMPROVED: Truncate long code
        code = result.get('code', 'No code generated')
        if len(code) > 1500:
            code = code[:1500] + "\n\n... (truncated, showing first 1500 chars)"
        
        report.append("```")
        report.append(code)
        report.append("```")
        
        # Recommendations (FIXED: Proper numbering)
        report.append("\n" + "="*70)
        report.append("💡 WHAT YOU CAN DO")
        report.append("="*70)
        
        recommendations = []
        rec_num = 1
        
        if missing_modules:
            recommendations.append(f"{rec_num}. Install missing modules:")
            rec_num += 1
            for module in missing_modules:
                availability = self.check_module_availability(module)
                if not availability['available']:
                    recommendations.append(f"   pip install {module}")
        
        recommendations.append(f"{rec_num}. Review the debugger analysis in iteration logs above")
        rec_num += 1
        recommendations.append(f"{rec_num}. Manually fix the code based on test failures")
        rec_num += 1
        recommendations.append(f"{rec_num}. Check if your Python environment has required dependencies")
        rec_num += 1
        recommendations.append(f"{rec_num}. Try a simpler version of the problem first")
        
        report.extend(recommendations)
        report.append("\n" + "="*70)
        
        return '\n'.join(report)
