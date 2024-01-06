import time
import datetime
from database import compare_old_new_text
import yagmail
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.chrome.options import Options


def verificar_horario():
    horario_atual = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))  # Fuso horário do Brasil (GMT-3)
    hora_inicio = horario_atual.replace(hour=10, minute=30, second=0, microsecond=0)  # Horário de início (10:30)
    hora_limite = horario_atual.replace(hour=23, minute=0, second=0, microsecond=0)  # Horário limite (23:00)

    if horario_atual < hora_inicio:
        return False  # Sai do programa se for mais cedo que 10:30
    elif horario_atual >= hora_limite:
        return False # Sai do programa se for mais tarde que 23:00
    else:
        return True


if verificar_horario():
    # Crie uma instância de Options
    opcoes = Options()

    # Adicione o argumento "--headless"
    opcoes.add_argument("--headless")

    # Inicialize o driver do navegador com as opções especificadas
    driver = webdriver.Chrome(options=opcoes)

    # Configurações do e-mail e autenticação
    sender_email = 'E-MAIL QUE VAI ENVIAR'
    receiver_email = 'E-MAIL QUE RECEBER'
    subject = 'TITULO DO E-MAIL'
    smtp_username = 'E-MAIL QUE VAI ENVIAR'
    smtp_password = 'senha do SMTP DO GMAIL'

    # Abra a página de login
    driver.get('SITE DO DASHBOARD')

    # Aguarde 5 segundos para o site abrir
    time.sleep(5)

    # Encontre os campos de nome de usuário e senha e insira suas credenciais
    username = driver.find_element(By.CSS_SELECTOR, 'input#j_username.ui-inputfield.ui-inputtext.ui-widget.ui-state-default.ui-corner-all')
    password = driver.find_element(By.CSS_SELECTOR, 'input#j_password.ui-inputfield.ui-password.ui-widget.ui-state-default.ui-corner-all')
    username.send_keys('MINHA CREDENCIAL')
    password.send_keys('MINHA CREDENCIAL')

    # Pressione Enter para fazer login
    password.send_keys(Keys.RETURN)

    # Aguarde 3 minutos para a página carregar
    time.sleep(10)

    # Verifique se há um alerta e aceite-o se houver
    try:
        alert = Alert(driver)
        alert.accept()
    except:
        pass

    # Encontre o elemento desejado pelo ID
    element = driver.find_element(By.ID, 'tabViewGeral:0:j_idt385:13:j_idt904')

    # Obtenha o texto dentro do elemento
    element_text = element.text

    text_changed = compare_old_new_text(element_text)

    if text_changed:
        # Cria uma instância do objeto yagmail
        yag = yagmail.SMTP(smtp_username, smtp_password)

        # Cria o assunto do e-mail
        email_subject = f"{subject}"

        # Envia o e-mail somente se o texto tiver mudado
        yag.send(
            to=receiver_email,
            subject=email_subject,
            contents=f"""
                <div style="text-align: center;">
                    <p><strong style="color: red;">IMPORTANTE</strong></p>
                    <p>O valor de {element.text} está travado há mais de 40 minutos. Por favor, verifique.</p>
                    <br><br><br>
                </div>
            """,
            headers={'X-Priority': '1'}
        )
        driver.quit()
    else:
        driver.quit()
