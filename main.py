import pandas as pd
from flask import Flask, jsonify, request, redirect
from flasgger import Swagger
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from datetime import datetime, date

#------------------Etapa 02 configuração iniciakl da aplicação
app = Flask('First API')
Swagger = Swagger(app)

#criar o banco de dados (arquivo em excel)
ARQUIVO_HISTORICO = 'Historico_chat.xlsx'

#crir as colunas que esperamos em cada arquivo
COLUNAS_HISTORICO = ['id', "mensagem_usuario", 'mensagem_bot', 'data', 'hora']

#chave de API
GROQ_API_KEY = ''

#ETAPA3 FUNCOES AUXILIARES

#FUNCOES PARA O BANCO DE DADOS DE HISTORICO DE CHAT
def get_historico_df():
    """Tentar ler o dataframe de historico do excel. Se não existir, criar uma vazia"""
    try:
        return pd.read_excel(ARQUIVO_HISTORICO, sheet_name='Historico')
    except FileNotFoundError:
        return pd.DataFrame(columns=COLUNAS_HISTORICO)
    
def save_historico_df(df):
    """ Salva o dataframe de pessoas no excel """
    df.to_excel(ARQUIVO_HISTORICO, sheet_name='Historico', index=False)


#----ETAPA4 rota de redirecionamento
@app.route("/")
def index():
    """Redirecionar a rota principal '/' para a documentação '/appidocs/'"""
    #Se algem acessar a URL raiz, é redirecionado para a documentação
    return redirect("/apidocs")

#--------ETAPA5 A CRIAÇÃO DO ENDPOINT DE COMUNICAÇÃO COM CHATBOT
@app.route("/chat", methods=['POST'])
def conversar_bot():
    """
        Enviar uma mensagem para o chatbot (groq)
        ---
        tags:
            - Chatbot
        summary: Envia uma mensagem para o chatbot
        parameters:
            - in: body
              name: body
              required: true
              schema:
                id: ChatInput
                required: [mensagem]
                properties:
                    mensagem: {type: string, example: "Olá, qual a capital da França" }
        responses:
            200:
                description: Resposta do chatbot
            400: 
                description: Mensagem do usuário  faltando
            500:
                description: Erro ao conectar com a API            
    """
    dados = request.json
    mensagem_usuario = dados.get('mensagem')
    
    if not mensagem_usuario:
        return jsonify({"Erro": "A mensagem do usuario é obrigatorial!"}), 400
    
    #etapa1 conexao com a ia
    try:
        chat = ChatGroq(
            temperature=0.7,
            model='llama-3.1-8b-instant',
            api_key=GROQ_API_KEY #PONTO DE ATENÇÃO SE NÃO FUNCIONAR
        )
        resposta_ia = chat.invoke([HumanMessage(content=mensagem_usuario)]).content
    except Exception as e:
        return jsonify({"erro": f"erro ao gerar resposta: {str(e)}"}), 500
                        
    data_atual = datetime.now()
    
    df_hist = get_historico_df()
    
    novo_id = int(df_hist['id'].max()) + 1 if not df_hist.empty else 1
    
    nova_linha = {
        'id': novo_id,
        'mensagem_usuario': mensagem_usuario,
        'mensagem_bot': resposta_ia,
        'data': data_atual.strftime("%d/%m/#Y"),
        'hora': data_atual.strftime("%H:%M:%S")        
    }
    
    #adicionar a nova linha do arquivo
    df_hist = pd.concat([df_hist, pd.DataFrame([nova_linha])], ignore_index=True)
    save_historico_df(df_hist)
    
    #retornar na api a resposta
    return jsonify({'Resposta': resposta_ia}), 200
                              
#EXECUÇÃO DA APLICAÇÃO
if __name__ == "__main__":
    app.run(debug=True)