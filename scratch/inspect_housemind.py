import zipfile, json

with zipfile.ZipFile('data_test.zip', 'r') as z:
    for task_name in ['generation', 'editing', 'understanding']:
        fname = f'data_test/{task_name}.jsonl'
        with z.open(fname) as f:
            lines = [json.loads(line.decode('utf-8')) for line in f]
            print(f'*** {task_name}.jsonl: total samples = {len(lines)}')
            sample = lines[0]
            inp = sample['input'][:180].encode('ascii', 'replace').decode('ascii')
            print(f'Sample input: {inp}...')
            out_str = str(sample['output'])[:250].encode('ascii', 'replace').decode('ascii')
            print(f'Sample output: {out_str}...')
            try:
                parsed_out = json.loads(sample['output'])
                if isinstance(parsed_out, dict):
                    print(f'Parsed output keys: {list(parsed_out.keys())}')
                else:
                    print(f'Parsed output type: {type(parsed_out)}, length: {len(parsed_out)}')
            except Exception as e:
                print(f'Output not JSON: {e}')
            print()
