from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import boto3
import pandas as pd
import io
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa FastAPI
app = FastAPI()

# Variáveis de ambiente
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "sa-east-1")
S3_BUCKET = os.getenv("S3_BUCKET", "profutstat-data")

# Inicializa cliente S3
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

# Função para carregar arquivo Parquet do S3
def load_parquet_from_s3(key):
    response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
    body = response["Body"].read()
    return pd.read_parquet(io.BytesIO(body), engine="pyarrow")

# Carrega DataFrames
df_players = load_parquet_from_s3("players/bio.parquet")
df_teams = load_parquet_from_s3("teams/leagues_and_teams.parquet")

# Garantir consistência de tipos
df_players["player.id"] = df_players["player.id"].astype(str)
df_players["team_id"] = df_players["team_id"].astype(str)
df_teams["team_id"] = df_teams["team_id"].astype(str)
df_teams["team"] = df_teams["team"].astype(str)
df_teams["league"] = df_teams["league"].astype(str)

# Endpoint raiz
@app.get("/")
def root():
    return {"message": "API ProFutStat ativa com endpoints para jogadores, clubes, logos e fotos"}

# Endpoint para consulta de jogadores
@app.get("/players")
def get_players(
    player_id: Optional[str] = Query(None, alias="id"),
    team_id: Optional[str] = Query(None, alias="team")
):
    filtered_df = df_players.copy()

    if player_id:
        filtered_df = filtered_df[filtered_df["player.id"] == player_id]
    if team_id:
        filtered_df = filtered_df[filtered_df["team_id"] == team_id]

    return filtered_df.to_dict(orient="records")

# Endpoint para consulta de clubes e ligas
@app.get("/teams")
def get_teams(
    league: Optional[str] = Query(None),
    team: Optional[str] = Query(None),
):
    filtered_df = df_teams.copy()

    if league:
        filtered_df = filtered_df[filtered_df["league"].str.contains(league, case=False, na=False)]
    if team:
        filtered_df = filtered_df[filtered_df["team"].str.contains(team, case=False, na=False)]

    return filtered_df.to_dict(orient="records")

# Endpoint para logo do clube
@app.get("/team-logo")
def get_team_logo(team_id: str):
    key = f"teams/logo/team_{team_id}.png"
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
        return StreamingResponse(response["Body"], media_type="image/png")
    except Exception:
        return {"erro": f"Logo não encontrada para o time {team_id}"}

# Endpoint para foto do jogador
@app.get("/player-photo")
def get_player_photo(player_id: str):
    key = f"players/photo/{player_id}.png"
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
        return StreamingResponse(response["Body"], media_type="image/png")
    except Exception:
        return {"erro": f"Foto não encontrada para o jogador {player_id}"}
