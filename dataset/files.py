
import pandas as pd
from glob import glob

arquivos = glob('dataset/HIST_COVID/' + '*')



df = pd.DataFrame()
for arquivo in arquivos:
    frame = pd.read_csv(arquivo, sep=';')
    df = pd.concat([df, frame])

df_states = df[(~df['estado'].isna()) & (df['codmun'].isna())]
df_states = df_states.dropna(axis=1, how='all')
df_states['data'] = pd.to_datetime(df_states['data'])
df_states.sort_values(by='data', ignore_index=True, inplace=True)

df_states.to_parquet('dataset/HIST_COVID.parquet.gzip', compression='gzip', index=False)
