<h1>Automação de Testes com Selenium e SQLAlchemy</h1>

<p>Este projeto usa o Selenium WebDriver e SQLAlchemy para automatizar ações em um site da web. Ele faz login em uma página da web, verifica se há alertas e aceita-os, encontra um elemento específico na página e compara o texto desse elemento com o texto salvo em um banco de dados. Se o texto for o mesmo, ele envia um e-mail indicando que o valor está travado.</p>

![image](https://github.com/JoaoVicttorsMelo/Automacao_Dashboard/assets/69211741/6ddfe8fc-ac41-4ebf-8845-447c9499397b)


<h2>Requisitos</h2>

<ul>
    <li>Python 3</li>
    <li>Selenium</li>
    <li>SQLAlchemy</li>
    <li>WebDriver para o navegador escolhido (Chrome, Edge, etc.)</li>
    <li>yagmail</li>
</ul>

<h2>Como usar</h2>

<ol>
    <li>Clone este repositório.</li>
    <li>Instale as dependências usando pip: <code>pip install -r requirements.txt</code>.</li>
    <li>Baixe o WebDriver apropriado para o seu navegador e sistema operacional.</li>
    <li>Atualize as variáveis no script com suas informações (caminho para o WebDriver, credenciais de login, etc.).</li>
    <li>Execute o script: <code>python verifica_dash.py</code>.</li>
</ol>

<h2>Funcionalidades</h2>

<ul>
    <li>Faz login automaticamente em uma página da web.</li>
    <li>Aceita alertas.</li>
    <li>Encontra um elemento específico na página.</li>
    <li>Compara o texto do elemento com o texto salvo em um banco de dados.</li>
    <li>Envia um e-mail se o texto for o mesmo.</li>
</ul>

<h2>Contribuições</h2>

<p>Contribuições são bem-vindas! Por favor, leia as diretrizes de contribuição antes de enviar um pull request.</p>

<h2>Licença</h2>

<p>Este projeto está licenciado sob a licença MIT.</p>
