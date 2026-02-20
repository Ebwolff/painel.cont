# GUIA DO SISTEMA: END Monitor Contábil

Este guia explica, de forma simples e direta, como o **END Monitor Contábil** funciona e como ele ajuda o seu escritório e seus clientes a lidarem com a Reforma Tributária.

---

## 1. Como a informação entra no sistema?
Existem duas formas principais de o sistema receber os dados:
*   **Busca Automática:** O sistema se conecta diretamente com a SEFAZ (Governo) usando o Certificado Digital A1 da empresa. Ele monitora e baixa as notas fiscais assim que são emitidas.
*   **Envio Manual:** O usuário pode simplesmente arrastar e soltar os arquivos das notas fiscais (o arquivo XML) dentro do sistema para que ele comece a trabalhar.

---

## 2. Como o sistema processa as notas?
Assim que o sistema recebe uma nota, ele realiza uma "leitura inteligente":
*   Ele identifica quem vendeu, quem comprou e qual o valor total da operação.
*   Ele busca especificamente os novos impostos da Reforma (CBS e IBS) para ver o que foi escrito na nota.

---

## 3. Como é feita a conferência (Validação)?
O sistema funciona como um "auditor automático". Ele não apenas lê a nota, ele **refaz os cálculos** para ver se estão certos:
*   **O cálculo da Lei:** De acordo com as novas regras, o sistema sabe que os impostos devem ser de 0,9% (CBS) e 0,1% (IBS).
*   **A Comparação:** O sistema pega o valor total da nota e calcula quanto esses impostos deveriam ser. Depois, ele olha para o que o emissor da nota escreveu.
*   **O Alerta:** Se houver qualquer diferença maior que 5 centavos, o sistema avisa na hora que aquela nota está com erro ("Irregular").

---

## 4. Como o sistema gera valor (Resultados)?
O objetivo final é transformar esses dados em economia e segurança:
*   **Identificação de Créditos:** O sistema mostra ao cliente quanto ele tem de dinheiro para recuperar em impostos (aproximadamente 1% de tudo o que ele comprou/vendeu).
*   **Prevenção de Multas:** Ao avisar que uma nota está errada, o sistema permite que o erro seja corrigido antes que vire uma multa ou um problema com o fisco.
*   **Prova de Trabalho:** O contador consegue mostrar um relatório claro de quanto dinheiro ele "salvou" para o cliente através desse monitoramento.

---

## 5. Onde as informações ficam guardadas?
Tudo o que o sistema processa fica guardado com segurança em uma base de dados centralizada. Isso permite que você veja a evolução da empresa nos últimos 6 meses, acompanhando se os erros estão diminuindo e se a economia está aumentando ao longo do tempo.
