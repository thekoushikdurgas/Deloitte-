import os
import json
import re

class JSONTOPLJSON:
    def __init__(self, json_data):
        self.json_data = json_data
        self.sql_content = ""
        self.to_sql()
    
    def to_sql(self):
        pass


def read_json_to_oracle_triggers() -> None:
    # Define directories
    json_dir = "files/format_json"
    sql_out_dir = "files/format_pl_json"

    # Ensure directories exist
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
    if not os.path.exists(sql_out_dir):
        os.makedirs(sql_out_dir)

    # Process each analysis JSON file
    json_files = [f for f in os.listdir(json_dir) if f.endswith("_analysis.json")]

    for json_file in json_files:
        match = re.search(r"trigger(\d+)_analysis\.json$", json_file)
        if not match:
            # Skip non-trigger analysis files
            continue
        trigger_num = match.group(1)
        json_path = os.path.join(json_dir, json_file)
        with open(json_path, "r", encoding="utf-8") as f:
            analysis = json.load(f)

        analyzer = JSONTOPLJSON(analysis)
        sql_content = analyzer.to_sql()

        out_filename = f"trigger{trigger_num}.sql"
        out_path = os.path.join(sql_out_dir, out_filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(sql_content)
        print(f"Created {out_filename}")


if __name__ == "__main__":
    read_json_to_oracle_triggers()
    print("SQL formatting complete!")
