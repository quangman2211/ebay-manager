I need to merge my feature branch into the main branch safely. Please help me execute these steps:

1. First, check the current status and ensure all changes are committed in the feature branch:
   - Switch to feature branch: feature/tinh-nang-1
   - Check git status to confirm no uncommitted changes
   - If there are uncommitted changes, commit them first

2. Update the feature branch with the latest main:
   - Switch to main branch
   - Pull latest changes from origin main
   - Switch back to feature/tinh-nang-1
   - Merge main into the feature branch
   - Resolve any conflicts if they arise

3. Run tests to verify the feature still works after merging main:
   - Run the test suite
   - Verify the feature functionality

4. Merge the feature into main:
   - Switch to main branch
   - Merge feature/tinh-nang-1 into main
   - This should be a fast-forward merge if step 2 was done correctly

5. Push the updated main to remote:
   - Push main branch to origin

Please execute these git commands step by step, and pause if there are any conflicts that need manual resolution. Show me the output of each command.

The feature branch name is: feature/tinh-nang-1