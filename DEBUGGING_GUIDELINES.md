
# Debugging Guidelines

## Methodical Approach to Fixing Issues

1. **Identify the root cause**
   - Carefully read error messages and stack traces
   - Identify the primary issue before attempting fixes
   - Look for syntax errors, which often cause cascading failures

2. **Plan your changes**
   - Document what needs to be changed and why
   - Consider potential ripple effects of any changes
   - Plan verification steps before implementing

3. **Test in isolation**
   - Create validation scripts to test specific components
   - Verify syntax and basic functionality before full testing
   - Use small test cases that target the specific issue

4. **Implement changes incrementally**
   - Make one change at a time
   - Verify each change before moving to the next
   - Avoid making multiple unrelated changes simultaneously

5. **Document what was fixed**
   - Note the root cause and solution
   - Document any patterns that might cause similar issues
   - Update code with clear comments where appropriate

## Common Issues

### String Literals
- Ensure all string literals are properly terminated
- Check for balanced quotes and triple-quotes
- Be careful with f-strings that contain multiple lines

### Indentation
- Python is sensitive to indentation
- Verify consistent indentation after code changes
- Use syntax validation tools to catch indentation errors

### Asynchronous Code
- Ensure `await` is used with all coroutines
- Check that methods expected to be awaited are defined as `async`
- Be careful with embedding async calls in synchronous contexts
