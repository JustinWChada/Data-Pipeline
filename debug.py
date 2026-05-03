from pipeline.p_1_ingestion import ingest_all_sources
from pipeline.p_2_cleaning import clean_all_sources
from pipeline.p_3_preprocessing import preprocess_all_sources

print("=== INGESTION ===")
all_data = ingest_all_sources()
for key, val in all_data.items():
    if 'metadata' not in key:
        print(f'{key}: {type(val).__name__}')
        if hasattr(val, 'columns'):
            print(f'  Columns: {list(val.columns)}')

print("\n=== CLEANING ===")
cleaned_data = clean_all_sources(all_data)
for key, val in cleaned_data.items():
    if 'metadata' not in key:
        print(f'{key}: {type(val).__name__}')
        if hasattr(val, 'columns'):
            print(f'  Columns: {list(val.columns)}')

print("\n=== PREPROCESSING ===")
preprocessed_data = preprocess_all_sources(cleaned_data)
for key, val in preprocessed_data.items():
    if 'metadata' not in key:
        print(f'{key}: {type(val).__name__}')
        if hasattr(val, 'columns'):
            print(f'  Columns: {list(val.columns)}')

