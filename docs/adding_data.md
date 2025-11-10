You are helping a user create a custom Python script to import their data into Weaviate. Follow these steps exactly and **DO NOT modify any code except where explicitly marked with `# LLM TODO:`**.

## Step 1: Gather Requirements and Setup Environment

Ask the user to provide the following information AND complete the environment setup:

### Part A: Requirements

1. **Embedding Model Provider**: What embedding model provider would you like to use?
    - Available options: [https://docs.weaviate.io/weaviate/model-providers](https://docs.weaviate.io/weaviate/model-providers)
    - If unsure, recommend `text2vec-weaviate` (built-in, no API key required)
2. **Data Location**: Where is your data located?
    - Local file path (e.g., `/path/to/data.json`)
    - URL endpoint
    - Other source
3. **Data Schema**: Please provide an example object from your data. This will be used to define the property schema.
    - Example: `{"title": "Sample Title", "content": "Sample content text", "category": "example"}`

### Part B: Environment Setup

Please also complete this setup:

**Create Environment File**
Create a `.env` file in your project directory with these variables:

```
WEAVIATE_URL=
WEAVIATE_API_KEY=
EMBEDDINGS_PROVIDER_API_KEY=

```

**Setup Instructions:**

- Sign up for a free Weaviate Cloud account: [https://console.weaviate.cloud/](https://console.weaviate.cloud/)
- Create a free Sandbox cluster
- Copy your cluster URL and API key to the `.env` file
- If using `text2vec-weaviate`, leave `EMBEDDINGS_PROVIDER_API_KEY` empty
- If using another provider, add your API key for that provider

**WAIT for the user's response to Part A and confirmation that they have completed Part B before proceeding to Step 2.**

## Step 2: Virtual Environment Setup

Check if the user has a virtual environment. If not, instruct them to create one:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate

```

## Step 3: Install Dependencies

Install required packages:

```bash
pip install -U weaviate-client python-dotenv

```

## Step 4: Generate Custom Import Script

Create a file called `import_data.py` with the following code. **CRITICAL: Only modify sections marked with `# LLM TODO:`**

```python
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType, Tokenization
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

weaviate_url = os.environ["WEAVIATE_URL"]
weaviate_api_key = os.environ["WEAVIATE_API_KEY"]
embeddings_provider_api_key = os.environ.get("EMBEDDINGS_PROVIDER_API_KEY", "")

# Connect to Weaviate Cloud
if embeddings_provider_api_key:
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
        headers={"X-xx-Api-Key": embeddings_provider_api_key}  # LLM TODO: Replace 'xx' with correct provider header name (e.g., "X-OpenAI-Api-Key", "X-Cohere-Api-Key")
    )
else:
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key)
    )

print(f"Weaviate client ready: {client.is_ready()}")  # Should print: True

# Create collection
collection = client.collections.create(
    name="YourCollectionName",  # LLM TODO: Replace with appropriate collection name based on user's data
    vector_config=[
        Configure.Vectors.text2vec_weaviate(  # LLM TODO: Replace with user's chosen provider (e.g., text2vec_openai, text2vec_cohere)
            name="default",
            source_properties=["property1", "property2"],  # LLM TODO: Set source properties for vectorization based on user's data schema
        ),
    ],
    properties=[
        # LLM TODO: Define properties based on user's example data
        # Example:
        # Property(name="title", data_type=DataType.TEXT),
        # Property(name="content", data_type=DataType.TEXT),
        # Property(name="category", data_type=DataType.TEXT, skip_vectorization=True),
    ]
)

# LLM TODO: Load data based on user's specified location
# For local JSON file:
# with open("FILE_PATH", "r") as f:
#     data = json.load(f)

# For URL endpoint (note make sure to pip install and import requests library:
# response = requests.get("YOUR_URL")
# data = response.json()

# For other formats, adjust accordingly

# Import data in batches
with collection.batch.fixed_size(batch_size=200) as batch:
    for i, item in enumerate(data):
        batch.add_object({
            # LLM TODO: Map user's data properties to collection schema
            # Example:
            # "title": item["title"],
            # "content": item["content"],
            # "category": item["category"],
        })

        if batch.number_errors > 10:
            print("Batch import stopped due to excessive errors.")
            break

        # Progress indicator
        if i % 100 == 0:
            print(f"Imported {i} objects...")

# Check for import errors
failed_objects = collection.batch.failed_objects
if failed_objects:
    print(f"Number of failed imports: {len(failed_objects)}")
    print(f"First failed object: {failed_objects[0]}")
else:
    print("All objects imported successfully!")

print(f"Total objects in collection: {collection.aggregate.over_all(total_count=True).total_count}")

client.close()


### LLM TODO Instructions Summary:

1. **Line with headers**: Replace 'xx' in header name with correct provider (only if not using text2vec-weaviate)
2. **Collection name**: Choose appropriate name based on user's data type
3. **Vector config**: Replace with user's chosen embedding provider
4. **Source properties**: Set which properties should be vectorized
5. **Properties schema**: Define all properties from user's example data
6. **Data loading**: Implement correct data loading method based on user's data location
7. **Object mapping**: Map user's data fields to the defined schema

## Step 5: Error Handling

If there are any errors during execution:

1. First consult the Weaviate documentation: [https://docs.weaviate.io/weaviate/quickstart](https://docs.weaviate.io/weaviate/quickstart)
2. Check the specific error message and troubleshoot accordingly
3. Verify the `.env` file is properly configured
4. Ensure the data schema matches the actual data structure

## Step 6: Execute the Script

Run the import script:

```bash
python import_data.py

```

Upon successful completion, inform the user that their data has been imported to Weaviate and provide next steps for querying their data.

---

## Important Reminders:

- **Only modify code sections marked with `# LLM TODO:`**
- **Wait for user responses at Steps 1 and 2**
- **If using `text2vec-weaviate`, no external API key is needed**
- **Preserve all existing code structure and imports**