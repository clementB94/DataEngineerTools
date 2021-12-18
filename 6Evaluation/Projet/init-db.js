db = db.getSiblingDB("sku_db");
db.sku_tb.drop()

db.sku_tb.insertMany([
    {
        "id": 1,
        "name": "skurt"
    },
    {
        "id": 2,
        "name": "skaska"
    }
])