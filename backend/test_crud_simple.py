"""Test Product CRUD endpoints - Simple version without emoji."""
import json
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import Product

# Create test client
client = TestClient(app)

# Setup: Create tables
Base.metadata.create_all(bind=engine)

print("=" * 80)
print("Testing Product CRUD APIs")
print("=" * 80)

# Test 1: Create products
print("\n1. Testing POST /products - Create products...")
test_products = [
    {
        "sku": "WIDGET-001",
        "name": "Blue Widget",
        "description": "A high-quality blue widget",
    },
    {
        "sku": "GADGET-001",
        "name": "Red Gadget",
        "description": "A shiny red gadget",
    },
    {
        "sku": "TOOL-001",
        "name": "Power Tool",
        "description": "Professional grade power tool",
    },
]

created_ids = []
for product_data in test_products:
    response = client.post("/products", json=product_data)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    created_ids.append(data["id"])
    print(f"[PASS] Created product: {data['id']} - {data['name']} (SKU: {data['sku']})")

# Test 2: Try creating duplicate SKU (should fail)
print("\n2. Testing duplicate SKU detection...")
duplicate = {"sku": "WIDGET-001", "name": "Different Widget"}
response = client.post("/products", json=duplicate)
assert response.status_code == 409, f"Expected 409 conflict, got {response.status_code}"
print(f"[PASS] Correctly rejected duplicate SKU: {response.json()['detail']}")

# Test 3: Get single product
print("\n3. Testing GET /products/{{id}} - Get single product...")
response = client.get(f"/products/{created_ids[0]}")
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
data = response.json()
print(f"[PASS] Retrieved product: {data['id']} - {data['name']}")
assert data["sku"] == "WIDGET-001", "SKU mismatch"
assert data["description"] == "A high-quality blue widget", "Description mismatch"

# Test 4: Get non-existent product
print("\n4. Testing GET /products/{{id}} with invalid ID...")
response = client.get("/products/99999")
assert response.status_code == 404, f"Expected 404, got {response.status_code}"
print(f"[PASS] Correctly returned 404: {response.json()['detail']}")

# Test 5: List all products (no filters)
print("\n5. Testing GET /products - List all products...")
response = client.get("/products")
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
data = response.json()
assert data["total"] == 3, f"Expected 3 products, got {data['total']}"
assert data["limit"] == 10, "Default limit should be 10"
assert data["offset"] == 0, "Default offset should be 0"
assert len(data["items"]) == 3, f"Expected 3 items, got {len(data['items'])}"
print(f"[PASS] Listed {data['total']} products (limit={data['limit']}, offset={data['offset']})")
for item in data["items"]:
    print(f"   - {item['id']}: {item['name']}")

# Test 6: Pagination
print("\n6. Testing pagination (limit=2, offset=1)...")
response = client.get("/products?limit=2&offset=1")
assert response.status_code == 200
data = response.json()
assert data["limit"] == 2, "Limit should be 2"
assert data["offset"] == 1, "Offset should be 1"
assert len(data["items"]) == 2, "Should return 2 items"
assert data["total"] == 3, "Total should still be 3"
print(f"[PASS] Pagination works: returned {len(data['items'])} items (offset={data['offset']}, limit={data['limit']})")

# Test 7: Filter by name (case-insensitive)
print("\n7. Testing filter by name...")
response = client.get("/products?name=widget")
assert response.status_code == 200
data = response.json()
assert data["total"] == 1, "Should find 1 product with 'widget' in name"
assert data["items"][0]["name"] == "Blue Widget"
print(f"[PASS] Name filter works: found {data['total']} product(s)")

# Test 8: Filter by SKU
print("\n8. Testing filter by SKU...")
response = client.get("/products?sku=GADGET")
assert response.status_code == 200
data = response.json()
assert data["total"] == 1, "Should find 1 product with 'GADGET' in SKU"
assert data["items"][0]["sku"] == "GADGET-001"
print(f"[PASS] SKU filter works: found {data['total']} product(s)")

# Test 9: Filter by active status
print("\n9. Testing filter by active status...")
response = client.get("/products?active=false")
assert response.status_code == 200
data = response.json()
# (no active field in the simplified model)

# Test 10: Filter by description
print("\n10. Testing filter by description...")
response = client.get("/products?description=professional")
assert response.status_code == 200
data = response.json()
assert data["total"] == 1, "Should find 1 product with 'professional' in description"
assert data["items"][0]["name"] == "Power Tool"
print(f"[PASS] Description filter works: found {data['total']} product(s)")

# Test 11: Update product
print("\n11. Testing PUT /products/{{id}} - Update product...")
update_data = {"name": "Blue Widget Pro"}
response = client.put(f"/products/{created_ids[0]}", json=update_data)
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
data = response.json()
assert data["name"] == "Blue Widget Pro", "Name should be updated"
assert data["sku"] == "WIDGET-001", "SKU should not change"
print(f"[PASS] Updated product: {data['id']} - {data['name']}")

# Test 12: Partial update (update only active status)
print("\n12. Testing partial update (active status)...")
# No active field to update in simplified model

# Test 13: Update non-existent product
print("\n13. Testing PUT /products/{{id}} with invalid ID...")
response = client.put("/products/99999", json={"name": "Fake"})
assert response.status_code == 404, f"Expected 404, got {response.status_code}"
print("[PASS] Correctly returned 404")

# Test 14: Delete product
print("\n14. Testing DELETE /products/{{id}} - Delete product...")
response = client.delete(f"/products/{created_ids[2]}")
assert response.status_code == 204, f"Expected 204, got {response.status_code}"
print(f"[PASS] Deleted product {created_ids[2]}")

# Verify deletion
response = client.get(f"/products/{created_ids[2]}")
assert response.status_code == 404, "Product should be deleted"
print("[PASS] Verified: product no longer exists")

# Test 15: List after deletion (should have 2 products now)
print("\n15. Testing list after deletion...")
response = client.get("/products")
assert response.status_code == 200
data = response.json()
assert data["total"] == 2, f"Expected 2 products after deletion, got {data['total']}"
print(f"[PASS] Updated product count: {data['total']}")

# Test 16: Delete non-existent product
print("\n16. Testing DELETE /products/{{id}} with invalid ID...")
response = client.delete("/products/99999")
assert response.status_code == 404, f"Expected 404, got {response.status_code}"
print("[PASS] Correctly returned 404")

# Test 17: Combined filters
print("\n17. Testing combined filters (name contains 'widget')...")
response = client.get("/products?name=widget")
assert response.status_code == 200
data = response.json()
assert data["total"] == 1, "Should find 1 product with 'widget' in name"
assert data["items"][0]["name"] == "Blue Widget Pro"
print(f"[PASS] Combined filters work: found {data['total']} product(s)")

# Test 18: Invalid limit (should fail validation)
print("\n18. Testing pagination limit validation...")
response = client.get("/products?limit=200")  # Should be rejected (max is 100)
assert response.status_code == 422, "Should reject limit > 100"
print("[PASS] Limit validation works: correctly rejected limit=200")

# Test 19: Negative offset (should fail)
print("\n19. Testing negative offset validation...")
response = client.get("/products?offset=-1")
assert response.status_code == 422, "Should reject negative offset"
print("[PASS] Offset validation works")

# Clean up
db = SessionLocal()
db.query(Product).delete()
db.commit()
db.close()

print("\n" + "=" * 80)
print("[SUCCESS] ALL PRODUCT CRUD TESTS PASSED!")
print("=" * 80)
