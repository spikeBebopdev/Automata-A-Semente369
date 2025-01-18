import requests
import time
import serial
from datetime import datetime

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

    horario_atual = datetime.now().hour
    log_action("Verificando condições...")

    if temperatura > 30 and umidade_ar < 50:
        log_action(f"Ativando irrigação (Temperatura: {temperatura}°C, Umidade: {umidade_ar}%)")
        enviar_para_arduino("irrigacao_ativar", ser)

    if horario_atual > 18 and temperatura > 30 and luminosidade > 200:
        log_action(f"Ativando ventilação (Hora: {horario_atual}:00, Temperatura: {temperatura}°C)")
        enviar_para_arduino("ventilacao_ativar", ser)

    if luminosidade < 150:
        log_action("Ativando luz artificial (Luminosidade baixa)")
        enviar_para_arduino("iluminacao_ativar", ser)

    if horario_atual == 6 and dados_clima[0].lower() == "clear":
        log_action("Clima favorável para irrigação ao amanhecer")
        enviar_para_arduino("irrigacao_ativar", ser)

    if temperatura < 10 and umidade_ar > 90:
        log_action(f"Temperatura baixa e umidade alta. Desligando ventilação.")
        enviar_para_arduino("ventilacao_desligar", ser)
        if luminosidade < 100:
            log_action("Ativando iluminação para manter temperatura interna.")
            enviar_para_arduino("iluminacao_ativar", ser)

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
