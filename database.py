from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Criando a conexão com o banco de dados
engine = create_engine('sqlite:///comparacao.db', echo=True)  # Substitua o tipo de banco conforme necessário
Base = declarative_base()

# Definindo o modelo
class ElementText(Base):
    __tablename__ = 'element_text'
    id = Column(Integer, primary_key=True)
    text = Column(String)

# Criando a tabela no banco, se não existir
Base.metadata.create_all(engine)

def add_text_to_db(new_text):
    Session = sessionmaker(bind=engine)
    session = Session()
    element_text = ElementText(text=new_text)
    session.add(element_text)  # Adiciona o texto ao banco de dados
    session.commit()  # Realiza o commit para persistir as alterações no banco
    session.close()

# Função para comparar valores antigo e novo
def compare_old_new_text(new_text):
    Session = sessionmaker(bind=engine)
    session = Session()
    old_text = session.query(ElementText).order_by(ElementText.id.desc()).first()

    if old_text:
        if old_text.text == new_text:
            # Se o texto for igual ao último registrado, não faz nada além de fechar a sessão
            session.close()
            return True  # Retorna True para indicar que o texto é repetido
        else:
            # Se o texto for diferente, adiciona ao banco e fecha a sessão
            add_text_to_db(new_text)
            session.close()
            return False  # Retorna False para indicar que o texto é novo
    else:
        # Se não houver texto registrado ainda, adiciona ao banco e fecha a sessão
        add_text_to_db(new_text)
        session.close()
        return False  # Retorna False para indicar que o texto é novo