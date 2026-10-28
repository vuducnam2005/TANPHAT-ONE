import json

with open('excel_summary.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('summary_readable.txt', 'w', encoding='utf-8') as out:
    for fname, fcontent in data.items():
        out.write('=' * 60 + '\n')
        out.write(f'FILE: {fname}\n')
        out.write('=' * 60 + '\n')
        for sname, sinfo in fcontent['sheets'].items():
            out.write(f"\n--- SHEET: {sname} (Rows: {sinfo['max_row']}, Cols: {sinfo['max_column']}) ---\n")
            for idx, row in enumerate(sinfo['sample']):
                non_empty = [f'[c{i}]: {v}' for i, v in enumerate(row) if v is not None and str(v).strip() != '']
                if non_empty:
                    out.write(f"  Row {idx+1}: " + " | ".join(non_empty) + "\n")

print("summary_readable.txt generated successfully.")
