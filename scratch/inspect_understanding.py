import zipfile, json

with zipfile.ZipFile('data_test.zip', 'r') as z:
    with z.open('data_test/understanding.jsonl') as f:
        first_line = json.loads(f.readline().decode('utf-8'))
        print("House ID:", first_line['house_id'])
        print("Input:", first_line['input'])
        out = json.loads(first_line['output'])
        print("\nRooms (first 3):")
        for r in out.get('rooms', [])[:3]:
            print(" ", r)
        print("\nEdges (first 5):")
        for e in out.get('edges', [])[:5]:
            print(" ", e)
        print("\nDescription:", out.get('description'))
