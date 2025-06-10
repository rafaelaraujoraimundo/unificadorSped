import os

def ler_arquivo_sped(caminho):
    """
    Lê um arquivo SPED e retorna suas linhas.
    Tenta a leitura com 'utf-8' primeiro, e se falhar, tenta com 'latin1'.
    """
    try:
        with open(caminho, 'r', encoding='utf-8') as arquivo:
            return arquivo.readlines()
    except UnicodeDecodeError:
        with open(caminho, 'r', encoding='latin1') as arquivo:
            return arquivo.readlines()

def escrever_arquivo_sped(caminho, linhas):
    """
    Escreve as linhas em um arquivo SPED no caminho especificado.
    """
    with open(caminho, 'w', encoding='utf-8') as arquivo:
        arquivo.writelines(linhas)

def processar_blocos_unicos_0(arquivos):
    """
    Processa blocos únicos que começam com 0 (exceto 0300, 0305 e 0990).
    Inclui o bloco 0005 do primeiro arquivo após a linha 0002.
    Retorna uma lista de linhas unificadas.
    """
    registros_unicos = {}
    bloco_0005 = processar_bloco_0005(arquivos)
    bloco_0002 = []

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
           if linha.startswith('|0') and not (
                linha.startswith('|0005') or 
                linha.startswith('|0200') or 
                linha.startswith('|0205') or 
                linha.startswith('|0220') or 
                linha.startswith('|0300') or 
                linha.startswith('|0305') or 
                linha.startswith('|0500') or 
                linha.startswith('|0990')):
                reg = linha.split('|')[1]
                chave = (reg, linha.split('|')[2])
                if chave not in registros_unicos:
                    registros_unicos[chave] = linha

    linhas_unificadas = []
    for chave in sorted(registros_unicos.keys()):
        linha = registros_unicos[chave]
        linhas_unificadas.append(linha)
        if linha.startswith('|0002|') and bloco_0005:
            linhas_unificadas.extend(bloco_0005)

    return linhas_unificadas

def processar_blocos_0200_em_estrutura(arquivos):
    """
    Processa os blocos 0200, 0205 e 0220 de todos os arquivos,
    garantindo que mesmo que o 0200 e o 0220 (ou 0205) apareçam em arquivos diferentes,
    eles sejam unificados corretamente.

    Passos:
    1) Lê todas as linhas de todos os arquivos e junta em uma única lista.
    2) Identifica a "ordem de aparição" do COD_ITEM, pela primeira vez que aparecer
       em qualquer registro 0200/0205/0220.
    3) Cria um dicionário onde cada COD_ITEM mapeia para:
       - '0200': linha 0200 (se existir)
       - '0205': set de linhas 0205
       - '0220': set de linhas 0220
    4) Gera a lista final na ordem de primeiro aparecimento do COD_ITEM.
    """

    # 1) Lê e concatena todas as linhas de todos os arquivos
    todas_as_linhas = []
    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        todas_as_linhas.extend(linhas)

    # 2) Descobre, para cada linha 0200/0205/0220, qual é o COD_ITEM
    #    e em que posição total (índice) ele apareceu pela primeira vez.
    ordem_cod_item = {}  # dict: cod_item -> índice da primeira aparição
    for indice, linha in enumerate(todas_as_linhas):
        if (
            linha.startswith('|0200|') or
            linha.startswith('|0205|') or
            linha.startswith('|0220|')
        ):
            partes = linha.strip().split('|')
            if len(partes) < 3:
                continue
            reg = partes[1]
            cod_item = partes[2]
            if cod_item not in ordem_cod_item:
                # Salva o índice em que esse COD_ITEM apareceu pela primeira vez
                ordem_cod_item[cod_item] = indice

    # Ordena os COD_ITEMs pela posição de primeiro aparecimento
    cod_items_ordenados = sorted(ordem_cod_item.keys(), key=lambda c: ordem_cod_item[c])

    # 3) Cria o dicionário que relaciona COD_ITEM ao seu 0200, 0205, 0220
    registros_por_cod_item = {
        cod_item: {
            '0200': None,
            '0205': set(),
            '0220': set()
        }
        for cod_item in cod_items_ordenados
    }

    # Preenche os dados
    for linha in todas_as_linhas:
        if (
            linha.startswith('|0200|') or
            linha.startswith('|0205|') or
            linha.startswith('|0220|')
        ):
            partes = linha.strip().split('|')
            if len(partes) < 3:
                continue
            reg = partes[1]
            cod_item = partes[2]

            if cod_item in registros_por_cod_item:  # Garantia de que este COD_ITEM apareceu em algum lugar
                if reg == '0200':
                    # Guarda a linha 0200 caso ainda não tenha uma
                    if registros_por_cod_item[cod_item]['0200'] is None:
                        registros_por_cod_item[cod_item]['0200'] = linha
                elif reg == '0205':
                    registros_por_cod_item[cod_item]['0205'].add(linha)
                elif reg == '0220':
                    registros_por_cod_item[cod_item]['0220'].add(linha)

    # 4) Gera a lista final, mantendo a ordem de primeiro aparecimento do COD_ITEM
    #    e a estrutura: 0200, em seguida 0205(s), depois 0220(s).
    linhas_unificadas = []
    for cod_item in cod_items_ordenados:
        dado = registros_por_cod_item[cod_item]
        # Se houver 0200, acrescenta
        if dado['0200']:
            linhas_unificadas.append(dado['0200'])
        # Acrescenta as 0205
        for linha_0205 in sorted(dado['0205']):
            linhas_unificadas.append(linha_0205)
        # Acrescenta as 0220
        for linha_0220 in sorted(dado['0220']):
            linhas_unificadas.append(linha_0220)

    return linhas_unificadas

def processar_bloco_0005(arquivos):
    """
    Processa o bloco 0005 copiando-o apenas do primeiro arquivo.
    """
    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|0005|'):
                return [linha]
    return []

def processar_blocos_0300_0305(arquivos):
    """
    Processa blocos 0300 e 0305.
    Retorna uma lista de linhas unificadas.
    """
    linhas_0300_0305 = []
    temp_0300 = None
    
    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|0300|'):
                if temp_0300:
                    linhas_0300_0305.append(temp_0300)
                temp_0300 = linha
            elif linha.startswith('|0305|'):
                if temp_0300:
                    linhas_0300_0305.append(temp_0300)
                    linhas_0300_0305.append(linha)
                    temp_0300 = None
            else:
                if temp_0300:
                    linhas_0300_0305.append(temp_0300)
                    temp_0300 = None
    if temp_0300:
        linhas_0300_0305.append(temp_0300)
    
    return linhas_0300_0305

def processar_bloco_0500(arquivos):
    """
    Processa o bloco 0500 garantindo que cada linha seja única por todos os campos.
    Retorna uma lista de linhas únicas do bloco 0500.
    """
    registros_0500 = set()
    linhas_0500_unicas = []

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|0500|'):
                if linha not in registros_0500:
                    registros_0500.add(linha)
                    linhas_0500_unicas.append(linha)

    return linhas_0500_unicas


def adicionar_bloco_9(linhas_unificadas):
    bloco_9 = ["|9001|0|\n"]

    registros_contagem = {}
    for linha in linhas_unificadas:
        if not linha.startswith('|9900|'):  # IGNORA os que já são totalizadores
            reg = linha.split('|')[1]
            if reg not in registros_contagem:
                registros_contagem[reg] = 0
            registros_contagem[reg] += 1

    for reg, contagem in registros_contagem.items():
        bloco_9.append(f"|9900|{reg}|{contagem}|\n")

    bloco_9.append("|9900|9001|1|\n")
    bloco_9.append(f"|9900|9900|{len(bloco_9) + 2}|\n")
    bloco_9.append("|9900|9990|1|\n")
    bloco_9.append("|9900|9999|1|\n")

    qtd_lin_9 = len(bloco_9) + 1
    bloco_9.append(f"|9990|{qtd_lin_9}|\n")

    return bloco_9

def adicionar_encerramento_bloco_0(linhas_unificadas):
    """
    Adiciona a linha de encerramento do bloco 0 (0990) ao final das linhas unificadas.
    """
    qtd_lin_0 = sum(1 for linha in linhas_unificadas if linha.startswith('|0')) + 1
    linhas_unificadas.append(f"|0990|{qtd_lin_0}|\n")
    return linhas_unificadas

def adicionar_encerramento_arquivo(linhas_unificadas):
    """
    Adiciona a linha de encerramento do arquivo (9999) ao final das linhas unificadas.
    """
    qtd_lin = len(linhas) + 1
    linhas_unificadas.append(f"|9999|{qtd_lin}|\n")
    return linhas_unificadas

def importar_blocos_especificos(caminho):
    """
    Importa blocos específicos dos arquivos SPED.
    """
    blocos_importados = []
    blocos_a_importar = ['|B001|1|', '|B990|', '|1001|0|', '|1010|']
    linhas = ler_arquivo_sped(caminho)
    for linha in linhas:
        if any(linha.startswith(bloco) for bloco in blocos_a_importar):
            blocos_importados.append(linha)
    return blocos_importados

def totalizar_blocos_X990(linhas_unificadas):
    """
    Totaliza os blocos X990 e os adiciona às linhas unificadas.
    """
    blocos_X990 = {}
    for linha in linhas_unificadas:
        if linha.endswith('990|'):
            bloco = linha.split('|')[1]
            if bloco not in blocos_X990:
                blocos_X990[bloco] = 0
            blocos_X990[bloco] += 1

    for bloco, contagem in blocos_X990.items():
        linhas_unificadas.append(f"|{bloco}990|{contagem + 1}|\n")
    
    return linhas_unificadas

def organizar_blocos(linhas_unificadas):
    """
    Organiza os blocos na ordem especificada.
    """
    blocos_ordenados = {'0': [], 'B': [], 'C': [], 'D': [], 'E': [], 'F': [], 'G': [], 'H': [], 'I': [], 'J': [], 'K': [], 'L': [], 'M': [], 'N': [], 'O': [], 'P': [], 'Q': [], 'R': [], 'S': [], 'T': [], '1': [], '9': []}
    
    for linha in linhas_unificadas:
        bloco = linha.split('|')[1][0]  # Identifica o bloco pelo segundo caractere da linha (depois do primeiro '|')
        if bloco in blocos_ordenados:
            blocos_ordenados[bloco].append(linha)
    
    linhas_reorganizadas = []
    for bloco in '0BCDEFGHIJKLMNOPQRST19':
        linhas_reorganizadas.extend(blocos_ordenados[bloco])
    
    return linhas_reorganizadas

def processar_bloco_e100(arquivos):
    """
    Processa o bloco E100 copiando-o apenas do primeiro arquivo.
    """
    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|E100|'):
                return [linha]
    return []

def processar_bloco_e110(arquivos):
    """
    Processa o bloco E110 somando os valores correspondentes de cada arquivo.
    """
    soma_e110 = None

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|E110|'):
                valores = [float(valor.replace(',', '.')) for valor in linha.split('|')[2:-1]]
                if soma_e110 is None:
                    soma_e110 = valores
                else:
                    soma_e110 = [soma + valor for soma, valor in zip(soma_e110, valores)]

    if soma_e110 is not None:
        linha_somada = '|E110|' + '|'.join(f"{valor:.2f}".replace('.', ',') for valor in soma_e110) + '|\n'
        return [linha_somada]
    
    return []

def processar_bloco_e111(arquivos):
    """
    Processa o bloco E111 somando apenas o quarto campo se houver o mesmo campo nos arquivos.
    """
    soma_e111 = 0.0
    primeira_linha = None
    
    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|E111|'):
                campos = linha.split('|')
                if primeira_linha is None:
                    primeira_linha = linha
                soma_e111 += float(campos[4].replace(',', '.'))

    if primeira_linha:
        campos = primeira_linha.split('|')
        soma_e111_texto = f"{soma_e111:.2f}".replace('.', ',')
        linha_somada = f"|E111|{campos[2]}|{campos[3]}|{soma_e111_texto}|\n"
        return [linha_somada]
    
    return []

def processar_bloco_e116(arquivos):
    """
    Processa o bloco E116 somando o terceiro campo e mantendo os outros campos inalterados.
    """
    soma_e116 = 0.0
    primeira_linha = None

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|E116|'):
                campos = linha.split('|')
                if primeira_linha is None:
                    primeira_linha = linha
                soma_e116 += float(campos[3].replace(',', '.'))

    if primeira_linha:
        campos = primeira_linha.split('|')
        soma_e116_texto = f"{soma_e116:.2f}".replace('.', ',')
        linha_somada = f"|E116|{campos[2]}|{soma_e116_texto}|{campos[4]}|{campos[5]}|{campos[6]}|{campos[7]}|{campos[8]}|{campos[9]}|{campos[10]}|\n"
        return [linha_somada]
    
    return []

def processar_bloco_e200_e210(arquivos):
    """
    Processa os blocos E200 e E210 somando os valores correspondentes de cada arquivo,
    e fixa o campo após E210 como 0.
    """
    blocos_e200_e210 = {}
    
    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        bloco_e200_atual = None
        for linha in linhas:
            if linha.startswith('|E200|'):
                bloco_e200_atual = linha
                if bloco_e200_atual not in blocos_e200_e210:
                    blocos_e200_e210[bloco_e200_atual] = []
            elif linha.startswith('|E210|') and bloco_e200_atual is not None:
                valores = [float(valor.replace(',', '.')) for valor in linha.split('|')[3:-1]]  # Ignora o campo após E210
                if blocos_e200_e210[bloco_e200_atual] == []:
                    blocos_e200_e210[bloco_e200_atual] = valores
                else:
                    blocos_e200_e210[bloco_e200_atual] = [soma + valor for soma, valor in zip(blocos_e200_e210[bloco_e200_atual], valores)]

    blocos_finais = []
    for bloco_e200, valores_e210 in blocos_e200_e210.items():
        blocos_finais.append(bloco_e200)
        linha_somada_e210 = '|E210|0|' + '|'.join(f"{valor:.2f}".replace('.', ',') for valor in valores_e210) + '|\n'
        blocos_finais.append(linha_somada_e210)
    
    return blocos_finais

def processar_bloco_e500(arquivos):
    """
    Processa o bloco E500 copiando-o apenas do primeiro arquivo.
    """
    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|E500|'):
                return [linha]
    return []

def processar_bloco_e510(arquivos):
    """
    Processa o bloco E510 somando os campos correspondentes de cada arquivo.
    """
    blocos_e510 = {}

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|E510|'):
                chave = tuple(linha.split('|')[1:4])
                valores = [float(valor.replace(',', '.')) for valor in linha.split('|')[4:-1]]
                if chave not in blocos_e510:
                    blocos_e510[chave] = valores
                else:
                    blocos_e510[chave] = [soma + valor for soma, valor in zip(blocos_e510[chave], valores)]

    blocos_finais = []
    for chave, valores in blocos_e510.items():
        linha_somada = '|' + '|'.join(chave) + '|' + '|'.join(f"{valor:.2f}".replace('.', ',') for valor in valores) + '|\n'
        blocos_finais.append(linha_somada)
    
    return blocos_finais

def processar_bloco_c(arquivos):
    """
    Processa o bloco C conforme a regra especificada.
    Move registros C500 e C590 para o final do bloco C (antes de C990).
    """
    blocos_c = []
    blocos_c500_c590 = []
    bloco_c_presente = False

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|C') and not linha.startswith('|C001|') and not linha.startswith('|C990|'):
                if linha.startswith('|C500|') or linha.startswith('|C590|'):
                    blocos_c500_c590.append(linha)
                else:
                    blocos_c.append(linha)
                    bloco_c_presente = True

    if bloco_c_presente or blocos_c500_c590:
        bloco_final = ['|C001|0|\n'] + blocos_c + blocos_c500_c590
        qtd_lin_c = len(bloco_final) + 1  # +1 para C990
        bloco_final.append(f"|C990|{qtd_lin_c}|\n")
    else:
        bloco_final = ['|C001|1|\n', '|C990|2|\n']

    return bloco_final

def processar_bloco_d(arquivos):
    """
    Processa o bloco D conforme a regra especificada.
    Move registros D500 e D590 para o final do bloco D (antes de D990).
    """
    blocos_d = []
    blocos_d500_d590 = []
    bloco_d_presente = False

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|D') and not linha.startswith('|D001|') and not linha.startswith('|D990|'):
                if linha.startswith('|D500|') or linha.startswith('|D590|'):
                    blocos_d500_d590.append(linha)
                else:
                    blocos_d.append(linha)
                    bloco_d_presente = True

    if bloco_d_presente or blocos_d500_d590:
        bloco_final = ['|D001|0|\n'] + blocos_d + blocos_d500_d590
        qtd_lin_d = len(bloco_final) + 1  # +1 para D990
        bloco_final.append(f"|D990|{qtd_lin_d}|\n")
    else:
        bloco_final = ['|D001|1|\n', '|D990|2|\n']

    return bloco_final

def processar_bloco_g110(arquivos):
    """
    Processa o bloco G110 somando:
    - o campo 4
    - o campo 5
    - e os campos do 9 em diante.
    Mantém fixos os campos 1 a 3 e 6 a 8. Todos os valores somados são arredondados para 2 casas decimais.
    """
    soma_g110 = None
    campos_fixos_inicio = None  # campos 1 a 3
    campos_fixos_meio = None    # campos 6 a 8

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|G110|'):
                campos = linha.strip().split('|')

                if len(campos) < 9:
                    continue  # pula linhas incompletas

                # Armazena os campos fixos
                if campos_fixos_inicio is None:
                    campos_fixos_inicio = campos[1:4]  # campos 1 a 3
                    campos_fixos_meio = campos[6:9]    # campos 6 a 8

                # Campos a somar: campo 4, 5 e 9 até o penúltimo
                valores = []

                try:
                    valores.append(float(campos[4].replace(',', '.')) if campos[4].strip() else 0.0)  # campo 4
                except ValueError:
                    valores.append(0.0)

                try:
                    valores.append(float(campos[5].replace(',', '.')) if campos[5].strip() else 0.0)  # campo 5
                except ValueError:
                    valores.append(0.0)

                for valor in campos[9:-1]:  # campos do 9 até penúltimo
                    try:
                        valores.append(float(valor.replace(',', '.')) if valor.strip() else 0.0)
                    except ValueError:
                        valores.append(0.0)

                if soma_g110 is None:
                    soma_g110 = valores
                else:
                    soma_g110 = [round(soma + valor, 2) for soma, valor in zip(soma_g110, valores)]

    if soma_g110 is not None:
        valores_str = [f"{valor:.2f}".replace('.', ',') for valor in soma_g110]

        linha_final = (
            '|' +
            '|'.join(campos_fixos_inicio) + '|' +
            valores_str[0] + '|' +  # campo 4 (somado)
            valores_str[1] + '|' +  # campo 5 (somado)
            '|'.join(campos_fixos_meio) + '|' +
            '|'.join(valores_str[2:]) + '|\n'
        )
        return [linha_final]

    return []

def processar_bloco_g125(arquivos):
    """
    Processa o bloco G125 copiando todas as suas linhas e incluindo
    os filhos G130 e G140 que aparecem logo em seguida.
    Retorna as linhas do bloco e um dicionário de contagem para 9900.
    """
    bloco_g125_com_filhos = []
    totalizadores = {
        'G125': 0,
        'G130': 0,
        'G140': 0
    }

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        i = 0
        while i < len(linhas):
            linha = linhas[i]
            if linha.startswith('|G125|'):
                bloco_g125_com_filhos.append(linha)
                totalizadores['G125'] += 1
                i += 1
                # Copia todos os filhos G130/G140 subsequentes
                while i < len(linhas) and (linhas[i].startswith('|G130|') or linhas[i].startswith('|G140|')):
                    bloco_g125_com_filhos.append(linhas[i])
                    if linhas[i].startswith('|G130|'):
                        totalizadores['G130'] += 1
                    elif linhas[i].startswith('|G140|'):
                        totalizadores['G140'] += 1
                    i += 1
            else:
                i += 1

    return bloco_g125_com_filhos, totalizadores

def processar_bloco_g(arquivos):
    """
    Processa o bloco G conforme a regra especificada.
    Inclui apenas G110, G125, G130 e G140.
    NÃO devolve contagens, pois serão feitas centralizadamente em adicionar_bloco_9.
    """
    bloco_g110_dados = processar_bloco_g110(arquivos)
    bloco_g125_dados = []

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        i = 0
        while i < len(linhas):
            linha = linhas[i]
            if linha.startswith('|G125|'):
                bloco_g125_dados.append(linha)
                i += 1
                while i < len(linhas) and (linhas[i].startswith('|G130|') or linhas[i].startswith('|G140|')):
                    bloco_g125_dados.append(linhas[i])
                    i += 1
            else:
                i += 1

    bloco_g_presente = len(bloco_g110_dados) > 0 or len(bloco_g125_dados) > 0

    if bloco_g_presente:
        bloco_g_dados = ['|G001|0|\n'] + bloco_g110_dados + bloco_g125_dados
        qtd_lin_g = len(bloco_g_dados) + 1  # +1 para G990
        bloco_g_dados.append(f"|G990|{qtd_lin_g}|\n")
    else:
        bloco_g_dados = ['|G001|1|\n', '|G990|2|\n']

    return bloco_g_dados

def processar_bloco_e(arquivos):
    """
    Processa o bloco E conforme a regra especificada.
    Ignora todas as linhas do bloco E dos arquivos de entrada, exceto E100, E110, E111, E116, E200, E210, E500, E510 e E520.
    """
    bloco_e_dados = processar_bloco_e100(arquivos)
    bloco_e110_dados = processar_bloco_e110(arquivos)
    bloco_e111_dados = processar_bloco_e111(arquivos)
    bloco_e116_dados = processar_bloco_e116(arquivos)
    bloco_e200_e210_dados = processar_bloco_e200_e210(arquivos)
    bloco_e500_dados = processar_bloco_e500(arquivos)
    bloco_e510_dados = processar_bloco_e510(arquivos)
    bloco_e520_dados = processar_bloco_e520(arquivos)
    bloco_e_presente = len(bloco_e_dados) > 0 or len(bloco_e110_dados) > 0 or len(bloco_e111_dados) > 0 or len(bloco_e116_dados) > 0 or len(bloco_e200_e210_dados) > 0 or len(bloco_e500_dados) > 0 or len(bloco_e510_dados) > 0 or len(bloco_e520_dados) > 0

    bloco_e_dados.extend(bloco_e110_dados)
    bloco_e_dados.extend(bloco_e111_dados)
    bloco_e_dados.extend(bloco_e116_dados)
    bloco_e_dados.extend(bloco_e200_e210_dados)
    bloco_e_dados.extend(bloco_e500_dados)
    bloco_e_dados.extend(bloco_e510_dados)
    bloco_e_dados.extend(bloco_e520_dados)

    if bloco_e_presente:
        bloco_e_dados.insert(0, '|E001|0|\n')
        qtd_lin_e = len(bloco_e_dados) + 1  # +1 para E990
        bloco_e_dados.append(f"|E990|{qtd_lin_e}|\n")
    else:
        bloco_e_dados = ['|E001|1|\n', '|E990|2|\n']

    return bloco_e_dados

def processar_bloco_e520(arquivos):
    """
    Processa o bloco E520 copiando-o apenas do primeiro arquivo onde ele aparece.
    """
    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|E520|'):
                return [linha]
    return []

def processar_bloco_k010_k100(arquivos):
    """
    Processa os blocos K010 e K100 copiando a primeira ocorrência de cada um.
    """
    bloco_k010 = None
    bloco_k100 = None

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if bloco_k010 is None and linha.startswith('|K010|'):
                bloco_k010 = linha
            if bloco_k100 is None and linha.startswith('|K100|'):
                bloco_k100 = linha
            if bloco_k010 and bloco_k100:
                break
        if bloco_k010 and bloco_k100:
            break

    return [bloco_k010, bloco_k100] if bloco_k010 or bloco_k100 else []

def processar_bloco_k200(arquivos):
    """
    Processa o bloco K200 somando os valores do quarto campo para cada chave única.
    """
    registros_k200 = {}

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|K200|'):
                campos = linha.split('|')
                chave = (campos[2], campos[3])  # chave de busca (segundo e terceiro campos)
                valor = float(campos[4].replace(',', '.'))
                if chave not in registros_k200:
                    registros_k200[chave] = valor
                else:
                    registros_k200[chave] += valor

    linhas_k200 = []
    for chave, soma_valor in registros_k200.items():
        valor_formatado = f"{soma_valor:.3f}".replace('.', ',')
        linha = f"|K200|{chave[0]}|{chave[1]}|{valor_formatado}|0||\n"
        linhas_k200.append(linha)

    return linhas_k200

def processar_bloco_k(arquivos):
    """
    Processa o bloco K conforme a regra especificada.
    Ignora todas as linhas do bloco K dos arquivos de entrada, exceto K010, K100 e K200.
    """
    bloco_k010_k100_dados = processar_bloco_k010_k100(arquivos)
    bloco_k200_dados = processar_bloco_k200(arquivos)
    bloco_k_presente = len(bloco_k010_k100_dados) > 0 or len(bloco_k200_dados) > 0

    if bloco_k_presente:
        bloco_k_dados = ['|K001|0|\n'] + bloco_k010_k100_dados + bloco_k200_dados
        qtd_lin_k = len(bloco_k_dados) + 1  # +1 para K990
        bloco_k_dados.append(f"|K990|{qtd_lin_k}|\n")
    else:
        bloco_k_dados = ['|K001|1|\n', '|K990|2|\n']

    return bloco_k_dados

def processar_bloco_k230_k235(arquivos):
    """
    Processa os blocos K230 e K235 na mesma ordem em que se encontram.
    """
    linhas_k230_k235 = []

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|K230|') or linha.startswith('|K235|'):
                linhas_k230_k235.append(linha)
    
    return linhas_k230_k235

def processar_bloco_k(arquivos):
    """
    Processa o bloco K conforme a regra especificada.
    Ignora todas as linhas do bloco K dos arquivos de entrada, exceto K010, K100, K200, K230 e K235.
    """
    bloco_k010_k100_dados = processar_bloco_k010_k100(arquivos)
    bloco_k200_dados = processar_bloco_k200(arquivos)
    bloco_k230_k235_dados = processar_bloco_k230_k235(arquivos)
    bloco_k_presente = len(bloco_k010_k100_dados) > 0 or len(bloco_k200_dados) > 0 or len(bloco_k230_k235_dados) > 0

    if bloco_k_presente:
        bloco_k_dados = ['|K001|0|\n'] + bloco_k010_k100_dados + bloco_k200_dados + bloco_k230_k235_dados
        qtd_lin_k = len(bloco_k_dados) + 1  # +1 para K990
        bloco_k_dados.append(f"|K990|{qtd_lin_k}|\n")
    else:
        bloco_k_dados = ['|K001|1|\n', '|K990|2|\n']

    return bloco_k_dados


def processar_bloco_h005(arquivos):
    """
    Processa o bloco H005 somando os valores do terceiro campo para cada chave única.
    """
    registros_h005 = {}

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|H005|'):
                campos = linha.split('|')
                chave = campos[2]  # chave de busca (data)
                valor = float(campos[3].replace(',', '.'))
                if chave not in registros_h005:
                    registros_h005[chave] = valor
                else:
                    registros_h005[chave] += valor

    linhas_h005 = []
    for chave, soma_valor in registros_h005.items():
        valor_formatado = f"{soma_valor:.2f}".replace('.', ',')
        linha = f"|H005|{chave}|{valor_formatado}|01|\n"
        linhas_h005.append(linha)

    return linhas_h005

def processar_bloco_h010(arquivos):
    """
    Processa o bloco H010 copiando todas as suas linhas.
    """
    bloco_h010 = []

    for arquivo in arquivos:
        linhas = ler_arquivo_sped(arquivo)
        for linha in linhas:
            if linha.startswith('|H010|'):
                bloco_h010.append(linha)
    
    return bloco_h010


def processar_bloco_h(arquivos):
    """
    Processa o bloco H conforme a regra especificada.
    Ignora todas as linhas do bloco H990 dos arquivos de entrada e gera um novo conforme a quantidade de linhas com inicial H.
    """
    bloco_h005_dados = processar_bloco_h005(arquivos)
    bloco_h010_dados = processar_bloco_h010(arquivos)
    
    if len(bloco_h005_dados) == 0 and len(bloco_h010_dados) == 0:
        bloco_h_dados = ['|H001|1|\n', '|H990|2|\n']
    else:
        bloco_h_dados = ['|H001|0|\n'] + bloco_h005_dados + bloco_h010_dados
        qtd_lin_h = len(bloco_h_dados) + 1  # +1 para H990

        # Gera o bloco H990 conforme a quantidade de linhas do bloco H
        bloco_h_dados.append(f"|H990|{qtd_lin_h}|\n")

    return bloco_h_dados


def unificar_arquivos_sped(arquivos):
    """
    Unifica os arquivos SPED conforme as regras especificadas.
    Retorna as linhas unificadas.
    """
    linhas_unificadas = processar_blocos_unicos_0(arquivos)

    linhas_0200_organizadas = processar_blocos_0200_em_estrutura(arquivos)
    linhas_unificadas.extend(linhas_0200_organizadas)

    linhas_0300_0305 = processar_blocos_0300_0305(arquivos)

    bloco_c_dados = processar_bloco_c(arquivos)
    linhas_unificadas.extend(bloco_c_dados)

    bloco_d_dados = processar_bloco_d(arquivos)
    linhas_unificadas.extend(bloco_d_dados)

    bloco_e_dados = processar_bloco_e(arquivos)
    linhas_unificadas.extend(bloco_e_dados)

    bloco_g_dados = processar_bloco_g(arquivos)
    linhas_unificadas.extend(bloco_g_dados)

    # Processamento do bloco H
    bloco_h_dados = processar_bloco_h(arquivos)
    linhas_unificadas.extend(bloco_h_dados)

    # Processamento do bloco K
    bloco_k_dados = processar_bloco_k(arquivos)
    linhas_unificadas.extend(bloco_k_dados)

    linhas_antes_0400 = []
    linhas_depois_0400 = []
    bloco_0400_encontrado = False

    for linha in linhas_unificadas:
        if linha.startswith('|0400|'):
            bloco_0400_encontrado = True
        if bloco_0400_encontrado:
            linhas_depois_0400.append(linha)
        else:
            linhas_antes_0400.append(linha)
    
    linhas_antes_0400.extend(linhas_0300_0305)
    linhas_unificadas = linhas_antes_0400 + linhas_depois_0400

    # Processamento do bloco 0500
    bloco_0500_dados = processar_bloco_0500(arquivos)

    # Inserção do bloco 0500 após o bloco 0460 e antes do bloco 0600, se existirem
    linhas_antes_0600 = []
    linhas_depois_0600 = []
    bloco_0600_encontrado = False

    for linha in linhas_unificadas:
        if linha.startswith('|0600|'):
            bloco_0600_encontrado = True
        if bloco_0600_encontrado:
            linhas_depois_0600.append(linha)
        else:
            linhas_antes_0600.append(linha)
    
    linhas_unificadas = linhas_antes_0600 + bloco_0500_dados + linhas_depois_0600

    # Atualizar a contagem de linhas no bloco 0990
    qtd_lin_0 = sum(1 for linha in linhas_unificadas if linha.startswith('|0')) + 1
    linhas_unificadas = [linha for linha in linhas_unificadas if not linha.startswith('|0990|')]
    linhas_unificadas.append(f"|0990|{qtd_lin_0}|\n")

    blocos_especificos = importar_blocos_especificos(arquivos[0])
    linhas_unificadas.extend(blocos_especificos)

    linhas_unificadas = totalizar_blocos_X990(linhas_unificadas)

    qtd_lin_1 = sum(1 for linha in linhas_unificadas if linha.startswith('|1')) + 1
    linhas_unificadas.append(f"|1990|{qtd_lin_1}|\n")

    bloco_9 = adicionar_bloco_9(linhas_unificadas)
    linhas_unificadas.extend(bloco_9)

    qtd_lin_9 = sum(1 for linha in linhas_unificadas if linha.startswith('|9'))
    linhas_unificadas = [linha for linha in linhas_unificadas if not linha.startswith('|9990|')]
    linhas_unificadas.append(f"|9990|{qtd_lin_9 + 1}|\n")

    # Adiciona o bloco 9999 considerando todos os blocos existentes
    qtd_lin = len(linhas_unificadas) + 1
    linhas_unificadas.append(f"|9999|{qtd_lin}|\n")

    linhas_020x = [linha for linha in linhas_unificadas if linha.startswith('|0200|') or linha.startswith('|0205|') or linha.startswith('|0220|')]
    linhas_sem_020x = [linha for linha in linhas_unificadas if linha not in linhas_020x]

# Reorganiza os outros blocos normalmente
    linhas_organizadas = organizar_blocos(linhas_sem_020x)

# Reinsere os blocos 0200/0205/0220 antes do primeiro 0300
    indice_insercao = next((i for i, linha in enumerate(linhas_organizadas) if linha.startswith('|0300|')), len(linhas_organizadas))
    linhas_organizadas = linhas_organizadas[:indice_insercao] + linhas_020x + linhas_organizadas[indice_insercao:]

    return linhas_organizadas

# Caminhos dos arquivos SPED
#arquivos_sped = [
    'C:\\SPED\\SPEDFiscal_142.txt',
    #'C:\\SPED\\SPEDFiscal_143.txt',
    'C:\\SPED\\SPEDFiscal_108.txt'
#]

# Unifica os arquivos SPED para todos os blocos
#linhas_unificadas = unificar_arquivos_sped(arquivos_sped)

# Caminho do arquivo unificado
#caminho_arquivo_unificado = 'C:\\SPED\\SpedEFD-UNIDO-FINAL.txt'

# Escreve o arquivo unificado
#escrever_arquivo_sped(caminho_arquivo_unificado, linhas_unificadas)

#print(f"Arquivo unificado salvo em: {caminho_arquivo_unificado}")