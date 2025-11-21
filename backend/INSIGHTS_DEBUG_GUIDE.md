# Insights Generation Debug Guide

## Issue
Insights are not being generated when calling `/agents/run-all`. The endpoint returns 403 Forbidden.

## Root Causes

The 403 Forbidden error can occur due to several reasons:

### 1. Email Verification (Most Likely)
The `get_current_user` dependency requires users to have verified their email. If a user's `email_verified` field is `False`, they will get a 403 error.

**Solution:**
```bash
# Verify user email manually for development
cd backend
python scripts/verify_user_email.py <user_email>
```

Example:
```bash
python scripts/verify_user_email.py indrajit.ghosh@intglobal.com
```

### 2. Project Ownership
The project must belong to the authenticated user. Check that `project.owner_id == current_user.id`.

### 3. RFP Document Ownership
The RFP document must belong to the specified project. Check that `rfp_document.project_id == project_id`.

## Enhanced Logging

I've added comprehensive logging throughout the workflow execution path. When you run the workflow, you should see:

1. **Authentication logs** (in `dependencies.py`):
   - Warning if email is not verified
   
2. **Agent endpoint logs** (in `agents.py`):
   - Project ownership verification
   - RFP document verification
   - Workflow execution start/completion

3. **Workflow manager logs** (in `workflow_manager.py`):
   - RFP document retrieval
   - Text extraction
   - Workflow graph invocation
   - Insights saving process

## Debugging Steps

1. **Check if email is verified:**
   ```bash
   cd backend
   python scripts/verify_user_email.py <your_email>
   ```

2. **Check backend logs** when calling `/agents/run-all`:
   - Look for the `RUNNING AGENTS WORKFLOW` section
   - Check for any `❌` error messages
   - Verify ownership checks pass (✓ marks)

3. **Verify project and RFP document IDs:**
   - Ensure the `project_id` and `rfp_document_id` in the request match what was created
   - Check that the RFP document has `extracted_text` (required for workflow)

4. **Check workflow execution:**
   - Look for `WORKFLOW MANAGER: Starting workflow execution`
   - Check for any exceptions during workflow graph invocation
   - Verify insights are being saved (look for `💾 Saving insights to database...`)

## Expected Flow

1. User creates project → `POST /projects/create`
2. User uploads RFP → `POST /upload/rfp?project_id=X`
3. User builds index → `POST /rag/build-index` (extracts text from RFP)
4. User runs agents → `POST /agents/run-all` (generates insights)
5. User fetches insights → `GET /insights/get?project_id=X`

## Common Issues

### Issue: "RFP document has no extracted text"
**Solution:** Make sure to call `/rag/build-index` before `/agents/run-all`. The index building process extracts text from the RFP document.

### Issue: "Project not found" or "Access denied"
**Solution:** Verify that:
- The project exists in the database
- The project belongs to the authenticated user
- The user's email is verified

### Issue: Workflow completes but insights are not saved
**Solution:** Check the database logs for any errors during the `_save_insights` call. The logs will show detailed information about what's being saved.

## Testing the Fix

After verifying the user's email, try running the workflow again:

```bash
# In your frontend or using curl:
POST /agents/run-all
{
  "project_id": 5,
  "rfp_document_id": 5
}
```

You should see detailed logs in the backend console showing each step of the process.

