const { default: makeWASocket, useMultiFileAuthState, fetchLatestBaileysVersion, downloadMediaMessage } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

const PYTHON_API = 'http://127.0.0.1:5000/webhook';
const MI_NUMERO = '34682075812@s.whatsapp.net';

async function iniciarBot() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys');
    const { version, isLatest } = await fetchLatestBaileysVersion();

    console.log(`[INFO] Versión WA Web: ${version.join('.')} (Última: ${isLatest})`);

    const sock = makeWASocket({
        version,
        auth: state,
        printQRInTerminal: false,
        browser: ['Ubuntu', 'Chrome', '20.0.04'],
        syncFullHistory: false
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, qr } = update;
        if (qr) qrcode.generate(qr, { small: true });
        if (connection === 'close') iniciarBot();
        else if (connection === 'open') console.log('¡Conectado a WhatsApp!');
    });

    sock.ev.on('messages.upsert', async (m) => {
        const msg = m.messages[0];
        if (!msg.message) return;

        const remitente = msg.key.remoteJid;

        // Ignorar grupos y estados
        if (remitente.endsWith('@g.us') || remitente === 'status@broadcast') return;

        let texto = msg.message.conversation || msg.message.extendedTextMessage?.text || "";
        let base64Audio = "";
        const esAudio = !!msg.message.audioMessage;

        // Si es un audio, lo descargamos y lo pasamos a base64
        if (esAudio) {
            try {
                const buffer = await downloadMediaMessage(
                    msg,
                    'buffer',
                    { },
                    { logger: console }
                );
                base64Audio = buffer.toString('base64');
            } catch (error) {
                console.error('[ERROR] Fallo al descargar el audio:', error.message);
                return; // Si falla la descarga, abortamos
            }
        }

        // Si no hay ni texto ni audio, ignoramos el mensaje
        if (!texto && !esAudio) return;

        const miJid = sock.user.id.split(':')[0] + '@s.whatsapp.net';

        const esAprendizajeForzado = texto.toLowerCase().startsWith('!aprende ');
        const esChatConmigoMismo = (remitente === miJid || remitente === MI_NUMERO);
        const modoAprendizaje = esAprendizajeForzado || esChatConmigoMismo;

        // No responder a mensajes propios en chats ajenos
        if (msg.key.fromMe && !esChatConmigoMismo && !esAprendizajeForzado) return;

        const textoLimpio = esAprendizajeForzado ? texto.substring(9).trim() : texto;

        console.log(`[←] ${remitente.split('@')[0]}: ${esAudio ? '[AUDIO RECIBIDO]' : textoLimpio}`);

        try {
            const response = await axios.post(PYTHON_API, {
                remitente: remitente,
                mensaje: textoLimpio,
                audio_b64: base64Audio,
                es_mio: modoAprendizaje
            });

            const respuestaIA = response.data.respuesta;
            const delayMs = response.data.delay_ms || 1200;

            if (!respuestaIA) return;

            if (!modoAprendizaje) {
                // 1. Esperar el delay calculado (simula lectura/escucha + tiempo de escritura)
                await new Promise(r => setTimeout(r, delayMs));

                // 2. Mostrar "escribiendo..." durante un momento proporcional a la respuesta
                await sock.sendPresenceUpdate('composing', remitente);
                const tiempoEscribiendo = Math.min(respuestaIA.length * 60, 3000);
                await new Promise(r => setTimeout(r, tiempoEscribiendo));
                await sock.sendPresenceUpdate('paused', remitente);

            } else {
                // En modo aprendizaje, respuesta casi inmediata
                await new Promise(r => setTimeout(r, 400));
            }

            await sock.sendMessage(remitente, { text: respuestaIA });
            console.log(`[→] ${remitente.split('@')[0]}: ${respuestaIA}`);

        } catch (error) {
            console.error('[ERROR] API Python:', error.message);
        }
    });
}

iniciarBot();
