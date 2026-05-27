from core.parser import LocalSRSParser
import json

# Inisialisasi parser dengan PDF yang baru dijana
parser = LocalSRSParser("srs_test.pdf")

# Ekstrak teks mentah
raw_text = parser.extract_clean_text()

# Proses teks kepada JSON berstruktur
structured_json = parser.filter_and_structure(raw_text)

# Paparkan hasil output JSON yang super bersih!
print(json.dumps(structured_json, indent=2))
