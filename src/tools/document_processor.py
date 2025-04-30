class ProcessadorDocumento:
    def __init__(self, conversor):
        self.conversor = conversor
    
    def processar_arquivo(self, caminho_arquivo, 
                          executar_ocr=False, 
                          executar_layout=True, 
                          executar_tabelas=True, 
                          executar_qa=False, 
                          executar_qa_imagens=False,
                          exportar_markdown=True,
                          exportar_texto=True,
                          exportar_json=False,
                          chunking=False,
                          export_to_langchain=False,
                          modelo_llm=None):
        # Processa o documento usando o conversor
        resultado = self.conversor.processar_documento(
            caminho_arquivo=caminho_arquivo,
            executar_ocr=executar_ocr,
            executar_layout=executar_layout,
            executar_tabelas=executar_tabelas,
            executar_qa=executar_qa,
            executar_qa_imagens=executar_qa_imagens,
            exportar_markdown=exportar_markdown,
            exportar_texto=exportar_texto,
            exportar_json=exportar_json,
            chunking=chunking,
            export_to_langchain=export_to_langchain,
            modelo_llm=modelo_llm
        )
        return resultado 