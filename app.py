import base64
from datetime import datetime
import io
import sqlite3
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session as flask_session, jsonify, session
from matplotlib import pyplot as plt
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import bcrypt
import seaborn as sns
from sqlalchemy.sql import func

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# -----------------Criar a função de registro no banco - INICIO------------------
# Database configuration
database_path = r'C:\Users\joao.silveira\Desktop\Projetos_Programas\projeto_etl\Verificar_DashBoard\dist\Banco_Dados\comparacao.db'
engine = create_engine(f'sqlite:///{database_path}', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)
# -----------------Criar a função de registro no banco - FIM ------------------


# -----------------Criar a função de log - INICIO------------------
class Log(Base):
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True)
    data_hora = Column(Integer, default=func.current_timestamp(), nullable=False)
    acao = Column(String(255), nullable=False)
    usuario_id = Column(Integer, ForeignKey('funcionario.id'))


    def __init__(self, acao, usuario_id=None):
        self.acao = acao
        self.usuario_id = usuario_id
        self.data_hora = datetime.now().replace(microsecond=0)



@app.route('/log', methods=['GET'])
def log():
    if 'usuario' not in flask_session:
        return redirect(url_for('index'))

    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    query = '''
        SELECT L.acao, L.data_hora
        FROM funcionario F
        JOIN log L ON F.id = L.usuario_id
    '''

    cursor.execute(query)
    logs = [{'acao': row[0], 'data_hora': row[1]} for row in cursor.fetchall()]

    conn.close()

    return render_template('partials/log.html', logs=logs)

# Função de registro de log
def registrar_log(acao, usuario_id=None):
    db_session = Session()
    if usuario_id:
        funcionario = db_session.query(Funcionario).filter_by(id=usuario_id).first()
        if funcionario:
            acao = f"{funcionario.usuario} - {acao}"  # Adiciona o nome do usuário à ação
    log_entry = Log(acao=acao, usuario_id=usuario_id)
    db_session.add(log_entry)
    db_session.commit()
    db_session.close()

# -----------------Criar a função de log - FIM------------------


# -----------------Campo modelo do banco - INICIO------------------
# Database model
class Funcionario(Base):
    __tablename__ = 'funcionario'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    usuario = Column(String(50), nullable=False)
    senha_hash = Column(String(60), nullable=False)
    funcao = Column(Integer, ForeignKey('escritorio_funcoes.id'), nullable=False)
    isadmin = Column(Integer, nullable=False)
    inativo = Column(Integer, nullable=False)
    DataCriacao = Column(String(50), nullable=False)
    DataDesativacao = Column(String(50), nullable=False)
    # -----------------Campo que cria atauliza a senha - INICIO------------------
    def set_senha(self, senha):
        self.senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # -----------------Campo que cria atauliza a senha - FIM------------------

    # -----------------Campo que verifica a senha - INICIO------------------
    def check_senha(self, senha):
        return bcrypt.checkpw(senha.encode('utf-8'), self.senha_hash.encode('utf-8'))


# -----------------Campo que verifica a senha - FIM------------------


# -----------------Campo modelo do banco - FIM------------------


# -----------------Campo modelo do banco Funcionario - FIM------------------


# Create the table
Base.metadata.create_all(engine)

# -----------------Campo de Login - INICIO------------------

# -----------------Melhoria - Adicionar efeito Shake no html------------------


# Registro de login
@app.route('/', methods=['GET', 'POST'])
def index():
    error = False
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        db_session = Session()
        funcionario = db_session.query(Funcionario).filter_by(usuario=usuario).first()

        if funcionario and funcionario.check_senha(senha):
            # Verificação do status do usuário
            if funcionario.inativo == 0 and funcionario.DataDesativacao is None:
                flask_session['usuario'] = funcionario.usuario
                flask_session['isadmin'] = funcionario.isadmin
                flask_session['funcionario_id'] = funcionario.id

                # Registro no log
                log_entry = Log(f"Login de {funcionario.usuario}")
                db_session.add(log_entry)
                db_session.commit()
                db_session.close()

                return redirect(url_for('home'))
            else:
                # Registro no log para usuário inativo tentando acessar
                log_entry = Log(f"Tentativa de login de usuário inativo: {funcionario.usuario}")
                db_session.add(log_entry)
                db_session.commit()
                error = True
        else:
            error = True

        db_session.close()

    return render_template('index.html', error=error)


# -----------------Campo de Login - FIM------------------

# -----------------CRIA A FUNÇÃO DE DESLOGAR DO SITE - INICIO------------------

@app.route('/logout')
def logout():
    if 'usuario' in flask_session:
        usuario_id = flask_session.get('funcionario_id')

        try:
            # Registro no log
            log_entry = Log(f"Logout de {flask_session['usuario']}", usuario_id)

            with Session() as db_session:
                db_session.add(log_entry)
                db_session.commit()

        except SQLAlchemyError as e:
            # Manipule a exceção SQLAlchemyError conforme necessário
            print(f"Erro ao gravar log de logout: {e}")
            db_session.rollback()  # Faça rollback se ocorrer algum erro

        finally:
            flask_session.pop('usuario', None)
            flask_session.pop('isadmin', None)
            flask_session.pop('funcionario_id', None)

    return redirect(url_for('index'))


# -----------------CRIA A FUNÇÃO DE DESLOGAR DO SITE - FIM------------------


# -----------------CRIA A TELA INCIAL DO SITE - INICIO------------------
@app.route('/home')
def home():
    if 'usuario' not in flask_session:
        return redirect(url_for('index'))
    return render_template('partials/home.html', usuario=flask_session['usuario'], isadmin=flask_session.get('isadmin'))
# -----------------CRIA A TELA INCIAL DO SITE - FIM------------------


# ------------------- CRUD DO PROJETO INICIANDO -----------------------



# -----------------VERIFICA SEM O TI É ADMIN - INICIO------------------
def is_ti_admin(usuario_id):
    db_session = Session()
    funcionario = db_session.query(Funcionario).filter_by(id=usuario_id, funcao=1, isadmin=1).first()
    db_session.close()
    return funcionario is not None

# -----------------VERIFICA SEM O TI É ADMIN - FIM------------------



# -----------------EDITAR USUARIO - INICIO------------------

# Função para obter funções
def get_funcoes():
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, funcao FROM escritorio_funcoes;")
        funcoes = cursor.fetchall()
        conn.close()
        return funcoes
    except Exception as e:
        print(f"Error fetching funcoes: {e}")
        return []

def get_funcao_nome(funcao_id):
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT funcao FROM escritorio_funcoes WHERE id = ?", (funcao_id,))
        funcao_nome = cursor.fetchone()
        conn.close()
        return funcao_nome[0] if funcao_nome else None
    except Exception as e:
        print(f"Error fetching funcao name: {e}")
        return None



# Modificar a função de editar usuário para registrar mudanças
@app.route('/editar_usuario', methods=['GET', 'POST'])
def editar_usuario():
    if 'usuario' not in flask_session:
        return redirect(url_for('index'))

    is_admin = flask_session.get('isadmin', 0) == 1
    usuario_id = flask_session.get('funcionario_id')
    is_ti_admin_user = is_ti_admin(usuario_id)

    if request.method == 'POST':
        funcionario_id = request.form.get('funcionario_id') if is_admin else flask_session.get('funcionario_id')
        novo_usuario = request.form.get('usuario')
        nova_senha = request.form.get('senha')
        nova_funcao_id = request.form.get('funcao') if is_admin else None
        novo_isadmin = 1 if 'isadmin' in request.form and request.form['isadmin'] == 'on' else 0

        db_session = Session()
        funcionario = db_session.query(Funcionario).filter_by(id=funcionario_id).first()
        if funcionario:
            if novo_usuario and novo_usuario != funcionario.usuario:
                registrar_log(f"{funcionario.usuario} alterou o nome de usuário para {novo_usuario}", usuario_id)
                funcionario.usuario = novo_usuario
            if nova_senha:
                funcionario.set_senha(nova_senha)
                registrar_log(f"{funcionario.usuario} alterou a senha", usuario_id)
            if nova_funcao_id and nova_funcao_id != str(funcionario.funcao):
                antiga_funcao_nome = get_funcao_nome(funcionario.funcao)
                nova_funcao_nome = get_funcao_nome(nova_funcao_id)
                registrar_log(f"{funcionario.usuario} alterou a função de {antiga_funcao_nome} para {nova_funcao_nome}", usuario_id)
                funcionario.funcao = nova_funcao_id
            if is_admin and novo_isadmin != funcionario.isadmin:
                acao = "tornou-se administrador" if novo_isadmin else "não é mais administrador"
                registrar_log(f"{funcionario.usuario} {acao}", usuario_id)
                funcionario.isadmin = novo_isadmin
            db_session.commit()
        db_session.close()

        return redirect(url_for('home'))

    db_session = Session()
    funcionarios = db_session.query(Funcionario).all()
    current_funcionario = db_session.query(Funcionario).filter_by(id=usuario_id).first()
    db_session.close()
    funcoes = get_funcoes()

    current_funcionario_data = {
        'id': current_funcionario.id,
        'usuario': current_funcionario.usuario,
        'funcao': current_funcionario.funcao,
        'isadmin': current_funcionario.isadmin
    }

    return render_template('partials/editar_usuario.html',
                           funcionarios=funcionarios,
                           funcoes=funcoes,
                           isadmin=is_admin,
                           current_funcionario=current_funcionario_data,
                           is_ti_admin_user=is_ti_admin_user)

# -----------------EDITAR USUARIO - ATUALIZA SENHA - INICIO------------------
def update_password(user_id, new_password):
    db_session = Session()
    funcionario = db_session.query(Funcionario).filter_by(id=user_id).first()
    if funcionario:
        funcionario.set_senha(new_password)
        db_session.commit()
    db_session.close()

    # -----------------EDITAR USUARIO - ATUALIZA SENHA - FIM------------------


# -----------------EDITAR USUARIO - ATUALIZA FUNÇÃO - INICIO------------------

def update_role(user_id, new_role):
    db_session = Session()
    funcionario = db_session.query(Funcionario).filter_by(id=user_id).first()
    if funcionario:
        funcionario.funcao = new_role
        db_session.commit()
    db_session.close()
    # -----------------EDITAR USUARIO - ATUALIZA FUNÇÃO - FIM------------------


# -----------------EDITAR USUARIO - FIM------------------

# -----------------CRIA UM JSON COM OS FUNCIONARIOS - INICIO------------------

@app.route('/api/funcionario/<int:funcionario_id>', methods=['GET'])
def api_funcionario(funcionario_id):
    db_session = Session()
    funcionario = db_session.query(Funcionario).filter_by(id=funcionario_id).first()
    db_session.close()
    if funcionario:
        funcionario_data = {
            'id': funcionario.id,
            'usuario': funcionario.usuario,
            'funcao': funcionario.funcao,
            'isadmin': funcionario.isadmin
        }
        return jsonify(funcionario_data)
    else:
        return jsonify({'error': 'Funcionário não encontrado'}), 404
# -----------------CRIA UM JSON COM OS FUNCIONARIOS - FIM------------------


# -----------------CRIA CADASTRO DE USUARIO - INICIO------------------
# -----------------Melhoria - puxar as funções da table escritorio_funcao------------------
@app.route('/cadastrar_funcionario', methods=['GET', 'POST'])
def cadastrar_funcionario():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        funcao_id = request.form['funcao']
        isadmin = 'isadmin' in request.form  # Verifica se foi marcado como administrador

        novo_funcionario = Funcionario(
            usuario=usuario,
            senha_hash=bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            funcao=funcao_id,
            isadmin=isadmin,  # Define isadmin com base no formulário
            inativo=0,
            DataCriacao=datetime.now().replace(microsecond=0),
            DataDesativacao=None
        )

        db_session = Session()
        db_session.add(novo_funcionario)
        db_session.commit()

        # Obter o nome da função
        funcao_nome = get_funcao_nome(funcao_id)

        # Constrói a mensagem de log
        acao_log = f"Cadastro de novo funcionário: {usuario}, Função: {funcao_nome}, Administrador: {'Sim' if isadmin else 'Não'}"

        # Registra no log
        usuario_id = flask_session.get('funcionario_id')
        registrar_log(acao_log, usuario_id)

        db_session.close()

        return redirect(url_for('home'))

    funcoes = get_funcoes()
    return render_template('partials/cadastrar_funcionario.html', funcoes=funcoes)

# -----------------CRIA CADASTRO DE USUARIO - FIM------------------

# -----------------EXCLUIR CADASTRO DE USUARIO - INICIO------------------
class EscritorioFuncao(Base):
    __tablename__ = 'escritorio_funcoes'
    id = Column(Integer, primary_key=True)
    funcao = Column(String, nullable=False)

@app.route('/excluir_usuario')
def excluir_usuario():
    if 'usuario' not in flask_session:
        return redirect(url_for('index'))

    db_session = Session()
    usuarios = db_session.query(Funcionario, EscritorioFuncao).join(EscritorioFuncao,
                                                                    Funcionario.funcao == EscritorioFuncao.id).all()
    db_session.close()
    return render_template('partials/excluir_usuario.html', usuarios=usuarios)



# Rota para ativar um usuário
@app.route('/ativar_usuario', methods=['POST'])
def ativar_usuario():
    if 'funcionario_id' not in session:
        return redirect(url_for('login'))

    user_id = request.form.get('id')

    with Session() as db_session:
        try:
            user = db_session.query(Funcionario).get(user_id)
            if user:
                user.inativo = 0
                user.DataDesativacao = None
                db_session.commit()

                # Registro no log
                usuario_desabilitador_id = session.get('funcionario_id')
                usuario_desabilitador_nome = session.get('funcionario_nome')
                usuario_desabilitado_nome = user.usuario
                acao = f"Ativação do usuário '{usuario_desabilitado_nome}' por '{usuario_desabilitador_nome}'"
                registrar_log(acao, usuario_desabilitador_id)

        except Exception as e:
            db_session.rollback()
            print(f"Erro ao ativar usuário: {e}")

    return redirect(url_for('excluir_usuario'))

# Rota para desativar um usuário
@app.route('/desativar_usuario', methods=['POST'])
def desativar_usuario():
    if 'funcionario_id' not in session:
        return redirect(url_for('login'))

    user_id = request.form.get('id')

    with Session() as db_session:
        try:
            user = db_session.query(Funcionario).get(user_id)
            if user:
                user.inativo = 1
                user.DataDesativacao = datetime.now().replace(microsecond=0)
                db_session.commit()

                # Registro no log
                usuario_desabilitador_id = session.get('funcionario_id')
                usuario_desabilitador_nome = session.get('funcionario_nome')
                usuario_desabilitado_nome = user.usuario
                acao = f"Desativação do usuário '{usuario_desabilitado_nome}' por '{usuario_desabilitador_nome}'"
                registrar_log(acao, usuario_desabilitador_id)

        except Exception as e:
            db_session.rollback()
            print(f"Erro ao desativar usuário: {e}")

    return redirect(url_for('excluir_usuario'))
# -----------------EXCLUIR CADASTRO DE USUARIO - FIM------------------

# ------------------- CRUD DO PROJETO FINALIZADO -----------------------




# ------------------- INICIANDO AS FUNCIONALIDADES --------------------


# ----------------- GERANDO LISTA INICIO --------------------------------------
# -----------------Pega a data e interpreta a mesma - INICIO ------------------
def get_data(query):
    try:
        conn = sqlite3.connect(database_path)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        raise
# -----------------Pega a data e interpreta a mesma - FIM ------------------
@app.route('/gerar_lista')
def gerar_lista():
    if 'usuario' not in flask_session:
        return redirect(url_for('index'))
    # Lógica para gerar a lista
    return render_template('partials/gerar_lista.html')


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

        # Registro no log
        usuario_id = flask_session.get('funcionario_id')
        registrar_log(f"gerou lista para a data {data}", usuario_id)

        return jsonify(result)
    except Exception as e:
        print(f"Error generating list: {e}")
        return jsonify({"error": "An error occurred while generating the list"}), 500
# -----------------Gerar lista - FIM------------------


# -----------------Gerar Gráfico - INICIO------------------
def plotar_grafico(resultados):
    # Obtém todos os dias e horas únicos
    dias = sorted(set([data for data, _, _ in resultados]))
    horas = sorted(set([hora for _, hora, _ in resultados]))

    # Inicializa o dicionário para armazenar os valores
    valores_por_dia_hora = {dia: {hora: 0 for hora in horas} for dia in dias}

    # Preenche o dicionário com os valores
    for data, hora, valor in resultados:
        valores_por_dia_hora[data][hora] = valor

    fig, ax = plt.subplots()

    bar_width = 0.2
    indices = np.arange(len(horas))

    for i, dia in enumerate(dias):
        valores = [valores_por_dia_hora[dia][hora] for hora in horas]
        ax.bar(indices + i * bar_width, valores, width=bar_width, label=dia, color=sns.set_palette('husl', len(dias)))

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

@app.route('/gerar_grafico')
def gerar_grafico():
    if 'usuario' not in flask_session:
        return redirect(url_for('index'))
    # Lógica para gerar o gráfico
    return render_template('partials/gerar_grafico.html')

# -----------------Configura a data - INICIO------------------
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
# -----------------Configura a data - FIM ------------------

# Registro no gerar gráfico
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

    # Registro no log
    usuario_id = flask_session.get('funcionario_id')
    registrar_log(f"gerou gráfico de {data_inicial} a {data_final}", usuario_id)

    return jsonify({"img_str": f"data:image/png;base64,{img_base64}"})

# -----------------Gerar Gráfico - FIM------------------



if __name__ == '__main__':
    app.run(host='192.168.30.166', port=5000, debug=True)
