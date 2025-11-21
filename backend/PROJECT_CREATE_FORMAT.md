# Project Creation API Format

## Endpoint
```
POST /projects/create
```

## Required Request Body Format

```json
{
  "name": "Project Name",
  "client_name": "Client Name",
  "industry": "Healthcare",
  "region": "North America",
  "project_type": "new",
  "description": "Optional description"
}
```

## Field Requirements

### Required Fields

1. **name** (string)
   - Project name
   - Example: "Healthcare RFP Analysis"

2. **client_name** (string)
   - Name of the client
   - Example: "ABC Healthcare Corp"

3. **industry** (string)
   - Industry sector
   - Example: "Healthcare", "Finance", "Technology"

4. **region** (string)
   - Geographic region
   - Example: "North America", "Europe", "Asia Pacific"

5. **project_type** (string, enum)
   - Must be one of: `"new"`, `"expansion"`, `"renewal"`
   - Example: `"new"`

### Optional Fields

6. **description** (string, optional)
   - Project description
   - Can be omitted or set to `null`

## Example Requests

### Minimal Request
```json
{
  "name": "Q1 Healthcare RFP",
  "client_name": "MedCorp",
  "industry": "Healthcare",
  "region": "North America",
  "project_type": "new"
}
```

### Full Request
```json
{
  "name": "Q1 Healthcare RFP",
  "client_name": "MedCorp",
  "industry": "Healthcare",
  "region": "North America",
  "project_type": "new",
  "description": "Analysis of healthcare RFP for patient management system"
}
```

## Common Validation Errors

### Missing Required Field
```json
{
  "detail": "Validation error",
  "errors": [
    {
      "field": "name",
      "message": "Field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Invalid project_type
```json
{
  "detail": "Validation error",
  "errors": [
    {
      "field": "project_type",
      "message": "Input should be 'new', 'expansion' or 'renewal'",
      "type": "enum"
    }
  ]
}
```

### Wrong Field Name
```json
{
  "detail": "Validation error",
  "errors": [
    {
      "field": "clientName",
      "message": "Extra inputs are not permitted",
      "type": "extra_forbidden"
    }
  ]
}
```

**Note:** Use `client_name` (snake_case), not `clientName` (camelCase)

## Response

### Success (201 Created)
```json
{
  "id": 1,
  "name": "Q1 Healthcare RFP",
  "client_name": "MedCorp",
  "industry": "Healthcare",
  "region": "North America",
  "project_type": "new",
  "description": "Analysis of healthcare RFP...",
  "status": "draft",
  "owner_id": 1,
  "created_at": "2025-11-15T12:00:00",
  "updated_at": "2025-11-15T12:00:00"
}
```

### Validation Error (422)
```json
{
  "detail": "Validation error",
  "errors": [
    {
      "field": "name",
      "message": "Field required",
      "type": "value_error.missing"
    }
  ],
  "message": "Request validation failed. Check the 'errors' field for details."
}
```

## Frontend Integration

### JavaScript/TypeScript Example
```typescript
const createProject = async (projectData: {
  name: string;
  client_name: string;
  industry: string;
  region: string;
  project_type: "new" | "expansion" | "renewal";
  description?: string;
}) => {
  const response = await fetch("http://localhost:8000/projects/create", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify(projectData)
  });
  
  if (!response.ok) {
    const error = await response.json();
    console.error("Validation errors:", error.errors);
    throw new Error(error.message);
  }
  
  return await response.json();
};
```

## Troubleshooting

1. **Check field names**: Use snake_case (`client_name`, not `clientName`)
2. **Check project_type**: Must be exactly `"new"`, `"expansion"`, or `"renewal"`
3. **Check Content-Type**: Must be `application/json`
4. **Check authentication**: Must include valid Bearer token
5. **Check required fields**: All 5 required fields must be present

