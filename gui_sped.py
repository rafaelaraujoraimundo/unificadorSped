import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QMessageBox, 
                             QVBoxLayout, QPushButton, QLineEdit, QListWidget, QLabel, QWidget, QAction, QHBoxLayout)
from unifica_sped import unificar_arquivos_sped, escrever_arquivo_sped
from PyQt5.QtGui import QIcon
import os

class SPEDApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('SPED Unificador - Combio')
        self.setGeometry(100, 100, 600, 400)
        
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
        self.setWindowIcon(QIcon(icon_path))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.label_principal = QLabel('Arquivo Principal:')
        layout.addWidget(self.label_principal)
        self.line_principal = QLineEdit(self)
        self.line_principal.setReadOnly(True)  # Torna a caixa de texto inativa
        layout.addWidget(self.line_principal)
        self.button_principal = QPushButton('Selecionar Arquivo Principal', self)
        self.button_principal.clicked.connect(self.select_principal)
        layout.addWidget(self.button_principal)

        self.label_secundarios = QLabel('Arquivos Secundários:')
        layout.addWidget(self.label_secundarios)
        self.list_secundarios = QListWidget(self)
        layout.addWidget(self.list_secundarios)

        # Layout horizontal para os botões de adicionar e remover arquivos secundários
        sec_buttons_layout = QHBoxLayout()
        self.button_secundarios = QPushButton('Adicionar Arquivos Secundários', self)
        self.button_secundarios.clicked.connect(self.select_secundarios)
        sec_buttons_layout.addWidget(self.button_secundarios)

        self.button_remover = QPushButton('Remover Arquivo Selecionado', self)
        self.button_remover.clicked.connect(self.remover_secundario)
        sec_buttons_layout.addWidget(self.button_remover)

        layout.addLayout(sec_buttons_layout)

        self.button_unificar = QPushButton('Unificar Arquivos', self)
        self.button_unificar.clicked.connect(self.unificar_arquivos)
        layout.addWidget(self.button_unificar)

        # Adicionando a barra de status
        self.statusBar().showMessage('Combio S/A - Versão 1.12 - Rafael Araujo')

        # Adicionando um menu "Sobre"
        menubar = self.menuBar()
        helpMenu = menubar.addMenu('Ajuda')
        aboutAction = QAction('Sobre', self)
        aboutAction.triggered.connect(self.show_about)
        helpMenu.addAction(aboutAction)

    def select_principal(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo Principal", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file:
            self.line_principal.setText(file)

    def select_secundarios(self):
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self, "Selecionar Arquivos Secundários", "", "Text Files (*.txt);;All Files (*)", options=options)
        if files:
            for file in files:
                self.list_secundarios.addItem(file)

    def remover_secundario(self):
        selected_item = self.list_secundarios.currentItem()
        if selected_item:
            reply = QMessageBox.question(self, 'Confirmação', f'Deseja realmente remover o arquivo {selected_item.text()}?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.list_secundarios.takeItem(self.list_secundarios.row(selected_item))

    def unificar_arquivos(self):
        principal = self.line_principal.text()
        secundarios = [self.list_secundarios.item(i).text() for i in range(self.list_secundarios.count())]

        if not principal or not secundarios:
            QMessageBox.warning(self, "Atenção", "Selecione o arquivo principal e pelo menos um arquivo secundário.")
            return

        reply = QMessageBox.question(self, 'Confirmação', 'Deseja realmente unificar os arquivos?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                arquivos_sped = [principal] + secundarios
                linhas_unificadas = unificar_arquivos_sped(arquivos_sped)

                options = QFileDialog.Options()
                file, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo Unificado", "", "Text Files (*.txt);;All Files (*)", options=options)
                if file:
                    escrever_arquivo_sped(file, linhas_unificadas)
                    QMessageBox.information(self, "Sucesso", f"Arquivo unificado salvo em: {file}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao unificar os arquivos: {e}")

    def show_about(self):
        QMessageBox.about(self, "Sobre", 
            ("<b>Programa:</b> Sistema de Unificação SPED<br>"
             "<b>Desenvolvido pelo Setor de Tecnologia da Informação - 2024</b><br><br>"
             "Rafael Araujo<br>"
             "rafael.araujo@combioenergia.com.br<br>"
             "<b>Versão 1.12</b>"))

def main():
    app = QApplication(sys.argv)
    ex = SPEDApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
