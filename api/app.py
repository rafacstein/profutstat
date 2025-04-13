from fastapi import FastAPI, Query
from typing import Optional
import boto3
import pandas as pd
import io
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente (para uso local e no Render)
load_dotenv()

# Inicializa FastAPI
app = FastAPI()

# Carrega variáveis do .env
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "sa-east-1")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_KEY = os.getenv("S3_KEY")

# Lê o arquivo Parquet do S3
def load_parquet_from_s3():
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )
    response = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
    body = response["Body"].read()
    df = pd.read_parquet(io.BytesIO(body), engine="pyarrow")
    return df

# Carrega uma vez ao iniciar
df = load_parquet_from_s3()
df["player.id"] = df["player.id"].astype(str)

@app.get("/")
def root():
    return {"message": "Bem-vindo ao Serviço API ProFutStat de consulta de jogadores"}

@app.get("/players")
def get_players(
    player_id: Optional[str] = Query(None, alias="id"),
    team_id: Optional[str] = Query(None, alias="team")
):
    filtered_df = df.copy()

    if player_id is not None:
        filtered_df = filtered_df[filtered_df["player.id"] == player_id]

    if team_name is not None:
        filtered_df = filtered_df[filtered_df["team_id"] == team_id]

    return filtered_df.to_dict(orient="records")
