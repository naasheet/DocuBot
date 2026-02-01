import sys
import time
import requests
from qdrant_client import QdrantClient
from qdrant_client import models

def wait_for_qdrant(url: str, timeout: int = 30) -> bool:
    """Wait for Qdrant service to be healthy."""
    print(f"⏳ Waiting for Qdrant at {url}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/healthz")
            if response.status_code == 200:
                print("✅ Qdrant is healthy")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    return False

def main():
    # Determine Qdrant URL based on environment
    # Inside Docker network, the service name is 'qdrant'
    # From host machine, it is 'localhost'
    try:
        # Try internal docker DNS name first
        requests.get("http://qdrant:6333/healthz", timeout=1)
        base_url = "http://qdrant:6333"
    except requests.exceptions.RequestException:
        try:
            # Try container name as fallback
            requests.get("http://docubot-qdrant:6333/healthz", timeout=1)
            base_url = "http://docubot-qdrant:6333"
        except requests.exceptions.RequestException:
            base_url = "http://localhost:6333"

    collection_name = "test_collection"
    
    if not wait_for_qdrant(base_url):
        print(f"❌ Could not connect to Qdrant at {base_url}")
        sys.exit(1)

    client = QdrantClient(url=base_url)

    try:
        # 1. Check existing and cleanup
        collections = client.get_collections()
        exists = any(c.name == collection_name for c in collections.collections)
        
        if exists:
            print(f"🗑️  Deleting existing collection '{collection_name}'...")
            client.delete_collection(collection_name=collection_name)

        # 2. Create Collection
        print(f"✨ Creating collection '{collection_name}'...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=4, distance=models.Distance.DOT),
        )

        # 3. Verify
        collections = client.get_collections()
        created = any(c.name == collection_name for c in collections.collections)
        
        if created:
            print(f"✅ Collection '{collection_name}' created successfully!")
            try:
                info = client.get_collection(collection_name=collection_name)
                print(f"   Status: {info.status}")
                print(f"   Vectors Count: {info.vectors_count}")
            except Exception:
                print("   ⚠️  Detailed info skipped due to version mismatch (collection exists)")

            print(f"   View in Dashboard: {base_url}/dashboard")
            if "localhost" not in base_url:
                print(f"   (From host machine: http://localhost:6333/dashboard)")
        else:
            print(f"❌ Failed to verify collection creation")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()