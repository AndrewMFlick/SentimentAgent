# Quickstart: Admin Tool Management & Aliasing

## Prerequisites

- **Backend**: Python 3.13.3, FastAPI 0.109.2
- **Frontend**: TypeScript 5.3.3, React 18.2.0, TailwindCSS 3.4+
- **Database**: Azure Cosmos DB (SQL API)
- **Development**: VS Code with Python + TypeScript extensions

## Setup

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; import azure.cosmos; print('Dependencies OK')"
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Verify TailwindCSS is configured
npm run build -- --dry-run
```

### 3. Database Setup

#### Create Cosmos DB Containers

```python
# backend/scripts/create_tool_containers.py
from azure.cosmos import CosmosClient, PartitionKey
import os

client = CosmosClient(
    os.getenv("COSMOS_ENDPOINT"),
    os.getenv("COSMOS_KEY")
)

database = client.get_database_client("SentimentDB")

# Create Tools container
tools_container = database.create_container(
    id="Tools",
    partition_key=PartitionKey(path="/partitionKey"),
    indexing_policy={
        "includedPaths": [
            {"path": "/name/?"},
            {"path": "/category/?"},
            {"path": "/status/?"},
            {"path": "/slug/?"}
        ]
    }
)

# Create ToolAliases container
aliases_container = database.create_container(
    id="ToolAliases",
    partition_key=PartitionKey(path="/partitionKey"),
    indexing_policy={
        "includedPaths": [
            {"path": "/alias_tool_id/?"},
            {"path": "/primary_tool_id/?"}
        ]
    }
)

print("Containers created successfully!")
```

Run the script:

```bash
cd backend
python scripts/create_tool_containers.py
```

#### Seed Initial Data

```python
# backend/scripts/seed_tools.py
from azure.cosmos import CosmosClient
import os
import uuid
from datetime import datetime

client = CosmosClient(os.getenv("COSMOS_ENDPOINT"), os.getenv("COSMOS_KEY"))
database = client.get_database_client("SentimentDB")
tools_container = database.get_container_client("Tools")

seed_tools = [
    {
        "id": str(uuid.uuid4()),
        "partitionKey": "tool",
        "name": "GitHub Copilot",
        "slug": "github-copilot",
        "vendor": "GitHub",
        "category": "code-completion",
        "description": "AI pair programmer",
        "status": "active",
        "metadata": {},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "partitionKey": "tool",
        "name": "Jules AI",
        "slug": "jules-ai",
        "vendor": "Jules",
        "category": "code-completion",
        "description": "AI coding assistant",
        "status": "active",
        "metadata": {},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
]

for tool in seed_tools:
    tools_container.create_item(tool)
    print(f"Created tool: {tool['name']}")
```

Run the script:

```bash
cd backend
python scripts/seed_tools.py
```

## Development Workflow

### Backend Development

#### 1. Create ToolService

```bash
# Create new service file
touch backend/src/services/tool_service.py
```

```python
# backend/src/services/tool_service.py
from azure.cosmos import CosmosClient
import uuid
from datetime import datetime
from typing import List, Optional, Dict

class ToolService:
    def __init__(self, client: CosmosClient, database_name: str):
        self.database = client.get_database_client(database_name)
        self.tools_container = self.database.get_container_client("Tools")
        self.aliases_container = self.database.get_container_client("ToolAliases")
    
    async def create_tool(self, tool_data: Dict) -> Dict:
        """Create a new tool"""
        tool_id = str(uuid.uuid4())
        tool = {
            "id": tool_id,
            "partitionKey": "tool",
            "name": tool_data["name"],
            "slug": tool_data["name"].lower().replace(" ", "-"),
            "vendor": tool_data["vendor"],
            "category": tool_data["category"],
            "description": tool_data.get("description", ""),
            "status": "active",
            "metadata": tool_data.get("metadata", {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        self.tools_container.create_item(tool)
        return tool
    
    async def get_tool(self, tool_id: str) -> Optional[Dict]:
        """Get tool by ID"""
        query = "SELECT * FROM Tools t WHERE t.id = @id AND t.status = 'active'"
        items = list(self.tools_container.query_items(
            query=query,
            parameters=[{"name": "@id", "value": tool_id}],
            enable_cross_partition_query=True
        ))
        return items[0] if items else None
    
    async def list_tools(self, page: int = 1, limit: int = 20, search: str = "", category: str = None) -> List[Dict]:
        """List all tools with pagination"""
        offset = (page - 1) * limit
        query = "SELECT * FROM Tools t WHERE t.partitionKey = 'tool' AND t.status = 'active'"
        
        if search:
            query += f" AND CONTAINS(LOWER(t.name), LOWER('{search}'))"
        
        if category:
            query += f" AND t.category = '{category}'"
        
        query += f" ORDER BY t.name OFFSET {offset} LIMIT {limit}"
        
        return list(self.tools_container.query_items(query=query, enable_cross_partition_query=True))
    
    async def create_alias(self, alias_tool_id: str, primary_tool_id: str, created_by: str) -> Dict:
        """Link an alias to a primary tool"""
        # Validation: Check both tools exist
        alias_tool = await self.get_tool(alias_tool_id)
        primary_tool = await self.get_tool(primary_tool_id)
        
        if not alias_tool or not primary_tool:
            raise ValueError("Tool not found")
        
        if alias_tool_id == primary_tool_id:
            raise ValueError("Tool cannot be alias of itself")
        
        # Create alias relationship
        alias = {
            "id": str(uuid.uuid4()),
            "partitionKey": "alias",
            "alias_tool_id": alias_tool_id,
            "primary_tool_id": primary_tool_id,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": created_by
        }
        self.aliases_container.create_item(alias)
        return alias
    
    async def resolve_tool_id(self, tool_id: str) -> str:
        """Resolve tool ID to primary tool ID (follows aliases)"""
        query = "SELECT * FROM ToolAliases ta WHERE ta.alias_tool_id = @id"
        items = list(self.aliases_container.query_items(
            query=query,
            parameters=[{"name": "@id", "value": tool_id}],
            enable_cross_partition_query=True
        ))
        
        return items[0]["primary_tool_id"] if items else tool_id
```

#### 2. Create Admin Routes

```bash
# Create admin routes file
touch backend/src/api/admin_routes.py
```

```python
# backend/src/api/admin_routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from ..services.tool_service import ToolService

router = APIRouter(prefix="/api/admin", tags=["admin"])

class ToolCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    vendor: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., regex="^(code-completion|chat|analysis)$")
    description: Optional[str] = Field(default="", max_length=500)

class AliasLinkRequest(BaseModel):
    primary_tool_id: str = Field(..., regex="^[a-f0-9-]{36}$")

@router.post("/tools")
async def create_tool(tool: ToolCreateRequest, tool_service: ToolService = Depends()):
    try:
        result = await tool_service.create_tool(tool.dict())
        return {"id": result["id"], "message": "Tool created successfully"}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/tools")
async def list_tools(page: int = 1, limit: int = 20, search: str = "", category: str = None, tool_service: ToolService = Depends()):
    tools = await tool_service.list_tools(page, limit, search, category)
    return {"tools": tools}

@router.put("/tools/{tool_id}/alias")
async def link_alias(tool_id: str, link: AliasLinkRequest, tool_service: ToolService = Depends()):
    try:
        await tool_service.create_alias(tool_id, link.primary_tool_id, "admin-123")
        return {"message": "Alias linked successfully"}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
```

#### 3. Register Routes

```python
# backend/src/main.py
from .api.admin_routes import router as admin_router

app.include_router(admin_router)
```

### Frontend Development

#### 1. Create AdminToolManagement Component

```bash
# Create component file
touch frontend/src/components/AdminToolManagement.tsx
```

```tsx
// frontend/src/components/AdminToolManagement.tsx
import React, { useState } from 'react';
import { api } from '../services/api';

export function AdminToolManagement() {
  const [toolName, setToolName] = useState('');
  const [vendor, setVendor] = useState('');
  const [category, setCategory] = useState('code-completion');
  const [description, setDescription] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const response = await api.post('/admin/tools', {
        name: toolName,
        vendor,
        category,
        description
      });
      
      setMessage(`✓ ${response.data.message}`);
      // Reset form
      setToolName('');
      setVendor('');
      setDescription('');
    } catch (error) {
      setMessage(`✗ Failed to create tool: ${error.message}`);
    }
  };

  return (
    <div className="glass-card p-6">
      <h2 className="text-2xl font-bold text-gray-100 mb-6">Add New Tool</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-200 mb-2">Tool Name</label>
          <input 
            type="text" 
            className="glass-input w-full"
            placeholder="e.g., Cursor IDE"
            value={toolName}
            onChange={(e) => setToolName(e.target.value)}
            required
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-200 mb-2">Vendor</label>
          <input 
            type="text" 
            className="glass-input w-full"
            placeholder="e.g., Anysphere"
            value={vendor}
            onChange={(e) => setVendor(e.target.value)}
            required
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-200 mb-2">Category</label>
          <select 
            className="glass-input w-full"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="code-completion">Code Completion</option>
            <option value="chat">Chat Assistant</option>
            <option value="analysis">Code Analysis</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-200 mb-2">Description</label>
          <textarea 
            className="glass-input w-full h-24"
            placeholder="Brief description of the tool"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        
        <button 
          type="submit" 
          className="glass-button bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 px-6 py-2"
        >
          Add Tool
        </button>
        
        {message && (
          <div className={`p-3 rounded-lg ${message.startsWith('✓') ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
            {message}
          </div>
        )}
      </form>
    </div>
  );
}
```

#### 2. Add Component to Admin Page

```tsx
// frontend/src/components/AdminToolApproval.tsx
import { AdminToolManagement } from './AdminToolManagement';

// Inside the component:
<div className="space-y-6">
  <AdminToolManagement />
  {/* Existing approval table */}
</div>
```

## Testing

### Backend Tests

```bash
# Test tool creation
pytest backend/tests/test_tool_service.py -v

# Test admin routes
pytest backend/tests/test_admin_routes.py -v
```

### Frontend Tests

```bash
# Start dev server
cd frontend
npm run dev

# Manual testing:
# 1. Navigate to Admin page
# 2. Fill out "Add New Tool" form
# 3. Submit and verify success message
# 4. Check database for new tool record
```

### Integration Test

```bash
# Full workflow test
cd backend

# 1. Create tool via API
curl -X POST http://localhost:8000/api/admin/tools \
  -H "Content-Type: application/json" \
  -d '{"name": "Cursor IDE", "vendor": "Anysphere", "category": "code-completion", "description": "AI-first code editor"}'

# 2. List tools
curl http://localhost:8000/api/admin/tools

# 3. Link alias
curl -X PUT http://localhost:8000/api/admin/tools/<tool-id>/alias \
  -H "Content-Type: application/json" \
  -d '{"primary_tool_id": "<primary-id>"}'
```

## Common Issues

### Database Connection Failed

```bash
# Verify environment variables
echo $COSMOS_ENDPOINT
echo $COSMOS_KEY

# Test connection
python -c "from azure.cosmos import CosmosClient; client = CosmosClient('$COSMOS_ENDPOINT', '$COSMOS_KEY'); print('Connection OK')"
```

### Container Already Exists

```bash
# Delete existing containers (CAUTION: deletes data)
python -c "
from azure.cosmos import CosmosClient
import os
client = CosmosClient(os.getenv('COSMOS_ENDPOINT'), os.getenv('COSMOS_KEY'))
db = client.get_database_client('SentimentDB')
db.delete_container('Tools')
db.delete_container('ToolAliases')
"
```

### Frontend Build Fails

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Verify TailwindCSS config
cat tailwind.config.js
```

## Next Steps

1. **Add Authentication**: Protect `/api/admin/*` routes with JWT
2. **Add Alias Linking UI**: Modal component for linking aliases
3. **Add Tool Management Table**: View/edit/delete tools
4. **Add Validation**: Client-side + server-side validation
5. **Add Tests**: Unit tests for ToolService and admin routes

## Resources

- [Azure Cosmos DB Python SDK](https://docs.microsoft.com/azure/cosmos-db/sql/quickstart-python)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TailwindCSS Glass Morphism](https://tailwindcss.com/docs/backdrop-blur)
- [React Hook Form](https://react-hook-form.com/) (for advanced forms)
