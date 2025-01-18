import requests
import time
import serial
import openai
from datetime import datetime

# Solicitar a chave da API ao usuário
def obter_chave_api():
    chave_api = input("Digite sua chave de API do OpenAI: ")
    openai.api_key = chave_api

def solicitar_configuracoes():
    cidade = input("Digite a cidade para monitoramento do clima: ")
    latitude = input("Digite a latitude da localização: ")
    longitude = input("Digite a longitude da localização: ")
    porta_serial = input("Digite a porta serial do Arduino (ex: /dev/ttyUSB0 ou COM3): ")
    intervalo = int(input("Digite o intervalo de coleta de dados (em segundos): "))
    return {
        'cidade': cidade,
        'latitude': latitude,
        'longitude': longitude,
        'porta_serial': porta_serial,
        'intervalo': intervalo
    }

def obter_dados_clima(cidade):
    url = f'https://wttr.in/{cidade}?format=%C+%t+%h+%w'
    try:
        resposta = requests.get(url, timeout=5)
        if resposta.status_code == 200:
            return resposta.text.split()
        else:
            print(f"Erro ao obter dados do clima: {resposta.status_code}")
    except requests.RequestException:
        print("Erro de conexão ao obter dados do clima.")
    return None

def obter_dados_umidade_ar(latitude, longitude):
    url = f'https://sensor.com/api/weather/{latitude},{longitude}'
    try:
        resposta = requests.get(url, timeout=5)
        if resposta.status_code == 200:
            return resposta.json()
        else:
            print(f"Erro ao obter dados de umidade do ar: {resposta.status_code}")
    except requests.RequestException:
        print("Erro de conexão ao obter dados de umidade do ar.")
    return None

def obter_dados_luminosidade(cidade):
    url = f'http://api.luminosity.com/{cidade}'
    try:
        resposta = requests.get(url, timeout=5)
        if resposta.status_code == 200:
            return resposta.json()
        else:
            print(f"Erro ao obter dados de luminosidade: {resposta.status_code}")
    except requests.RequestException:
        print("Erro de conexão ao obter dados de luminosidade.")
    return None

def tomar_decisoes(dados_clima, dados_umidade_ar, dados_luminosidade, ser):
    try:
        temperatura = float(dados_clima[1][:-1])
        umidade_ar = dados_umidade_ar.get('humidity', 0)
        luminosidade = dados_luminosidade.get('luminosity', 0)
    except (ValueError, IndexError, TypeError):
        print("Erro ao interpretar os dados coletados.")
        return

    if temperatura > 30:
        enviar_para_arduino("irrigacao_ativar", ser)
        log_action("Irrigação ativada devido à temperatura alta.")
    elif temperatura < 15:
        enviar_para_arduino("ventilacao_ativar", ser)
        log_action("Ventilação ativada devido à temperatura baixa.")

    if umidade_ar < 40:
        enviar_para_arduino("irrigacao_ativar", ser)
        log_action("Irrigação ativada devido à baixa umidade do ar.")

    if luminosidade < 300:
        enviar_para_arduino("iluminacao_ativar", ser)
        log_action("Iluminação ativada devido à baixa luminosidade.")

def log_action(acao):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{timestamp} - {acao}")

def enviar_para_arduino(comando, ser):
    try:
        ser.write(f"{comando}\n".encode())
        resposta = ser.readline().decode().strip()
        if resposta:
            print(f"Resposta do Arduino: {resposta}")
    except serial.SerialException:
        print("Erro na comunicação com o Arduino.")

def executar_robo():
    obter_chave_api()  # Solicitar a chave da API no início
    configuracoes = solicitar_configuracoes()
    cidade = configuracoes['cidade']
    latitude = configuracoes['latitude']
    longitude = configuracoes['longitude']
    porta_serial = configuracoes['porta_serial']
    intervalo = configuracoes['intervalo']

    try:
        ser = serial.Serial(porta_serial, 9600, timeout=1)
        time.sleep(2)
        log_action("Comunicação com Arduino estabelecida.")
    except serial.SerialException:
        print(f"Erro ao conectar à porta serial {porta_serial}")
        return

    while True:
        dados_clima = obter_dados_clima(cidade)
        dados_umidade_ar = obter_dados_umidade_ar(latitude, longitude)
        dados_luminosidade = obter_dados_luminosidade(cidade)

        if dados_clima and dados_umidade_ar and dados_luminosidade:
            tomar_decisoes(dados_clima, dados_umidade_ar, dados_luminosidade, ser)
        else:
            log_action("Falha na coleta de dados. Tentando novamente...")

        time.sleep(intervalo)

if __name__ == "__main__":
    executar_robo()
