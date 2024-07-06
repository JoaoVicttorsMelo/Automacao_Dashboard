import time
import yagmail
import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from datetime import timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuração do banco de dados
database_path = r'database_path'
engine = create_engine(f'sqlite:///{database_path}', echo=True)  # Substitua conforme necessário
Base = declarative_base()


class ElementText(Base):
    __tablename__ = 'element_text'
    id = Column(Integer, primary_key=True)
    text = Column(String)
    created_at = Column(DateTime)


Base.metadata.create_all(engine)


def add_text_to_db(new_text):
    Session = sessionmaker(bind=engine)
    session = Session()
    adjusted_time = datetime.datetime.now() - timedelta(hours=0)
    element_text = ElementText(text=new_text, created_at=adjusted_time)
    session.add(element_text)
    session.commit()
    session.close()


def compare_old_new_text(new_text):
    Session = sessionmaker(bind=engine)
    session = Session()
    old_text = session.query(ElementText).order_by(ElementText.id.desc()).first()

    if old_text:
        if old_text.text == new_text:
            session.close()
            return True
        else:
            add_text_to_db(new_text)
            session.close()
            return False
    else:
        add_text_to_db(new_text)
        session.close()
        return False


# Lista de feriados (formato: 'AAAA-MM-DD')
feriados = [
    '2024-01-01',  # Ano Novo
    '2024-04-21',  # Tiradentes
    '2024-05-01',  # Dia do Trabalho
    '2024-09-07',  # Independência do Brasil
    '2024-10-12',  # Nossa Senhora Aparecida
    '2024-11-02',  # Finados
    '2024-11-15',  # Proclamação da República
    # Adicione mais feriados conforme necessário
]


def verificar_horario():
    horario_atual = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
    hora_especifica_inicio = horario_atual.replace(hour=14, minute=30, second=0, microsecond=0)
    hora_especifica_fim = horario_atual.replace(hour=20, minute=30, second=0, microsecond=0)
    hora_inicio = horario_atual.replace(hour=10, minute=30, second=0, microsecond=0)
    hora_limite = horario_atual.replace(hour=23, minute=10, second=0, microsecond=0)

    # Verifica se é domingo ou feriado e se o horário está entre 14:30 e 20:00
    if horario_atual.weekday() == 6 or horario_atual.strftime('%Y-%m-%d') in feriados:  # Domingo é representado por 6
        return hora_especifica_inicio <= horario_atual < hora_especifica_fim
    else:
        return hora_inicio <= horario_atual < hora_limite


def salvar_arquivo_txt(mensagem, caminho_log):
    with open(f"{caminho_log}/log_erro_banco.txt", "a") as file:
        file.write(f"{datetime.datetime.now()}: {mensagem}\n")


def salvar_elemento_txt(element_text, proximo_horario, caminho_log):
    with open(f"{caminho_log}/log.txt", "a") as file:
        file.write(f"{datetime.datetime.now()}: {element_text}\n")
        file.write(f"Próximo horário de execução: {proximo_horario}\n")


caminho_log = r"caminho_log"

while True:
    while not verificar_horario():
        time.sleep(300)  # Espera 5 minutos antes de verificar novamente

    opcoes = Options()
    opcoes.add_argument("--headless")
    driver = webdriver.Chrome(options=opcoes)

    sender_email = 'sender_email'
    receiver_email = ['receiver_email']
    subject = 'subject'
    smtp_username = 'smtp_username'
    smtp_password = 'smtp_password'

    driver.get('link')
    time.sleep(5)

    try:
        username = driver.find_element(By.CSS_SELECTOR,
                                       'input#j_username.ui-inputfield.ui-inputtext.ui-widget.ui-state-default.ui-corner-all')
        password = driver.find_element(By.CSS_SELECTOR,
                                       'input#j_password.ui-inputfield.ui-password.ui-widget.ui-state-default.ui-corner-all')
        username.send_keys('username')
        password.send_keys('password')
    except NoSuchElementException:
        yag = yagmail.SMTP(smtp_username, smtp_password)
        yag.send(
            to=receiver_email,
            subject="Erro ao acessar campos de login - Favor verificar",
            contents="""
                <div style="text-align: center;">
                    <p><strong style="color: red;">ALERTA</strong></p>
                    <p>O campo de login ou senha não foi encontrado na página. Por favor, verifique.</p>
                    <br><br><br>
                </div>
            """,
            headers={'X-Priority': '1'}
        )
        driver.quit()
        continue

    password.send_keys(Keys.RETURN)
    time.sleep(10)

    try:
        alert = Alert(driver)
        alert.accept()
    except:
        pass

    try:
        value_id = 'tabViewGeral:0:j_idt378:13:j_idt897'
        element = driver.find_element(By.ID, value_id)
        element_text = element.text

        try:
            text_changed = compare_old_new_text(element_text)
            # Calcular o próximo horário de execução
            proximo_horario = datetime.datetime.now() + timedelta(seconds=2220)
            salvar_elemento_txt(element_text, proximo_horario, caminho_log)
        except Exception as e:
            salvar_arquivo_txt(f"Erro ao verificar ou salvar no banco de dados: {e}", caminho_log)
            text_changed = False

        if text_changed:
            yag = yagmail.SMTP(smtp_username, smtp_password)
            yag.send(
                to=receiver_email,
                subject=subject,
                contents=f"""
                    <div style="text-align: center;">
                        <p><strong style="color: red;">IMPORTANTE</strong></p>
                        <p>O valor de {element.text} está travado há mais de 40 minutos. Por favor, verifique.</p>
                        <br><br><br>
                    </div>
                """,
                headers={'X-Priority': '1'}
            )
    except NoSuchElementException:
        yag = yagmail.SMTP(smtp_username, smtp_password)
        yag.send(
            to=receiver_email,
            subject="ID não encontrado - Favor verificar",
            contents=f"""
                <div style="text-align: center;">
                    <p><strong style="color: red;">ALERTA</strong></p>
                    <p>O ID {value_id} não foi encontrado na página. Por favor, verifique.</p>
                    <br><br><br>
                </div>
            """,
            headers={'X-Priority': '1'}
        )
    except Exception as e:
        salvar_arquivo_txt(f"Erro ao acessar a página ou processar o elemento: {e}", caminho_log)
    finally:
        driver.quit()
    time.sleep(2280)