import os
import io
import boto3
import pandas as pd
import pyarrow.parquet as pq
from flask import Flask, request, jsonify

# Inicializa o app Flask
app = Flask(__name__)

# Carrega variáveis de ambiente
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_KEY = os.getenv("S3_KEY")

# Lista de colunas esperadas (opcional para segurança)
COLUMNS = [
    'player.name', 'player.team.name', 'player.proposedMarketValue',
    'player.height', 'player.preferredFoot', 'player.country.name',
    'player.shirtNumber', 'player.dateOfBirthTimestamp',
    'player.contractUntilTimestamp', 'player.position', 'team_id',
    'positions', 'id'
]

# Função para carregar o Parquet do S3
def load_data_from_s3():
    session = boto3.session.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_DEFAULT_REGION
    )
    s3 = session.client("s3")
    obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
    buffer = io.BytesIO(obj["Body"].read())
    table = pq.read_table(buffer)
    df = table.to_pandas()

    # Garante que só colunas esperadas sejam usadas (opcional)
    df = df[[col for col in COLUMNS if col in df.columns]]

    return df

# Carrega o DataFrame na inicialização
df = load_data_from_s3()

# Função para aplicar filtros
def filter_data(player_id=None, team=None):
    filtered = df.copy()
    if player_id:
        filtered = filtered[filtered["id"] == player_id]
    if team:
        filtered = filtered[filtered["player.team.name"].str.lower() == team.lower()]
    return filtered

# Endpoint principal da API
@app.route("/players", methods=["GET"])
def get_players():
    player_id = request.args.get("player_id", type=int)
    team = request.args.get("team")

    result = filter_data(player_id, team)

    if result.empty:
        return jsonify({"message": "Nenhum jogador encontrado"}), 404

    return jsonify(result.to_dict(orient="records"))

# Executa localmente (ignorado no Render)
if __name__ == "__main__":
    app.run(debug=True)
