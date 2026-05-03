from config import *
from pathlib import Path
import os

print(f'RAW_DIR: {RAW_DIR}')
print(f'Files in RAW_DIR:')
for f in RAW_DIR.glob('*.csv'):
    print(f'  - {f.name} ({f.stat().st_size} bytes)')

print(f'\nDatabase connection: {DB_CONN_STRING}')

# Try to read one CSV directly
print(f'\nTrying to read {RAW_STUDENT_DETAILS_PATH}...')
import pandas as pd
df = pd.read_csv(RAW_STUDENT_DETAILS_PATH)
print(f'Successfully read {len(df)} rows')
print(f'Columns: {list(df.columns)}')
