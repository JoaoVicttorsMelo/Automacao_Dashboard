import base64
import io
import sqlite3

import numpy as np
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session as flask_session, jsonify
from matplotlib import pyplot as plt
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database configuration
database_path = r'C:\Users\joao.silveira\Desktop\Projetos_Programas\projeto_etl\Verificar_DashBoard\dist\Banco_Dados\comparacao.db'
engine = create_engine(f'sqlite:///{database_path}', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)

def extrair_datas_horas_texto_com_filtro(cursor, query, data_inicial, data_final):
    cursor.execute(query, (data_inicial, data_final))
    rows = cursor.fetchall()
    resultados = []
    for texto, created_at in rows:
        data, horario_completo = created_at.split(' ')
        hora = horario_completo[:2]
        texto = texto.replace('.', '')  # Removendo pontos para conversão numérica
        resultados.append((data, hora, float(texto)))  # Convertendo texto para float para comparação numérica
    return resultados


def plotar_grafico(resultados):
    # Obtém todos os dias e horas únicos
    dias = sorted(set([data for data, _, _ in resultados]))
    horas = sorted(set([hora for _, hora, _ in resultados]))

    # Inicializa o dicionário para armazenar os valores
    valores_por_dia_hora = {dia: {hora: 0 for hora in horas} for dia in dias}

    # Preenche o dicionário com os valores
    for data, hora, valor in resultados:
        valores_por_dia_hora[data][hora] = valor

    # Cria a lista de cores, usando uma cor diferente para cada dia
    cores = ['blue', 'green', 'red', 'purple', 'orange', 'brown', 'pink', 'gray', 'cyan', 'magenta']

    fig, ax = plt.subplots()

    bar_width = 0.2
    indices = np.arange(len(horas))

    for i, dia in enumerate(dias):
        valores = [valores_por_dia_hora[dia][hora] for hora in horas]
        ax.bar(indices + i * bar_width, valores, width=bar_width, label=dia, color=cores[i % len(cores)])

    ax.set_xlabel('Horário')
    ax.set_ylabel('Valor')
    ax.set_title('Comparação de valores entre as datas selecionadas por horário')
    ax.legend()
    ax.set_xticks(indices + bar_width * (len(dias) - 1) / 2)
    ax.set_xticklabels(horas)

    plt.xticks(rotation=45)
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()  # Fechar o plot para liberar memória

    return img_base64

def get_data(query):
    try:
        conn = sqlite3.connect(database_path)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        raise

# Database model
class Funcionario(Base):
    __tablename__ = 'funcionario'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    usuario = Column(String(50), nullable=False)
    senha_hash = Column(String(60), nullable=False)
    funcao = Column(String(60), nullable=False)
    isadmin = Column(Boolean, nullable=False, default=False)

    def set_senha(self, senha):
        self.senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_senha(self, senha):
        return bcrypt.checkpw(senha.encode('utf-8'), self.senha_hash.encode('utf-8'))

# Create the table
Base.metadata.create_all(engine)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = False
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        db_session = Session()
        funcionario = db_session.query(Funcionario).filter_by(usuario=usuario).first()
        db_session.close()

        if funcionario and funcionario.check_senha(senha):
            flask_session['usuario'] = funcionario.usuario
            flask_session['isadmin'] = funcionario.isadmin
            return redirect(url_for('home'))
        else:
            error = True
    return render_template('index.html', error=error)

@app.route('/home')
def home():
    if 'usuario' not in flask_session:
        return redirect(url_for('index'))
    return render_template('home.html', usuario=flask_session['usuario'], isadmin=flask_session.get('isadmin'))

@app.route('/logout')
def logout():
    flask_session.pop('usuario', None)
    flask_session.pop('isadmin', None)
    return redirect(url_for('index'))

@app.route('/gerar_grafico_ajax', methods=['GET'])
def gerar_grafico_ajax():
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')

    db_path = r"C:\Users\joao.silveira\Desktop\Projetos_Programas\projeto_etl\Verificar_DashBoard\dist\Banco_Dados\comparacao.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
    SELECT text, created_At
    FROM element_text
    WHERE DATE(created_At) BETWEEN DATE(?) AND DATE(?);
    """

    resultados = extrair_datas_horas_texto_com_filtro(cursor, query, data_inicial, data_final)
    conn.close()

    img_base64 = plotar_grafico(resultados)
    return jsonify({"img_str": f"data:image/png;base64,{img_base64}"})


@app.route('/gerar_lista_ajax', methods=['GET'])
def gerar_lista_ajax():
    data = request.args.get('data')

    try:
        query = f"SELECT text, created_at FROM element_text WHERE DATE(created_at) = '{data}'"
        df = get_data(query)

        if df.empty:
            return jsonify({"error": "No data found for the selected date"}), 404

        # Gerando a lista de resultados
        result = df.to_dict(orient='records')
        return jsonify(result)
    except Exception as e:
        print(f"Error generating list: {e}")
        return jsonify({"error": "An error occurred while generating the list"}), 500

@app.route('/gerar_grafico')
def gerar_grafico():
    if 'usuario' not in flask_session:
        return redirect(url_for('index'))
    # Lógica para gerar o gráfico
    return render_template('partials/gerar_grafico.html')

@app.route('/gerar_lista')
def gerar_lista():
    if 'usuario' not in flask_session:
        return redirect(url_for('index'))
    # Lógica para gerar a lista
    return render_template('partials/gerar_lista.html')

@app.route('/cadastrar_funcionario', methods=['GET', 'POST'])
def cadastrar_funcionario():
    if 'usuario' not in flask_session or not flask_session.get('isadmin'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        funcao = request.form['funcao']
        isadmin = request.form.get('isadmin') == 'on'

        db_session = Session()
        novo_funcionario = Funcionario(usuario=usuario, funcao=funcao, isadmin=isadmin)
        novo_funcionario.set_senha(senha)
        db_session.add(novo_funcionario)
        db_session.commit()
        db_session.close()

        return redirect(url_for('home'))

    return render_template('partials/cadastrar_funcionario.html')

if __name__ == '__main__':
    app.run(host='192.168.30.166', port=5000, debug=True)
