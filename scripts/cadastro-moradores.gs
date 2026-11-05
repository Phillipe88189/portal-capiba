/**
 * Cadastro de moradores do App do Morador – Edifício Capiba
 * Google Apps Script ligado a uma planilha Google PRIVADA da gestão (síndico e subsíndico).
 *
 * Instalação (uma vez):
 * 1. Crie uma planilha no Google Drive da gestão (ex.: "Cadastro – App do Morador Capiba").
 * 2. Na planilha: Extensões › Apps Script. Apague o conteúdo e cole este arquivo. Salve.
 * 3. Implantar › Nova implantação › tipo "App da Web".
 *    Executar como: "Eu"  ·  Quem pode acessar: "Qualquer pessoa". Autorize com a conta da gestão.
 * 4. Copie o endereço do app da Web (termina em /exec) e informe ao Claude para preencher
 *    REGISTRO_URL no index.html.
 *
 * "Qualquer pessoa" significa apenas que o app consegue ENVIAR um cadastro; ninguém consegue
 * ler a planilha pelo endereço. A planilha continua visível só para quem você compartilhar.
 *
 * Dados pessoais (LGPD): a aba guarda apartamento e primeiro nome. Não compartilhe a planilha
 * com moradores nem a use em material coletivo.
 */

const ABA = 'Cadastros';
const CABECALHO = ['Cadastrado em', 'Última atualização', 'Apartamento', 'Primeiro nome',
  'Forma de uso', 'Aparelho', 'ID do aparelho'];

function doPost(e) {
  const trava = LockService.getScriptLock();
  trava.waitLock(10000);
  try {
    const d = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    const apto = String(d.apto || '').replace(/\D/g, '');
    const nome = String(d.nome || '').trim().split(/\s+/)[0].slice(0, 30);
    const id = String(d.id || '').slice(0, 64);
    if (!/^\d{3,4}$/.test(apto) || !/^[A-Za-zÀ-ÖØ-öø-ÿ'’-]{2,30}$/.test(nome) || !id) return resposta('invalido');

    const aba = abaCadastros_();
    const agora = new Date();
    const modo = ['App instalado', 'Navegador'].indexOf(d.modo) >= 0 ? d.modo : '';
    const aparelho = ['iPhone', 'iPad', 'Android', 'Computador'].indexOf(d.aparelho) >= 0 ? d.aparelho : '';
    const cadastro = d.cadastro ? new Date(d.cadastro) : agora;

    // Mesmo aparelho já cadastrado: atualiza a linha (ex.: passou do navegador para o app instalado)
    const ids = aba.getLastRow() > 1 ? aba.getRange(2, 7, aba.getLastRow() - 1, 1).getValues() : [];
    for (let i = 0; i < ids.length; i++) {
      if (ids[i][0] === id) {
        aba.getRange(i + 2, 2, 1, 5).setValues([[agora, apto, nome, modo, aparelho]]);
        return resposta('atualizado');
      }
    }
    aba.appendRow([isNaN(cadastro) ? agora : cadastro, agora, apto, nome, modo, aparelho, id]);
    return resposta('ok');
  } catch (err) {
    return resposta('erro');
  } finally {
    trava.releaseLock();
  }
}

function abaCadastros_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let aba = ss.getSheetByName(ABA);
  if (!aba) {
    aba = ss.insertSheet(ABA);
    aba.getRange(1, 1, 1, CABECALHO.length).setValues([CABECALHO])
      .setFontWeight('bold').setBackground('#1B6951').setFontColor('#FFE8B8');
    aba.setFrozenRows(1);
    aba.getRange('A:B').setNumberFormat('dd/MM/yyyy HH:mm');
    aba.getRange('C:C').setNumberFormat('@');
  }
  return aba;
}

function resposta(status) {
  return ContentService.createTextOutput(JSON.stringify({ status: status }))
    .setMimeType(ContentService.MimeType.JSON);
}
